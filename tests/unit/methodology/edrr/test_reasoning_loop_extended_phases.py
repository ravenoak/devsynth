"""Additional fast tests covering extended phase fallbacks in reasoning_loop."""

from __future__ import annotations

from collections import deque
from typing import Any

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.methodology.edrr.contracts import CoordinatorRecorder, NullWSDETeam
from devsynth.methodology.edrr.reasoning_loop import Phase


@pytest.mark.fast
def test_reasoning_loop_preserves_nonstandard_phase_without_hints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-standard phases fall back to the refine recorder when no hints are provided."""

    call_order: deque[str] = deque()

    def scripted_apply(
        wsde_team: Any,
        task: Any,
        critic: Any,
        memory: Any,
    ) -> dict[str, Any]:
        call_order.append("call")
        if len(call_order) == 1:
            return {"status": "running"}
        return {"status": "completed"}

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: scripted_apply
    )

    coordinator = CoordinatorRecorder()
    results = rl.reasoning_loop(
        NullWSDETeam(),
        {"problem": "nonstandard"},
        critic_agent=None,
        phase=Phase.RETROSPECT,
        max_iterations=3,
        coordinator=coordinator,
    )

    assert len(call_order) == 2
    assert len(results) == 2
    assert [phase for phase, _ in coordinator.records] == ["refine", "refine"]


@pytest.mark.fast
def test_reasoning_loop_handles_extended_phase_transitions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Extended phases transition via string hints and continue using refine fallback."""

    call_index = 0

    def scripted_apply(
        wsde_team: Any,
        task: Any,
        critic: Any,
        memory: Any,
    ) -> dict[str, Any]:
        nonlocal call_index
        call_index += 1
        if call_index == 1:
            return {"status": "running", "phase": "analysis", "next_phase": "analysis"}
        if call_index == 2:
            return {"status": "running"}
        return {"status": "completed"}

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: scripted_apply
    )

    coordinator = CoordinatorRecorder()
    results = rl.reasoning_loop(
        NullWSDETeam(),
        {"problem": "analysis-phase"},
        critic_agent=None,
        phase=Phase.RETROSPECT,
        max_iterations=5,
        coordinator=coordinator,
    )

    assert call_index == 3
    assert len(results) == 3
    assert [phase for phase, _ in coordinator.records] == ["refine", "refine", "refine"]
