"""Tests for reasoning loop recursion invariants documented in reasoning_loop_invariants.md."""

from __future__ import annotations

import importlib
from typing import Any, Callable

import pytest

from devsynth.methodology.edrr.reasoning_loop import Phase

rl = importlib.import_module("devsynth.methodology.edrr.reasoning_loop")


class _RecordingCoordinator:
    """Coordinator that captures the order of recorded EDRR phases."""

    def __init__(self) -> None:
        self.recorded_phases: list[Phase] = []
        self.consensus_failures: list[Exception] = []

    def _remember(self, phase: Phase, result: dict[str, Any]) -> dict[str, Any]:
        self.recorded_phases.append(phase)
        return result

    def record_expand_results(self, result: dict[str, Any]) -> dict[str, Any]:
        return self._remember(Phase.EXPAND, result)

    def record_differentiate_results(self, result: dict[str, Any]) -> dict[str, Any]:
        return self._remember(Phase.DIFFERENTIATE, result)

    def record_refine_results(self, result: dict[str, Any]) -> dict[str, Any]:
        return self._remember(Phase.REFINE, result)

    def record_consensus_failure(self, error: Exception) -> None:  # pragma: no cover - defensive
        self.consensus_failures.append(error)


@pytest.fixture
def _patch_reasoning_loop(monkeypatch: pytest.MonkeyPatch) -> Callable[[Callable[..., dict[str, Any]]], None]:
    """Patch the reasoning loop internals to use a deterministic callable."""

    def _apply(fake: Callable[..., dict[str, Any]]) -> None:
        monkeypatch.setattr(
            rl, "_apply_dialectical_reasoning", fake, raising=False
        )
        monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake)

    return _apply


@pytest.mark.fast
def test_reasoning_loop_converges_to_refine_without_next_phase(
    _patch_reasoning_loop: Callable[[Callable[..., dict[str, Any]]], None],
) -> None:
    """The fallback phase transition reaches REFINE within two recursive iterations."""

    coordinator = _RecordingCoordinator()
    calls: list[dict[str, Any]] = []

    def fake_apply(_: Any, task: dict[str, Any], __: Any, ___: Any) -> dict[str, Any]:
        calls.append(task.copy())
        if len(calls) < 3:
            return {"status": "in_progress"}
        return {"status": "completed"}

    _patch_reasoning_loop(fake_apply)

    results = rl.reasoning_loop(
        wsde_team=None,
        task={"solution": "initial"},
        critic_agent=None,
        coordinator=coordinator,
        phase=Phase.EXPAND,
        max_iterations=5,
    )

    assert len(results) == 3
    assert [phase.value for phase in coordinator.recorded_phases] == [
        Phase.EXPAND.value,
        Phase.DIFFERENTIATE.value,
        Phase.REFINE.value,
    ], "Phase convergence invariant violated; see docs/implementation/reasoning_loop_invariants.md"


@pytest.mark.fast
def test_reasoning_loop_propagates_synthesis_between_iterations(
    _patch_reasoning_loop: Callable[[Callable[..., dict[str, Any]]], None]
) -> None:
    """Each recursive call receives the prior synthesis as the next solution."""

    observed_solutions: list[str] = []
    syntheses = ["draft", "refined", "final"]

    def fake_apply(_: Any, task: dict[str, Any], __: Any, ___: Any) -> dict[str, Any]:
        observed_solutions.append(task["solution"])
        index = len(observed_solutions) - 1
        payload = {"synthesis": syntheses[index]}
        if index < 2:
            payload["status"] = "in_progress"
        else:
            payload["status"] = "completed"
        return payload

    _patch_reasoning_loop(fake_apply)

    results = rl.reasoning_loop(
        wsde_team=None,
        task={"solution": "initial"},
        critic_agent=None,
        max_iterations=3,
    )

    assert observed_solutions == [
        "initial",
        "draft",
        "refined",
    ], "Synthesis propagation invariant violated; see docs/implementation/reasoning_loop_invariants.md"
    assert [result["synthesis"] for result in results] == syntheses
