from __future__ import annotations

import sys
import types
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
