from __future__ import annotations

import sys
import types
from datetime import datetime, timedelta
from typing import Any

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.domain.models.wsde_dialectical_types import DialecticalTask
from devsynth.methodology.edrr.contracts import CoordinatorRecorder, NullWSDETeam


@pytest.mark.fast
def test_reasoning_loop_exhausts_retry_budget_and_backoff(monkeypatch):
    """Transient errors exhaust the retry budget and honor exponential backoff.

    ReqID: N/A
    """

    call_counter = {"count": 0}

    def always_transient(*_args, **_kwargs):
        call_counter["count"] += 1
        raise RuntimeError("temporary failure")

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: always_transient
    )

    sleep_calls: list[float] = []

    def fake_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    def fake_monotonic() -> float:
        return 0.0

    monkeypatch.setattr(rl.time, "sleep", fake_sleep)
    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "test"},
        critic_agent=None,
        retry_attempts=2,
        retry_backoff=0.1,
    )

    assert results == []
    assert call_counter["count"] == 3
    assert sleep_calls == pytest.approx([0.1, 0.2])


@pytest.mark.fast
def test_reasoning_loop_retries_clamp_sleep_to_remaining_budget(monkeypatch):
    """Transient errors clamp retry sleep to remaining total time budget."""

    call_counter = {"count": 0}

    def transient_then_complete(*_args, **_kwargs):
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            raise RuntimeError("transient")
        return {"status": "completed"}

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: transient_then_complete
    )

    monotonic_values = iter([0.0, 0.01, 0.07])

    def fake_monotonic() -> float:
        try:
            return next(monotonic_values)
        except StopIteration:
            return 0.07

    sleep_calls: list[float] = []

    def fake_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(rl.time, "sleep", fake_sleep)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "clamp"},
        critic_agent=None,
        retry_attempts=1,
        retry_backoff=0.05,
        max_total_seconds=0.1,
    )

    assert results == [{"status": "completed"}]
    assert call_counter["count"] == 2
    assert sleep_calls == pytest.approx([0.03], rel=1e-9)


@pytest.mark.fast
def test_reasoning_loop_stops_retry_when_total_budget_exhausted(monkeypatch):
    """Remaining budget exhaustion stops retries without invoking sleep."""

    call_counter = {"count": 0}

    def always_transient(*_args, **_kwargs):
        call_counter["count"] += 1
        raise RuntimeError("boom")

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: always_transient
    )

    monotonic_values = iter([0.0, 0.05, 0.2])

    def fake_monotonic() -> float:
        try:
            return next(monotonic_values)
        except StopIteration:
            return 0.2

    sleep_calls: list[float] = []

    def fake_sleep(duration: float) -> None:  # pragma: no cover - guard
        sleep_calls.append(duration)

    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(rl.time, "sleep", fake_sleep)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "exhaust"},
        critic_agent=None,
        retry_attempts=2,
        retry_backoff=0.05,
        max_total_seconds=0.1,
    )

    assert results == []
    assert call_counter["count"] == 1
    assert sleep_calls == []


@pytest.mark.fast
def test_reasoning_loop_coordinator_records_phase_transitions(monkeypatch):
    """Coordinator hooks receive results based on reported phases and transition map.

    ReqID: N/A
    """

    payloads: list[dict[str, Any]] = [
        {
            "phase": "expand",
            "next_phase": "differentiate",
            "status": "in_progress",
            "synthesis": {"draft": "alpha"},
        },
        {
            "phase": "differentiate",
            "status": "in_progress",
            "synthesis": {"draft": "beta"},
        },
        {
            "phase": "unexpected",
            "status": "completed",
        },
    ]

    calls_seen: list[dict[str, Any]] = []

    def scripted_responses(
        _wsde: NullWSDETeam,
        task: DialecticalTask,
        _critic: Any,
        _memory: Any,
    ) -> dict[str, Any]:
        snapshot = dict(task.to_dict())
        calls_seen.append(snapshot)
        try:
            return payloads[len(calls_seen) - 1]
        except IndexError:  # pragma: no cover - protective guard
            raise AssertionError("unexpected call")

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: scripted_responses
    )

    coordinator = CoordinatorRecorder()

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "demo"},
        critic_agent=None,
        coordinator=coordinator,
        phase=rl.Phase.EXPAND,
        max_iterations=5,
    )

    assert [result["status"] for result in results] == [
        payload["status"] for payload in payloads
    ]
    assert [result.get("phase") for result in results] == [
        payload.get("phase") for payload in payloads
    ]
    assert coordinator.records == [
        ("expand", payloads[0]),
        ("differentiate", payloads[1]),
        ("refine", payloads[2]),
    ]
    assert calls_seen[0]["solution"] is None
    assert calls_seen[1]["solution"] == payloads[0]["synthesis"]
    assert calls_seen[2]["solution"] == payloads[1]["synthesis"]


@pytest.mark.fast
def test_reasoning_loop_records_dialectical_sequences_for_coordinator(monkeypatch):
    """Coordinator receives dict copies when dialectical sequences report phases."""

    phases = [
        ("expand", "differentiate", "in_progress", {"draft": "alpha"}),
        ("differentiate", "refine", "in_progress", {"draft": "beta"}),
        ("refine", None, "completed", {"draft": "gamma"}),
    ]

    sequences: list[DialecticalSequence] = []

    def build_sequence(index: int) -> DialecticalSequence:
        phase, next_phase, status, synthesis = phases[index]
        timestamp = datetime(2024, 1, 1) + timedelta(minutes=index)
        step_payload = {
            "id": f"step-{index}",
            "timestamp": timestamp,
            "task_id": f"task-{index}",
            "thesis": {"content": f"thesis-{index}"},
            "antithesis": {
                "id": f"antithesis-{index}",
                "timestamp": timestamp,
                "agent": "critic",
                "critiques": [],
                "critique_details": [],
                "alternative_approaches": [],
                "improvement_suggestions": [],
            },
            "synthesis": {
                "plan_id": f"plan-{index}",
                "timestamp": timestamp,
                "integrated_critiques": [],
                "rejected_critiques": [],
                "improvements": [],
                "reasoning": "",
                "content": f"content-{index}",
            },
            "method": "dialectical_reasoning",
        }
        sequence = DialecticalSequence.from_dict(
            {
                "sequence_id": f"sequence-{index}",
                "status": status,
                "steps": [step_payload],
            }
        )
        sequence._payload["phase"] = phase
        if next_phase is not None:
            sequence._payload["next_phase"] = next_phase
        else:
            sequence._payload.pop("next_phase", None)
        sequence._payload["synthesis"] = synthesis
        return sequence

    def scripted_sequences(*_args, **_kwargs) -> DialecticalSequence:
        index = len(sequences)
        sequence = build_sequence(index)
        sequences.append(sequence)
        return sequence

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: scripted_sequences
    )

    coordinator = CoordinatorRecorder()

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "phases"},
        critic_agent=None,
        coordinator=coordinator,
        phase=rl.Phase.EXPAND,
        max_iterations=5,
    )

    assert results == sequences
    assert [record[0] for record in coordinator.records] == [
        "expand",
        "differentiate",
        "refine",
    ]
    assert all(isinstance(record[1], dict) for record in coordinator.records)
    assert all(
        record[1] is not sequence
        for record, sequence in zip(coordinator.records, sequences)
    )
    assert [record[1]["phase"] for record in coordinator.records] == [
        phase for phase, *_ in phases
    ]
    assert [record[1].get("next_phase") for record in coordinator.records] == [
        next_phase for _, next_phase, *_ in phases
    ]
    assert [record[1]["synthesis"] for record in coordinator.records] == [
        synthesis for *_, synthesis in phases
    ]


@pytest.mark.fast
def test_reasoning_loop_fallbacks_for_invalid_phase_and_next_phase(monkeypatch, caplog):
    """Unknown phases rely on deterministic fallbacks for coordinator logging."""

    payloads = [
        {"status": "in_progress", "phase": "mystery", "next_phase": "???"},
        {"status": "in_progress", "phase": "mystery", "next_phase": "???"},
        {"status": "completed", "phase": "mystery", "next_phase": "???"},
    ]

    call_index = {"value": 0}

    def scripted(*_args, **_kwargs):
        index = call_index["value"]
        call_index["value"] += 1
        return dict(payloads[index])

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: scripted)

    coordinator = CoordinatorRecorder()

    caplog.set_level("INFO", rl.logger.logger.name)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "fallback"},
        critic_agent=None,
        coordinator=coordinator,
        phase=rl.Phase.EXPAND,
        max_iterations=5,
    )

    assert [record[0] for record in coordinator.records] == [
        "expand",
        "differentiate",
        "refine",
    ]
    assert [result["status"] for result in results] == [
        payload["status"] for payload in payloads
    ]
    assert any(
        message.startswith("Dialectical reasoning iteration")
        for message in caplog.messages
    )


@pytest.mark.fast
def test_reasoning_loop_honors_total_time_budget(monkeypatch):
    """The loop exits early when the total time budget is exhausted before an iteration.

    ReqID: N/A
    """

    call_counter = {"count": 0}

    def should_not_run(*_args, **_kwargs):  # pragma: no cover - guard
        call_counter["count"] += 1
        return {}

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: should_not_run
    )

    monotonic_values = iter([0.0, 0.2])

    def fake_monotonic() -> float:
        try:
            return next(monotonic_values)
        except StopIteration:
            return 0.2

    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "budget"},
        critic_agent=None,
        max_total_seconds=0.1,
    )

    assert results == []
    assert call_counter["count"] == 0


@pytest.mark.fast
def test_reasoning_loop_seeds_random_sources(monkeypatch):
    """Deterministic seed initialization calls both random and numpy seed APIs.

    ReqID: N/A
    """

    seeded: list[tuple[str, int]] = []

    def fake_random_seed(value: int) -> None:
        seeded.append(("random", value))

    monkeypatch.setattr("random.seed", fake_random_seed)

    def fake_numpy_seed(value: int) -> None:
        seeded.append(("numpy", value))

    numpy_random_module = types.ModuleType("numpy.random")
    numpy_random_module.seed = fake_numpy_seed  # type: ignore[attr-defined]
    numpy_module = types.ModuleType("numpy")
    numpy_module.random = numpy_random_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "numpy.random", numpy_random_module)
    monkeypatch.setitem(sys.modules, "numpy", numpy_module)

    payload = {"status": "completed", "phase": "refine"}

    def return_payload(*_args, **_kwargs):
        return DialecticalSequence.from_dict(payload)

    monkeypatch.setattr(
        rl,
        "_import_apply_dialectical_reasoning",
        lambda: return_payload,
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "seed"},
        critic_agent=None,
        deterministic_seed=123,
    )

    assert [result["status"] for result in results] == [payload["status"]]
    assert ("random", 123) in seeded
    assert ("numpy", 123) in seeded
