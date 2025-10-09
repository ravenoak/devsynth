from __future__ import annotations

import pytest

import devsynth.methodology.edrr.reasoning_loop as reasoning_loop_module
from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.exceptions import ConsensusError
from devsynth.methodology.base import Phase
from devsynth.methodology.edrr.contracts import CoordinatorRecorder, NullWSDETeam


@pytest.mark.fast
def test_reasoning_loop_exits_when_budget_elapsed_before_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-09 — Exhausted time budget halts before invoking reasoning."""

    calls = {"count": 0}

    def fake_apply(*_args, **_kwargs):  # pragma: no cover - should not be hit
        calls["count"] += 1
        return DialecticalSequence.from_dict({"status": "completed"})

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    monotonic_values = iter([0.0, 0.5])

    def fake_monotonic() -> float:
        try:
            return next(monotonic_values)
        except StopIteration:  # pragma: no cover - defensive default
            return 0.5

    monkeypatch.setattr(reasoning_loop_module.time, "monotonic", fake_monotonic)

    results = reasoning_loop_module.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "x"},
        critic_agent=None,
        max_total_seconds=0.25,
    )

    assert results == []
    assert calls["count"] == 0


@pytest.mark.fast
def test_reasoning_loop_retry_sequence_updates_phase_and_coordinator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-10 — Retries back off exponentially and honor phase metadata."""

    outcomes: list[object] = [
        RuntimeError("transient-1"),
        RuntimeError("transient-2"),
        {
            "status": "in_progress",
            "phase": "EXPAND",
            "next_phase": "DIFFERENTIATE",
            "synthesis": {"step": 1},
        },
        {
            "status": "in_progress",
            "next_phase": "refine",
        },
        {
            "status": "completed",
            "phase": "refine",
        },
    ]
    index = {"value": 0}
    observed_tasks: list[dict[str, object]] = []

    def fake_apply(_team, task, _critic, _memory):
        outcome = outcomes[index["value"]]
        index["value"] += 1
        if isinstance(outcome, Exception):
            raise outcome
        observed_tasks.append(task.copy())
        return outcome

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    clock = {"value": 0.0}
    sleep_calls: list[float] = []

    def fake_monotonic() -> float:
        return clock["value"]

    def fake_sleep(duration: float) -> None:
        sleep_calls.append(duration)
        clock["value"] += duration

    monkeypatch.setattr(reasoning_loop_module.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(reasoning_loop_module.time, "sleep", fake_sleep)

    recorder = CoordinatorRecorder()

    results = reasoning_loop_module.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"id": "retry"},
        critic_agent=None,
        coordinator=recorder,
        phase=Phase.EXPAND,
        max_iterations=5,
        retry_attempts=2,
        retry_backoff=0.2,
    )

    assert [r["status"] for r in results] == [
        "in_progress",
        "in_progress",
        "completed",
    ]
    assert sleep_calls == pytest.approx([0.2, 0.4])
    assert observed_tasks[0]["id"] == "retry"
    assert observed_tasks[1]["solution"] == {"step": 1}
    assert recorder.records == [
        ("expand", dict(results[0])),
        ("differentiate", dict(results[1])),
        ("refine", dict(results[2])),
    ]


@pytest.mark.fast
def test_reasoning_loop_records_results_before_consensus_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: DRL-UNIT-11 — Existing progress is preserved when consensus fails."""

    payloads: list[object] = [
        {"status": "in_progress", "phase": "expand"},
        ConsensusError("stalemate"),
    ]
    index = {"value": 0}

    def fake_apply(_team, _task, _critic, _memory):
        outcome = payloads[index["value"]]
        index["value"] += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    recorder = CoordinatorRecorder()

    results = reasoning_loop_module.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"id": "consensus"},
        critic_agent=None,
        coordinator=recorder,
        phase=Phase.EXPAND,
        max_iterations=3,
    )

    assert len(results) == 1
    assert recorder.records == [("expand", dict(results[0]))]
    assert recorder.failures and isinstance(recorder.failures[0], ConsensusError)
    assert index["value"] == 2
