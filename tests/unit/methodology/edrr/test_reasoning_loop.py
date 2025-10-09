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
