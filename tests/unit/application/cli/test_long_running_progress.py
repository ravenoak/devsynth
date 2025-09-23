import importlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

import pytest

progress_module = importlib.import_module("devsynth.application.cli.progress")


if not hasattr(progress_module, "EnhancedProgressIndicator"):
    class EnhancedProgressIndicator:  # pragma: no cover - test shim
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    progress_module.EnhancedProgressIndicator = EnhancedProgressIndicator
    all_names = getattr(progress_module, "__all__", [])
    if "EnhancedProgressIndicator" not in all_names:
        progress_module.__all__ = list(all_names) + ["EnhancedProgressIndicator"]


long_running_progress = importlib.import_module("devsynth.application.cli.long_running_progress")


class FakeClock:
    """Deterministic clock returning monotonically increasing floats."""

    def __init__(self, start: float = 0.0, default_step: float = 1.0) -> None:
        self.current = start
        self.default_step = default_step
        self._queued_steps: List[float] = []
        self.history: List[float] = []

    def __call__(self) -> float:
        step = self._queued_steps.pop(0) if self._queued_steps else self.default_step
        if step <= 0:
            raise ValueError("FakeClock requires positive increments")
        self.current += step
        self.history.append(self.current)
        return self.current

    def advance(self, step: float) -> None:
        if step <= 0:
            raise ValueError("FakeClock advance requires a positive step")
        self._queued_steps.append(step)


@dataclass
class FakeTask:
    task_id: int
    description: str
    total: float
    completed: float = 0.0
    fields: Dict[str, Any] = field(default_factory=dict)


class FakeProgress:
    """Minimal stub mimicking Rich's Progress API used by the indicator."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.tasks: Dict[int, FakeTask] = {}
        self._next_task_id = 0
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def add_task(self, description: str, *, total: float = 100, **fields: Any) -> int:
        task_id = self._next_task_id
        self._next_task_id += 1
        task_fields = dict(fields)
        completed = float(task_fields.pop("completed", 0.0))
        task = FakeTask(task_id, description, total, completed=completed, fields=task_fields)
        self.tasks[task_id] = task
        return task_id

    def update(self, task_id: int, *, advance: float = 0.0, **fields: Any) -> FakeTask:
        task = self.tasks[task_id]
        if "completed" in fields:
            task.completed = float(fields.pop("completed"))
        else:
            task.completed += float(advance)
        if "description" in fields:
            task.description = fields.pop("description")
        for key, value in fields.items():
            task.fields[key] = value
        return task


class DummyConsole:
    def __init__(self) -> None:
        self.messages: List[Any] = []

    def print(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - behaviour unused
        self.messages.append((args, kwargs))


@pytest.fixture
def fake_clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    clock = FakeClock()
    monkeypatch.setattr(time, "time", clock)
    monkeypatch.setattr(long_running_progress.time, "time", clock)
    return clock


@pytest.fixture(autouse=True)
def fake_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(long_running_progress, "Progress", FakeProgress)


class ExplosiveRepr:
    def __str__(self) -> str:
        raise RuntimeError("boom")


@pytest.mark.fast
def test_update_adapts_interval_and_checkpoints(fake_clock: FakeClock) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(console, "task", total=100)

    indicator.update(advance=5)
    assert indicator._update_interval == pytest.approx(0.5)
    task = indicator._progress.tasks[indicator._task]
    assert task.completed == pytest.approx(5)

    indicator.update(advance=45)
    assert indicator._update_interval == pytest.approx(0.5)
    assert task.completed == pytest.approx(50)

    fake_clock.advance(2.5)
    indicator.update(advance=45)
    assert indicator._update_interval == pytest.approx(2.0)
    assert task.completed == pytest.approx(95)

    fake_clock.advance(2.0)
    indicator.update(advance=5)
    assert indicator._update_interval == pytest.approx(0.5)
    assert task.completed == pytest.approx(100)

    checkpoints = task.fields["checkpoints"]
    assert len(checkpoints) == 2
    assert [cp["progress"] for cp in checkpoints] == pytest.approx([0.5, 0.95])
    checkpoint_times = [cp["time"] for cp in checkpoints]
    assert checkpoint_times == pytest.approx([5.0, 7.5])
    for cp in checkpoints:
        expected_eta = indicator._start_time + (
            (cp["time"] - indicator._start_time) / cp["progress"]
        )
        assert cp["eta"] == pytest.approx(expected_eta)


@pytest.mark.fast
def test_status_history_tracks_unique_status_changes(fake_clock: FakeClock) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(console, "task", total=20)

    indicator.update(advance=5, status="Loading")
    indicator.update(advance=5, status="Loading")
    indicator.update(advance=5, status="Processing")
    indicator.update(advance=5, status="Complete")

    task = indicator._progress.tasks[indicator._task]
    history = task.fields["history"]
    assert [entry["status"] for entry in history] == ["Loading", "Processing", "Complete"]
    assert [entry["completed"] for entry in history] == [0, 10, 15]
    assert [entry["time"] for entry in history] == pytest.approx([4.0, 6.0, 7.0])
    assert task.fields["status"] == "Complete"


@pytest.mark.fast
def test_summary_reflects_fake_timeline_and_sanitizes_descriptions(
    fake_clock: FakeClock,
) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, ExplosiveRepr(), total=100
    )

    task = indicator._progress.tasks[indicator._task]
    assert task.description == "<main task>"

    fake_clock.advance(10.0)
    indicator.update(advance=10, description=ExplosiveRepr())
    assert task.description == "<description>"

    fake_clock.advance(5.0)
    summary = indicator.get_summary()
    current_time = fake_clock.history[-1]
    expected_elapsed = current_time - indicator._start_time
    assert summary["description"] == "<description>"
    assert summary["elapsed"] == pytest.approx(expected_elapsed)
    assert summary["progress"] == pytest.approx(task.completed / task.total)
    assert "remaining" in summary
    expected_remaining = summary["elapsed"] / summary["progress"] - summary["elapsed"]
    assert summary["remaining"] == pytest.approx(expected_remaining)
    assert summary["eta"] == pytest.approx(indicator._start_time + summary["elapsed"] / summary["progress"])
    assert task.fields["checkpoints"] == summary["checkpoints"]
