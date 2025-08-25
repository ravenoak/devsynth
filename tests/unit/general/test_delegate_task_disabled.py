from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl


def test_delegate_task_collaboration_disabled_succeeds():
    """Test that delegate task collaboration disabled succeeds.

    ReqID: N/A"""
    coord = AgentCoordinatorImpl({"features": {"wsde_collaboration": False}})
    result = coord.delegate_task({"team_task": True})
    assert result == {"success": False, "error": "Collaboration disabled"}
