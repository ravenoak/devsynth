"""Focused regression coverage for progress timeline simulation helpers."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

progress_module = importlib.import_module("devsynth.application.cli.progress")

if not hasattr(progress_module, "EnhancedProgressIndicator"):

    class EnhancedProgressIndicator:  # pragma: no cover - simple stub
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    progress_module.EnhancedProgressIndicator = EnhancedProgressIndicator
    exported = getattr(progress_module, "__all__", [])
    if "EnhancedProgressIndicator" not in exported:
        progress_module.__all__ = list(exported) + ["EnhancedProgressIndicator"]

from devsynth.application.cli.long_running_progress import simulate_progress_timeline


@dataclass
class _Task:
    task_id: int
    description: str
    total: float
    completed: float = 0.0
    fields: dict[str, Any] | None = None


class _StubProgress:
    """Minimal Rich.Progress stand-in for deterministic testing."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - stub
        self._next_task_id = 0
        self.tasks: dict[int, _Task] = {}

    def start(self) -> None:  # pragma: no cover - no-op for stub behaviour
        return None

    def stop(self) -> None:  # pragma: no cover - no-op for stub behaviour
        return None

    def add_task(self, description: str, *, total: float = 100, **fields: Any) -> int:
        task_id = self._next_task_id
        self._next_task_id += 1
        payload = dict(fields)
        completed = float(payload.pop("completed", 0.0))
        self.tasks[task_id] = _Task(task_id, description, total, completed, payload)
        return task_id

    def update(self, task_id: int, *, advance: float = 0.0, **fields: Any) -> _Task:
        task = self.tasks[task_id]
        task.completed = task.completed + float(advance)
        for key, value in fields.items():
            if key == "description":
                task.description = value
            else:
                task.fields = task.fields or {}
                task.fields[key] = value
        return task


class _Clock:
    def __init__(self) -> None:
        self.current = 0.0
        self.calls: list[float] = []

    def __call__(self) -> float:
        self.current += 1.0
        self.calls.append(self.current)
        return self.current


class _Console:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def print(self, *args: Any, **kwargs: Any) -> None:
        self.messages.append((args, kwargs))


@pytest.mark.fast
def test_progress_timeline_preserves_alias_after_subtask_rename() -> None:
    """simulate_progress_timeline keeps aliases valid as subtasks are renamed."""

    events = [
        {
            "action": "add_subtask",
            "alias": "seed",
            "description": "Seed data",
            "status": "queued",
            "total": 4,
        },
        {
            "action": "update_subtask",
            "alias": "seed",
            "description": "Seed data (phase 1)",
            "status": "running",
            "advance": 1,
        },
        {
            "action": "update_subtask",
            "alias": "seed",
            "status": "verifying",
            "advance": 3,
        },
        {"action": "complete_subtask", "alias": "seed"},
        {"action": "complete"},
    ]

    clock = _Clock()

    result = simulate_progress_timeline(
        events,
        description="Data sync",
        total=5,
        console=_Console(),
        clock=clock,
        progress_factory=lambda *args, **kwargs: _StubProgress(*args, **kwargs),
    )

    transcript = [entry for entry in result["transcript"] if entry[0] != "tick"]
    update_entries = [entry for entry in transcript if entry[0] == "update_subtask"]
    assert [entry[1]["alias"] for entry in update_entries] == ["seed", "seed"]
    assert [entry[1]["status"] for entry in update_entries] == ["running", "verifying"]

    completion = [entry for entry in transcript if entry[0] == "complete_subtask"]
    assert completion and completion[0][1]["alias"] == "seed"

    subtasks = result["subtasks"]
    assert "Seed data (phase 1)" in subtasks
    assert subtasks["Seed data (phase 1)"]["status"] == "Complete"

    assert clock.calls, "clock should advance to build deterministic ETA checkpoints"


@pytest.mark.fast
def test_progress_timeline_rebinds_alias_on_multiple_description_updates() -> None:
    """Later updates continue to reference the rebinding alias sequence."""

    events = [
        {
            "action": "add_subtask",
            "alias": "download",
            "description": "Download seeds",
            "status": "queued",
            "total": 10,
        },
        {
            "action": "update_subtask",
            "alias": "download",
            "description": "Download seeds (phase 1)",
            "status": "running",
            "advance": 4,
        },
        {
            "action": "update_subtask",
            "alias": "download",
            "description": "Download seeds (phase 2)",
            "status": "verifying",
            "advance": 3,
        },
        {
            "action": "update_subtask",
            "alias": "download",
            "status": "finalizing",
            "advance": 3,
        },
        {"action": "complete_subtask", "alias": "download"},
        {"action": "complete"},
    ]

    result = simulate_progress_timeline(
        events,
        description="Seed ingest",
        total=12,
        console=_Console(),
        clock=_Clock(),
        progress_factory=lambda *args, **kwargs: _StubProgress(*args, **kwargs),
    )

    transcript = [entry for entry in result["transcript"] if entry[0] != "tick"]
    alias_entries = [
        entry
        for entry in transcript
        if entry[0] in {"add_subtask", "update_subtask", "complete_subtask"}
    ]
    assert [entry[1]["alias"] for entry in alias_entries] == [
        "download",
        "download",
        "download",
        "download",
        "download",
    ]

    last_update = [entry for entry in transcript if entry[0] == "update_subtask"][-1][1]
    assert last_update["description"].endswith("Download seeds (phase 2)")
    assert last_update["status"] == "finalizing"

    subtasks = result["subtasks"]
    assert "Download seeds (phase 2)" in subtasks
    assert subtasks["Download seeds (phase 2)"]["status"] == "Complete"


@pytest.mark.fast
def test_progress_timeline_reports_eta_strings_when_progress_advances() -> None:
    """The simulated timeline exposes formatted ETA and remaining strings."""

    clock = _Clock()

    events = [
        {"action": "tick", "times": 2},
        {"action": "update", "advance": 15, "status": "warming"},
        {"action": "tick", "times": 3},
        {"action": "update", "advance": 35, "status": "running"},
        {"action": "tick", "times": 4},
        {"action": "update", "advance": 30, "status": "verifying"},
        {"action": "tick", "times": 2},
        {"action": "update", "advance": 20, "status": "finalizing"},
        {"action": "complete"},
    ]

    result = simulate_progress_timeline(
        events,
        description="Long task",
        total=100,
        console=_Console(),
        clock=clock,
        progress_factory=lambda *args, **kwargs: _StubProgress(*args, **kwargs),
    )

    summary = result["summary"]
    assert summary.eta_str is not None
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", summary.eta_str)
    assert summary.remaining_str is not None
    assert summary.remaining_str.count(":") == 2
    assert result["checkpoints"], "expected ETA checkpoints to be recorded"
    assert clock.calls, "expected clock ticks to drive eta calculations"


@pytest.mark.fast
def test_progress_timeline_records_failure_history_for_diagnostics() -> None:
    """Status changes to failure states surface in the recorded transcript/history."""

    clock = _Clock()

    events = [
        {"action": "update", "status": "running", "advance": 10},
        {"action": "tick", "times": 1},
        {
            "action": "update",
            "status": "failed: validation error",
            "advance": 0,
            "description": "Validating artifacts",
        },
        {"action": "complete"},
    ]

    result = simulate_progress_timeline(
        events,
        description="Failure demo",
        total=20,
        console=_Console(),
        clock=clock,
        progress_factory=lambda *args, **kwargs: _StubProgress(*args, **kwargs),
    )

    transcript = result["transcript"]
    failure_entries = [entry for entry in transcript if entry[0] == "update"]
    assert failure_entries[-1][1]["status"] == "failed: validation error"
    assert result["history"]
    assert result["history"][-1].status == "failed: validation error"

    console_messages = result["console_messages"]
    assert console_messages
    final_message = console_messages[-1][0][0]
    assert "Task completed" in final_message
