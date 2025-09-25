from __future__ import annotations

import sys
import types

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.domain.models.wsde_dialectical import DialecticalSequence


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
        wsde_team=types.SimpleNamespace(),
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

    payloads = [
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

    calls_seen: list[dict[str, object]] = []

    def scripted_responses(_wsde, task, _critic, _memory):
        calls_seen.append(task.to_dict())
        try:
            return DialecticalSequence.from_dict(payloads[len(calls_seen) - 1])
        except IndexError:  # pragma: no cover - protective guard
            raise AssertionError("unexpected call")

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: scripted_responses
    )

    recorded: list[tuple[str, dict[str, object]]] = []

    class DummyCoordinator:
        def record_expand_results(self, result):
            recorded.append(("expand", result))

        def record_differentiate_results(self, result):
            recorded.append(("differentiate", result))

        def record_refine_results(self, result):
            recorded.append(("refine", result))

        def record_consensus_failure(self, exc):  # pragma: no cover - safeguard
            raise AssertionError(f"unexpected consensus failure: {exc}")

    coordinator = DummyCoordinator()

    results = rl.reasoning_loop(
        wsde_team=types.SimpleNamespace(),
        task={"problem": "demo"},
        critic_agent=None,
        coordinator=coordinator,
        phase=rl.Phase.EXPAND,
        max_iterations=5,
    )

    assert [dict(r) for r in results] == payloads
    assert recorded == [
        ("expand", payloads[0]),
        ("differentiate", payloads[1]),
        ("refine", payloads[2]),
    ]
    assert calls_seen[0] == {"problem": "demo"}
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
        wsde_team=types.SimpleNamespace(),
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
        wsde_team=types.SimpleNamespace(),
        task={"problem": "seed"},
        critic_agent=None,
        deterministic_seed=123,
    )

    assert [dict(r) for r in results] == [payload]
    assert ("random", 123) in seeded
    assert ("numpy", 123) in seeded
