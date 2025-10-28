import importlib
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
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


long_running_progress = importlib.import_module(
    "devsynth.application.cli.long_running_progress"
)

from devsynth.application.cli.models import ProgressCheckpoint, ProgressHistoryEntry


@pytest.mark.fast
def test_progress_indicator_base_alias_is_exported() -> None:
    """The hoisted alias remains available for runtime imports."""

    assert hasattr(long_running_progress, "_ProgressIndicatorBase")
    base = long_running_progress._ProgressIndicatorBase
    assert base is long_running_progress.ProgressIndicator
    assert issubclass(long_running_progress.LongRunningProgressIndicator, base)


@pytest.mark.fast
def test_progress_indicator_base_alias_import_statement_works() -> None:
    """Direct ``from module import`` access to the alias succeeds."""

    from devsynth.application.cli.long_running_progress import (
        _ProgressIndicatorBase as imported_base,
    )

    assert imported_base is long_running_progress.ProgressIndicator
    assert issubclass(long_running_progress.LongRunningProgressIndicator, imported_base)


@pytest.mark.fast
def test_progress_indicator_protocol_alias_import_statement_works() -> None:
    """Importing the protocol helper remains stable for type hint users."""

    from devsynth.application.cli.long_running_progress import (
        _ProgressIndicatorProtocol as imported_protocol,
    )

    assert imported_protocol is long_running_progress._ProgressIndicatorProtocol


@pytest.mark.fast
def test_progress_indicator_aliases_listed_in_all() -> None:
    """Module exports remain discoverable via ``__all__``."""

    exported = set(long_running_progress.__all__)

    assert "_ProgressIndicatorBase" in exported
    assert "_ProgressIndicatorProtocol" in exported
    assert "LongRunningProgressIndicator" in exported


class FakeClock:
    """Deterministic clock returning monotonically increasing floats."""

    def __init__(self, start: float = 0.0, default_step: float = 1.0) -> None:
        self.current = start
        self.default_step = default_step
        self._queued_steps: list[float] = []
        self.history: list[float] = []

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
    fields: dict[str, Any] = field(default_factory=dict)


class FakeProgress:
    """Minimal stub mimicking Rich's Progress API used by the indicator."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.tasks: dict[int, FakeTask] = {}
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
        task = FakeTask(
            task_id, description, total, completed=completed, fields=task_fields
        )
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

    # Helpers for inspecting subtask state in tests -----------------------
    def child_tasks(self, parent_id: int) -> dict[int, FakeTask]:
        """Return a mapping of child task IDs to their FakeTask instances."""

        return {
            task_id: task
            for task_id, task in self.tasks.items()
            if task.fields.get("parent") == parent_id
        }

    def snapshot(self, task_id: int) -> dict[str, Any]:
        """Produce a serialisable snapshot for nested completion assertions."""

        task = self.tasks[task_id]
        child_ids = sorted(
            candidate_id
            for candidate_id, candidate in self.tasks.items()
            if candidate.fields.get("parent") == task_id
        )
        return {
            "task_id": task_id,
            "description": task.description,
            "total": task.total,
            "completed": task.completed,
            "fields": dict(task.fields),
            "children": [self.snapshot(child_id) for child_id in child_ids],
        }


class DummyConsole:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def print(self, *args: Any, **kwargs: Any) -> None:
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
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, "task", total=100
    )

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
    assert all(isinstance(cp, ProgressCheckpoint) for cp in checkpoints)
    assert [cp.progress for cp in checkpoints] == pytest.approx([0.5, 0.95])
    checkpoint_times = [cp.time for cp in checkpoints]
    assert checkpoint_times == pytest.approx([5.0, 7.5])
    for cp in checkpoints:
        expected_eta = indicator._start_time + (
            (cp.time - indicator._start_time) / cp.progress
        )
        assert cp.eta == pytest.approx(expected_eta)


@pytest.mark.fast
def test_status_history_tracks_unique_status_changes(fake_clock: FakeClock) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, "task", total=20
    )

    indicator.update(advance=5, status="Loading")
    indicator.update(advance=5, status="Loading")
    indicator.update(advance=5, status="Processing")
    indicator.update(advance=5, status="Complete")

    task = indicator._progress.tasks[indicator._task]
    history = task.fields["history"]
    assert all(isinstance(entry, ProgressHistoryEntry) for entry in history)
    assert [entry.status for entry in history] == [
        "Loading",
        "Processing",
        "Complete",
    ]
    assert [entry.completed for entry in history] == [0, 10, 15]
    assert [entry.time for entry in history] == pytest.approx([4.0, 6.0, 7.0])
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
    assert summary.description == "<description>"
    assert summary.elapsed == pytest.approx(expected_elapsed)
    assert summary.progress == pytest.approx(task.completed / task.total)
    assert summary.remaining is not None
    expected_remaining = summary.elapsed / summary.progress - summary.elapsed
    assert summary.remaining == pytest.approx(expected_remaining)
    assert summary.eta is not None
    assert summary.eta == pytest.approx(
        indicator._start_time + summary.elapsed / summary.progress
    )
    assert list(task.fields["checkpoints"]) == list(summary.checkpoints)


@pytest.mark.fast
def test_subtask_updates_remap_and_short_circuit(fake_clock: FakeClock) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, "workflow", total=120
    )

    main_task_id = indicator._task
    phase_one = indicator.add_subtask("phase 1", total=40)
    phase_two = indicator.add_subtask("phase 2", total=60)

    fake_clock.advance(1.0)
    indicator.update_subtask(phase_one, advance=20, status="Halfway")

    main_task = indicator._progress.tasks[main_task_id]
    expected_main = (20 / 40) * (main_task.total / len(indicator._subtasks))
    assert main_task.completed == pytest.approx(expected_main)

    phase_one_task_id = indicator._subtasks[phase_one].task_id
    child_tasks = indicator._progress.child_tasks(main_task_id)
    phase_one_task = child_tasks[phase_one_task_id]
    assert phase_one_task.completed == pytest.approx(20)
    assert phase_one_task.fields["status"] == "Halfway"

    fake_clock.advance(1.0)
    indicator.update_subtask(phase_one, advance=0, description="phase 1b")

    assert phase_one not in indicator._subtasks
    assert "phase 1b" in indicator._subtasks
    renamed_task_id = indicator._subtasks["phase 1b"].task_id
    renamed_task = indicator._progress.tasks[renamed_task_id]
    assert renamed_task.description.endswith("phase 1b")
    assert renamed_task.completed == pytest.approx(20)

    assert indicator._progress.tasks[main_task_id].completed == pytest.approx(
        expected_main
    )

    fake_clock.advance(1.0)
    snapshot_before = indicator._progress.snapshot(main_task_id)
    indicator.update_subtask("missing", advance=10, status="Ghost")
    assert indicator._progress.snapshot(main_task_id) == snapshot_before
    assert set(indicator._subtasks) == {"phase 1b", phase_two}


@pytest.mark.fast
def test_subtask_completion_rolls_up_and_freezes_summary(fake_clock: FakeClock) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, "pipeline", total=100
    )

    main_task_id = indicator._task

    fake_clock.advance(5.0)
    indicator.update(advance=15, status="Loading")
    fake_clock.advance(5.0)
    indicator.update(advance=15, status="Processing")

    stage_one = indicator.add_subtask("stage 1", total=50)
    stage_two = indicator.add_subtask("stage 2", total=50)

    fake_clock.advance(2.0)
    indicator.update_subtask(stage_one, advance=25)

    main_task = indicator._progress.tasks[main_task_id]
    before_completion = main_task.completed
    stage_one_task_id = indicator._subtasks[stage_one].task_id
    stage_one_task = indicator._progress.tasks[stage_one_task_id]
    remaining = stage_one_task.total - stage_one_task.completed

    fake_clock.advance(3.0)
    indicator.complete_subtask(stage_one)

    main_task_after = indicator._progress.tasks[main_task_id]
    expected_rollup = (
        remaining * main_task.total / (len(indicator._subtasks) * stage_one_task.total)
    )
    assert main_task_after.completed == pytest.approx(
        before_completion + expected_rollup
    )
    assert indicator._progress.tasks[stage_one_task_id].completed == pytest.approx(
        stage_one_task.total
    )

    history_before_complete = [
        asdict(entry) for entry in main_task_after.fields["history"]
    ]
    checkpoints_before_complete = [
        asdict(entry) for entry in main_task_after.fields["checkpoints"]
    ]
    checkpoint_times_before = [cp["time"] for cp in checkpoints_before_complete]

    fake_clock.advance(4.0)
    indicator.complete()
    completion_time = fake_clock.history[-1]
    elapsed_seconds = int(completion_time - indicator._start_time)
    expected_elapsed_str = str(timedelta(seconds=elapsed_seconds))
    assert (
        console.messages[-1][0][0]
        == f"[bold green]Task completed in {expected_elapsed_str}[/bold green]"
    )
    assert indicator._progress.stopped

    main_task_final = indicator._progress.tasks[main_task_id]
    assert [
        asdict(entry) for entry in main_task_final.fields["history"]
    ] == history_before_complete
    assert [
        asdict(entry) for entry in main_task_final.fields["checkpoints"]
    ] == checkpoints_before_complete

    stage_two_task_id = indicator._subtasks[stage_two].task_id
    stage_two_task = indicator._progress.tasks[stage_two_task_id]
    assert stage_two_task.completed == pytest.approx(stage_two_task.total)
    assert stage_two_task.fields["status"] == "Complete"

    summary = indicator.get_summary()
    assert summary.progress == pytest.approx(1.0)
    assert summary.remaining == pytest.approx(0.0)
    assert summary.remaining_str == str(timedelta(seconds=0))
    assert summary.eta is not None
    assert summary.eta_str == datetime.fromtimestamp(summary.eta).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    assert [asdict(cp) for cp in summary.checkpoints] == checkpoints_before_complete
    assert [cp.time for cp in summary.checkpoints] == checkpoint_times_before
    assert [asdict(entry) for entry in summary.history] == history_before_complete
    assert summary.subtasks == len(indicator._subtasks)


@pytest.mark.fast
def test_subtask_checkpoint_spacing_respects_minimum(fake_clock: FakeClock) -> None:
    console = DummyConsole()
    indicator = long_running_progress.LongRunningProgressIndicator(
        console, "task", total=100
    )

    first = indicator.add_subtask("fast lane", total=20)
    second = indicator.add_subtask("slow lane", total=80)

    fake_clock.advance(1.0)
    indicator.update_subtask(first, advance=5)
    fake_clock.advance(1.0)
    indicator.update_subtask(second, advance=8)
    fake_clock.advance(1.0)
    indicator.update_subtask(second, advance=8)
    fake_clock.advance(1.0)
    indicator.update_subtask(first, advance=15)
    fake_clock.advance(1.0)
    indicator.update_subtask(second, advance=32)

    checkpoints = indicator._progress.tasks[indicator._task].fields["checkpoints"]
    assert all(isinstance(cp, ProgressCheckpoint) for cp in checkpoints)
    progress_values = [cp.progress for cp in checkpoints]
    assert len(progress_values) >= 4
    assert progress_values == pytest.approx([0.125, 0.225, 0.6, 0.8])
    deltas = [b - a for a, b in zip(progress_values, progress_values[1:])]
    assert all(delta >= 0.1 - 1e-9 for delta in deltas)


class _Explosive:
    def __str__(self) -> str:
        raise RuntimeError("detonate")


@pytest.mark.fast
def test_simulation_timeline_produces_deterministic_transcript(
    fake_clock: FakeClock,
) -> None:
    console = DummyConsole()
    events = [
        {
            "action": "update",
            "advance": 5,
            "status": "Booting",
            "description": "alpha <task>",
        },
        {
            "action": "add_subtask",
            "description": "stage &1",
            "alias": "stage-one",
            "total": 40,
            "status": "Queued",
        },
        {
            "action": "add_subtask",
            "description": _Explosive(),
            "alias": "volatile",
            "total": 60,
        },
        {"action": "tick", "times": 2},
        {
            "action": "update_subtask",
            "alias": "stage-one",
            "advance": 20,
            "status": "Working",
        },
        {
            "action": "update_subtask",
            "alias": "volatile",
            "advance": 15,
            "description": "volatile <1>",
        },
        {"action": "tick", "times": 1},
        {"action": "complete_subtask", "alias": "stage-one"},
        {"action": "update", "advance": 35, "status": "Finalizing"},
        {"action": "complete"},
    ]

    result = long_running_progress.simulate_progress_timeline(
        events,
        description="Simulated <run>",
        total=120,
        console=console,
    )

    transcript = result["transcript"]
    assert [entry[0] for entry in transcript] == [
        "update",
        "add_subtask",
        "add_subtask",
        "tick",
        "update_subtask",
        "update_subtask",
        "tick",
        "complete_subtask",
        "update",
        "complete",
    ]

    main_updates = [payload for action, payload in transcript if action == "update"]
    assert main_updates[0]["status"] == "Booting"
    assert main_updates[0]["description"].endswith("alpha <task>")
    complete_payloads = [
        payload for action, payload in transcript if action == "complete"
    ]
    assert complete_payloads[-1]["status"] == "Complete"

    add_events = [payload for action, payload in transcript if action == "add_subtask"]
    assert add_events[0]["description"].startswith("  ↳ stage &1")
    assert add_events[1]["description"].startswith("  ↳ <subtask>")

    volatile_updates = [
        payload
        for action, payload in transcript
        if action == "update_subtask" and payload["alias"] == "volatile"
    ]
    assert volatile_updates[-1]["description"].endswith("volatile <1>")

    summary = result["summary"]
    assert summary.progress == pytest.approx(1.0)
    assert summary.eta is not None
    assert summary.checkpoints

    subtasks = result["subtasks"]
    assert "stage &1" in subtasks
    assert subtasks["stage &1"]["status"] == "Complete"
    assert "volatile <1>" in subtasks
    assert subtasks["volatile <1>"]["description"].endswith("volatile <1>")

    console_messages = result["console_messages"]
    assert console_messages
    assert console_messages[-1][0][0].startswith("[bold green]Task completed in ")


@pytest.mark.fast
def test_simulation_timeline_tracks_history_and_alias_renames() -> None:
    """Timeline simulation records history, checkpoints, and alias remaps."""

    clock = FakeClock(start=10.0, default_step=3.0)
    console = DummyConsole()
    events = [
        {
            "action": "update",
            "advance": 0,
            "status": "Queued",
            "description": "Boot <sequence>",
        },
        {"action": "tick", "times": 1},
        {
            "action": "add_subtask",
            "description": "prep <files>",
            "alias": "prep",
            "total": 40,
            "status": "Waiting",
        },
        {
            "action": "update_subtask",
            "alias": "prep",
            "advance": 12,
            "status": "Working",
        },
        {"action": "tick", "times": 1},
        {
            "action": "update_subtask",
            "alias": "prep",
            "advance": 8,
            "description": "prep review <1>",
            "status": "Review",
        },
        {"action": "tick", "times": 1},
        {"action": "update", "advance": 0, "status": "Processing"},
        {"action": "tick", "times": 1},
        {
            "action": "update_subtask",
            "alias": "prep",
            "advance": 20,
            "status": "Done",
        },
        {"action": "update", "advance": 0, "status": "Finalizing"},
        {"action": "tick", "times": 1},
        {"action": "complete_subtask", "alias": "prep"},
        {"action": "complete"},
    ]

    result = long_running_progress.simulate_progress_timeline(
        events,
        description="Nested rename",
        total=100,
        console=console,
        clock=clock,
    )

    history = result["history"]
    history_statuses = [entry.status for entry in history]
    assert history_statuses == ["Queued", "Processing", "Finalizing"]
    assert [entry.completed for entry in history] == pytest.approx([0.0, 51.0, 102.0])

    checkpoints = result["checkpoints"]
    checkpoint_progress = [cp.progress for cp in checkpoints]
    assert checkpoint_progress == pytest.approx([0.31, 0.51, 1.02])
    assert checkpoint_progress == sorted(checkpoint_progress)

    update_subtask_payloads = [
        payload
        for action, payload in result["transcript"]
        if action == "update_subtask"
    ]
    assert len(update_subtask_payloads) == 3
    assert update_subtask_payloads[1]["description"].endswith("prep review <1>")
    assert update_subtask_payloads[-1]["status"] == "Done"

    subtasks = result["subtasks"]
    assert "prep review <1>" in subtasks
    assert subtasks["prep review <1>"]["status"] == "Complete"

    console_messages = result["console_messages"]
    assert console_messages
    assert console_messages[-1][0][0].startswith("[bold green]Task completed in ")

    # Clock ticks capture deterministic ETA calculations for checkpoints.
    assert clock.history  # clock invoked throughout simulation


@pytest.mark.fast
def test_simulation_timeline_remains_deterministic_after_reload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reloading the module preserves deterministic simulation outputs."""

    def build_events() -> list[dict[str, object]]:
        return [
            {
                "action": "update",
                "advance": 5,
                "status": "Booting",
                "description": "alpha <task>",
            },
            {
                "action": "add_subtask",
                "description": "stage &1",
                "alias": "stage-one",
                "total": 40,
                "status": "Queued",
            },
            {
                "action": "add_subtask",
                "description": _Explosive(),
                "alias": "volatile",
                "total": 60,
            },
            {"action": "tick", "times": 2},
            {
                "action": "update_subtask",
                "alias": "stage-one",
                "advance": 20,
                "status": "Working",
            },
            {
                "action": "update_subtask",
                "alias": "volatile",
                "advance": 15,
                "description": "volatile <1>",
            },
            {"action": "tick", "times": 1},
            {"action": "complete_subtask", "alias": "stage-one"},
            {"action": "update", "advance": 35, "status": "Finalizing"},
            {"action": "complete"},
        ]

    monkeypatch.setattr(long_running_progress, "Progress", FakeProgress)

    first_clock = FakeClock(start=2.0, default_step=1.5)
    first_result = long_running_progress.simulate_progress_timeline(
        build_events(),
        description="Reload simulation",
        total=120,
        console=DummyConsole(),
        clock=first_clock,
    )

    reloaded_module = importlib.reload(long_running_progress)
    monkeypatch.setattr(reloaded_module, "Progress", FakeProgress)

    second_clock = FakeClock(start=2.0, default_step=1.5)
    second_result = reloaded_module.simulate_progress_timeline(
        build_events(),
        description="Reload simulation",
        total=120,
        console=DummyConsole(),
        clock=second_clock,
    )

    assert reloaded_module._ProgressIndicatorBase is reloaded_module.ProgressIndicator
    assert second_result["transcript"] == first_result["transcript"]
    assert second_result["summary"] == first_result["summary"]
    assert second_result["history"] == first_result["history"]
    assert second_result["checkpoints"] == first_result["checkpoints"]
    assert second_result["subtasks"] == first_result["subtasks"]
    assert second_result["console_messages"] == first_result["console_messages"]
