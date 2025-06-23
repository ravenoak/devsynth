from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl


def test_delegate_task_collaboration_disabled():
    coord = AgentCoordinatorImpl({"features": {"wsde_collaboration": False}})
    result = coord.delegate_task({"team_task": True})
    assert result == {"success": False, "error": "Collaboration disabled"}
