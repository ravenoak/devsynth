from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.methodology.edrr.contracts import (
    CoordinatorRecorder,
    MemoryIntegrationLog,
    NullWSDETeam,
)
from devsynth.methodology.edrr.reasoning_loop import Phase


@pytest.mark.fast
def test_reasoning_loop_completes_with_deterministic_seed(monkeypatch):
    """Basic completion still works when the apply function is patched.

    ReqID: N/A"""

    calls = {"count": 0}

    def fake_apply(wsde_team, task, critic_agent, memory_integration):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "status": "in_progress",
                "synthesis": "partial",
                "phase": "expand",
                "next_phase": "differentiate",
            }
        return {
            "status": "completed",
            "synthesis": "final",
            "phase": "refine",
        }

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    out = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "X"},
        critic_agent=None,
        phase=Phase.REFINE,
        max_iterations=5,
        deterministic_seed=123,
        max_total_seconds=1.0,
    )

    assert len(out) == 2
    assert out[-1]["status"] == "completed"
    assert out[0]["synthesis"] == "partial"
    assert out[1]["synthesis"] == "final"


@pytest.mark.fast
def test_reasoning_loop_phase_transitions_and_memory_integration(monkeypatch):
    """Next-phase overrides, synthesis propagation, and seeding are honored.

    ReqID: N/A"""

    results_sequence = [
        {
            "status": "in_progress",
            "synthesis": {"content": "step-1"},
            "phase": "invalid-phase",
            "next_phase": "differentiate",
        },
        {
            "status": "in_progress",
            "synthesis": {"content": "step-2"},
            "phase": "still-invalid",
            "next_phase": "not-a-phase",
        },
        {
            "status": "completed",
            "synthesis": {"content": "step-3"},
            "phase": "refine",
            "next_phase": "differentiate",
        },
    ]

    call_log: list[dict[str, Any]] = []
    memory = MemoryIntegrationLog()
    coordinator = CoordinatorRecorder()

    def scripted_apply(wsde_team, task, critic_agent, memory_integration):
        index = len(call_log)
        call_log.append({"task": task, "memory": memory_integration})
        assert memory_integration is memory
        result = results_sequence[index]
        memory_integration.store_dialectical_result(task, result)
        return result

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: scripted_apply
    )

    import random

    random_seeds: list[int] = []

    def fake_random_seed(value: int) -> None:
        random_seeds.append(value)

    monkeypatch.setattr(random, "seed", fake_random_seed)

    numpy_seeds: list[int] = []
    fake_numpy_random = types.ModuleType("numpy.random")

    def fake_numpy_seed(value: int) -> None:
        numpy_seeds.append(value)

    setattr(fake_numpy_random, "seed", fake_numpy_seed)
    fake_numpy = types.ModuleType("numpy")
    setattr(fake_numpy, "random", fake_numpy_random)
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "numpy.random", fake_numpy_random)

    initial_task = {"problem": "X", "solution": {"content": "initial"}}

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task=initial_task,
        critic_agent=None,
        memory_integration=memory,
        phase=Phase.EXPAND,
        coordinator=coordinator,
        deterministic_seed=99,
        max_iterations=5,
    )

    assert [result["status"] for result in results] == [
        payload["status"] for payload in results_sequence
    ]
    assert [result.get("phase") for result in results] == [
        payload.get("phase") for payload in results_sequence
    ]
    assert [entry[0] for entry in coordinator.records] == [
        "expand",
        "differentiate",
        "refine",
    ]
    assert coordinator.failures == []

    assert [call["memory"] for call in call_log] == [memory, memory, memory]
    assert call_log[1]["task"]["solution"] == results_sequence[0]["synthesis"]
    assert call_log[2]["task"]["solution"] == results_sequence[1]["synthesis"]

    assert [task["solution"] for task, _ in memory.calls] == [
        {"content": "initial"},
        {"content": "step-1"},
        {"content": "step-2"},
    ]

    assert random_seeds == [99]
    assert numpy_seeds == [99]


@pytest.mark.fast
def test_reasoning_loop_time_budget_exceeded(monkeypatch):
    """Time budget enforcement prevents infinite loops.

    ReqID: N/A"""

    def slow_apply(wsde_team, task, critic_agent, memory_integration):
        import time
        time.sleep(0.1)  # Simulate slow operation
        return {"status": "in_progress", "synthesis": "ongoing"}

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: slow_apply)

    import time
    start = time.monotonic()
    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "X"},
        critic_agent=None,
        max_iterations=10,  # High iteration count
        max_total_seconds=0.05,  # Very short budget
        deterministic_seed=42,
    )
    elapsed = time.monotonic() - start

    # Should exit early due to time budget, not iteration limit
    assert elapsed < 0.2  # Should be much less than 10 iterations * 0.1s
    assert len(results) < 10  # Should not complete all iterations


@pytest.mark.fast
def test_reasoning_loop_consensus_error_handling(monkeypatch):
    """ConsensusError is caught and logged, stopping iteration.

    ReqID: N/A"""

    from devsynth.exceptions import ConsensusError

    calls = {"count": 0}

    def failing_apply(wsde_team, task, critic_agent, memory_integration):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConsensusError("Team cannot agree")
        return {"status": "completed"}

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: failing_apply)

    coordinator = CoordinatorRecorder()

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "X"},
        critic_agent=None,
        coordinator=coordinator,
        max_iterations=3,
    )

    assert len(results) == 0  # No results due to immediate failure
    assert len(coordinator.failures) == 1
    assert "cannot agree" in str(coordinator.failures[0])


@pytest.mark.fast
def test_reasoning_loop_transient_error_retry(monkeypatch):
    """Transient errors trigger retries with exponential backoff.

    ReqID: N/A"""

    calls = {"count": 0}

    def flaky_apply(wsde_team, task, critic_agent, memory_integration):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("Temporary network issue")
        return {"status": "completed", "synthesis": "success"}

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: flaky_apply)

    import time
    start = time.monotonic()
    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "X"},
        critic_agent=None,
        max_iterations=3,
        retry_attempts=2,
        deterministic_seed=42,
    )
    elapsed = time.monotonic() - start

    assert len(results) == 1
    assert results[0]["status"] == "completed"
    assert calls["count"] == 2  # First call failed, second succeeded
    assert elapsed >= 0.05  # Some backoff time


@pytest.mark.fast
def test_reasoning_loop_result_type_handling(monkeypatch):
    """Different result types (dict vs DialecticalSequence) are handled correctly.

    ReqID: N/A"""

    from devsynth.domain.models.wsde_dialectical import DialecticalSequence

    call_count = 0

    def typed_apply(wsde_team, task, critic_agent, memory_integration):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"status": "in_progress", "phase": "expand"}
        # Create a minimal DialecticalSequence that implements Mapping
        class MockDialecticalSequence(dict):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

        sequence = MockDialecticalSequence(
            status="completed",
            synthesis="final_result",
            phase="refine"
        )
        return sequence

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: typed_apply)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "X"},
        critic_agent=None,
        max_iterations=3,
    )

    assert len(results) == 2
    assert results[0]["status"] == "in_progress"
    assert results[1]["status"] == "completed"
    assert results[1]["synthesis"] == "final_result"


@pytest.mark.fast
def test_reasoning_loop_phase_override_from_result(monkeypatch):
    """Phase from result payload overrides coordinator phase when valid.

    ReqID: N/A"""

    results_sequence = [
        {"status": "in_progress", "phase": "custom_phase", "next_phase": "differentiate"},
        {"status": "completed", "phase": "refine"},
    ]

    call_count = 0
    coordinator = CoordinatorRecorder()

    def scripted_apply(wsde_team, task, critic_agent, memory_integration):
        nonlocal call_count
        result = results_sequence[call_count]
        call_count += 1
        return result

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: scripted_apply)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "X"},
        critic_agent=None,
        coordinator=coordinator,
        phase=Phase.EXPAND,
        max_iterations=3,
    )

    # Should record using the phase from result, not the coordinator phase
    assert len(coordinator.records) == 2
    assert coordinator.records[0][0] == "expand"  # Initial phase
    assert coordinator.records[1][0] == "refine"  # Phase from result


@pytest.mark.fast
def test_reasoning_loop_invalid_result_type_raises(monkeypatch):
    """Invalid result type raises TypeError.

    ReqID: N/A"""

    def invalid_apply(wsde_team, task, critic_agent, memory_integration):
        return "invalid_result_type"

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: invalid_apply)

    with pytest.raises(TypeError, match="apply_dialectical_reasoning must return a mapping payload"):
        rl.reasoning_loop(
            wsde_team=NullWSDETeam(),
            task={"problem": "X"},
            critic_agent=None,
            max_iterations=1,
        )


@pytest.mark.fast
def test_reasoning_loop_deterministic_phase_transitions(monkeypatch):
    """Phase transitions follow deterministic fallback map when next_phase is invalid.

    ReqID: N/A"""

    results_sequence = [
        {"status": "in_progress", "next_phase": "invalid_phase"},
        {"status": "completed"},
    ]

    call_count = 0

    def scripted_apply(wsde_team, task, critic_agent, memory_integration):
        nonlocal call_count
        result = results_sequence[call_count]
        call_count += 1
        return result

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: scripted_apply)

    # Start in EXPAND phase - should transition to DIFFERENTIATE
    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "X"},
        critic_agent=None,
        phase=Phase.EXPAND,
        max_iterations=3,
    )

    assert len(results) == 2
    # Should complete both iterations without phase validation errors
