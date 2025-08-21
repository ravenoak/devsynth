"""Tests for :mod:`devsynth.agents.multi_agent_coordinator`."""

import pytest

from devsynth.agents import MultiAgentCoordinator


@pytest.mark.fast
def test_majority_consensus() -> None:
    """Coordinator returns the majority proposal. ReqID: FR-96"""
    agents = [lambda: "refactor", lambda: "refactor", lambda: "document"]
    coordinator = MultiAgentCoordinator(agents)
    result = coordinator.coordinate()
    assert result.decision == "refactor"
    assert result.rounds == 1


@pytest.mark.fast
def test_raises_when_no_consensus() -> None:
    """Coordinator raises when consensus is unreachable. ReqID: FR-96"""
    agents = [lambda: "a", lambda: "b", lambda: "c"]
    coordinator = MultiAgentCoordinator(agents)
    with pytest.raises(RuntimeError):
        coordinator.coordinate(max_rounds=1)
