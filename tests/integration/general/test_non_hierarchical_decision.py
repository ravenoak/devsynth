import types
from unittest.mock import MagicMock

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl


def test_non_hierarchical_conflict_resolution_succeeds():
    """Test that non hierarchical conflict resolution succeeds.

    ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    coordinator.team.build_consensus = MagicMock(return_value={"consensus": "done"})
    result = coordinator._resolve_conflicts({"solution": "a"}, {"solution": "b"})
    coordinator.team.build_consensus.assert_called_once()
    assert result["consensus"] == "done"
