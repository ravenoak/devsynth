"""Focused regression coverage for progress timeline simulation helpers."""

from __future__ import annotations

import importlib
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
    fields: Dict[str, Any] | None = None


class _StubProgress:
    """Minimal Rich.Progress stand-in for deterministic testing."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - stub
        self._next_task_id = 0
        self.tasks: Dict[int, _Task] = {}

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
        self.calls: List[float] = []

    def __call__(self) -> float:
        self.current += 1.0
        self.calls.append(self.current)
        return self.current


class _Console:
    def __init__(self) -> None:
        self.messages: List[Any] = []

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
