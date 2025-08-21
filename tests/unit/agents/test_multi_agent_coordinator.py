"""Tests for :mod:`devsynth.agents.multi_agent_coordinator`. ReqID: MAC-001"""

import pytest

from devsynth.agents import MultiAgentCoordinator


@pytest.mark.fast
def test_reach_consensus_majority_choice() -> None:
    """ReqID: MAC-001"""
    coordinator = MultiAgentCoordinator()
    coordinator.register_agent("a1", lambda _: "A")
    coordinator.register_agent("a2", lambda _: "A")
    coordinator.register_agent("a3", lambda _: "B")

    decision = coordinator.reach_consensus(task=None)
    assert decision == "A"
