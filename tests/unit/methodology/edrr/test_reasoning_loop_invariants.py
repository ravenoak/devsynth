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


@pytest.mark.fast
def test_reasoning_loop_respects_max_iterations_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-04 — Max iterations bound halts recursion deterministically.

    Issue: issues/coverage-below-threshold.md
    """

    call_count = {"value": 0}
    payloads = [
        {"status": "in_progress", "synthesis": {"step": 1}},
        {"status": "in_progress", "synthesis": {"step": 2}},
        {"status": "in_progress", "synthesis": {"step": 3}},
    ]

    def fake_apply(_team, task, _critic, _memory):
        payload = payloads[call_count["value"]]
        call_count["value"] += 1
        return payload

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(),
        {"id": "task-iterations"},
        MagicMock(),
        max_iterations=2,
    )

    assert call_count["value"] == 2
    assert len(results) == 2
    assert [r["synthesis"] for r in results] == [{"step": 1}, {"step": 2}]


@pytest.mark.fast
def test_reasoning_loop_retry_backoff_respects_remaining_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-05 — Retry backoff truncated by total time budget.

    Issue: issues/coverage-below-threshold.md
    """

    attempts = {"value": 0}

    def flaky_apply(_team, task, _critic, _memory):
        if attempts["value"] == 0:
            attempts["value"] += 1
            raise RuntimeError("transient")
        return {"status": "completed", "synthesis": task.get("solution", {})}

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: flaky_apply,
    )

    monotonic_values = iter([0.0, 0.01, 0.049, 0.051])

    def fake_monotonic() -> float:
        try:
            return next(monotonic_values)
        except StopIteration:  # pragma: no cover - defensive default
            return 0.051

    sleep_calls: list[float] = []

    def fake_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    monkeypatch.setattr(reasoning_loop_module.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(reasoning_loop_module.time, "sleep", fake_sleep)

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(),
        {"solution": {"step": 0}},
        MagicMock(),
        retry_attempts=1,
        retry_backoff=0.1,
        max_total_seconds=0.05,
    )

    assert len(results) == 1
    assert attempts["value"] == 1
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(0.001, rel=1e-6)


@pytest.mark.fast
def test_reasoning_loop_honors_phase_and_next_phase_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-06 — Result phases direct coordinator wiring and transitions.

    Issue: issues/coverage-below-threshold.md
    """

    payloads = [
        {
            "status": "in_progress",
            "synthesis": {"step": 1},
            "phase": "differentiate",
            "next_phase": "REFINE",
        },
        {
            "status": "completed",
            "synthesis": {"step": 2},
            "phase": "REFINE",
        },
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
            self.calls: list[str] = []

        def record_expand_results(self, result: dict[str, Any]) -> dict[str, Any]:
            self.calls.append("expand")
            return result

        def record_differentiate_results(
            self, result: dict[str, Any]
        ) -> dict[str, Any]:
            self.calls.append("differentiate")
            return result

        def record_refine_results(self, result: dict[str, Any]) -> dict[str, Any]:
            self.calls.append("refine")
            return result

    recorder = Recorder()

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(),
        {"id": "task-phase"},
        MagicMock(),
        coordinator=recorder,
        phase=Phase.EXPAND,
        max_iterations=len(payloads),
    )

    assert [r["status"] for r in results] == ["in_progress", "completed"]
    assert recorder.calls == ["differentiate", "refine"]
    assert observed_tasks[1]["solution"] == {"step": 1}
