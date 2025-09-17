from __future__ import annotations

import importlib
from typing import Any
from unittest.mock import MagicMock

import pytest

from devsynth.methodology.base import Phase

reasoning_loop_module = importlib.import_module(
    "devsynth.methodology.edrr.reasoning_loop",
)


@pytest.mark.fast
def test_reasoning_loop_enforces_total_time_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-01 — Max total seconds halts recursion."""

    call_count = {"value": 0}

    def fake_apply(_team, task, _critic, _memory):
        call_count["value"] += 1
        return {"status": "in_progress", "task_snapshot": task.copy()}

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    ticks = iter([0.0, 0.01, 0.06, 0.2])

    def fake_monotonic() -> float:
        try:
            return next(ticks)
        except StopIteration:  # pragma: no cover - defensive
            return 0.2

    sleep_calls: list[float] = []

    monkeypatch.setattr(reasoning_loop_module.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(reasoning_loop_module.time, "sleep", sleep_calls.append)

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(),
        {"id": "task-1"},
        MagicMock(),
        max_iterations=5,
        max_total_seconds=0.05,
    )

    assert call_count["value"] == 1
    assert len(results) == 1
    assert sleep_calls == []


@pytest.mark.fast
def test_reasoning_loop_retries_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """ReqID: DRL-UNIT-02 — Retries apply exponential backoff for transient failures."""

    outcomes = iter([RuntimeError("transient-1"), RuntimeError("transient-2"), "ok"])

    def fake_apply(_team, task, _critic, _memory):
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return {"status": "completed", "synthesis": task.get("solution")}

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    sleep_durations: list[float] = []

    def fake_sleep(duration: float) -> None:
        sleep_durations.append(duration)

    monkeypatch.setattr(reasoning_loop_module.time, "sleep", fake_sleep)

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(),
        {"solution": {"step": 0}},
        MagicMock(),
        retry_attempts=2,
        retry_backoff=0.1,
    )

    assert len(results) == 1
    assert sleep_durations == [0.1, 0.2]


@pytest.mark.fast
def test_reasoning_loop_fallback_transitions_and_propagation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-03 — Fallback transitions advance phases and propagate state."""

    payloads: list[dict[str, Any]] = [
        {"status": "in_progress", "synthesis": {"step": 1}, "next_phase": "unknown"},
        {"status": "in_progress", "synthesis": {"step": 2}},
        {"status": "completed", "synthesis": {"step": 3}},
    ]
    call_index = {"value": 0}
    observed_tasks: list[dict[str, Any]] = []

    def fake_apply(_team, task, _critic, _memory):
        observed_tasks.append(task.copy())
        payload = payloads[call_index["value"]]
        call_index["value"] += 1
        return payload

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    class Recorder:
        def __init__(self) -> None:
            self.phases: list[Phase] = []

        def record_expand_results(self, result: dict[str, Any]) -> dict[str, Any]:
            self.phases.append(Phase.EXPAND)
            return result

        def record_differentiate_results(
            self, result: dict[str, Any]
        ) -> dict[str, Any]:
            self.phases.append(Phase.DIFFERENTIATE)
            return result

        def record_refine_results(self, result: dict[str, Any]) -> dict[str, Any]:
            self.phases.append(Phase.REFINE)
            return result

    recorder = Recorder()

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(),
        {"id": "task-2"},
        MagicMock(),
        coordinator=recorder,
        phase=Phase.EXPAND,
        max_iterations=len(payloads),
    )

    assert [payload["status"] for payload in results] == [
        "in_progress",
        "in_progress",
        "completed",
    ]
    assert recorder.phases == [
        Phase.EXPAND,
        Phase.DIFFERENTIATE,
        Phase.REFINE,
    ]
    assert observed_tasks[1]["solution"] == {"step": 1}
    assert observed_tasks[2]["solution"] == {"step": 2}
