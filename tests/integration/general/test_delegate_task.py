import types
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.application.collaboration.exceptions import TeamConfigurationError
from devsynth.exceptions import ValidationError


class SimpleAgent:

    def __init__(self, name: str, agent_type: str, expertise=None):
        self.name = name
        self.agent_type = agent_type
        self.current_role = None
        self.expertise = expertise or []
        self.config = types.SimpleNamespace(
            name=name, parameters={"expertise": self.expertise}
        )
        self.process = MagicMock(return_value={"solution": f"{name}-sol"})


def test_delegate_task_team_consensus_succeeds(mocker):
    """Test that delegate task team consensus succeeds.

    ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    planner = SimpleAgent("planner", "planner", ["planning"])
    coder = SimpleAgent("coder", "code", ["python"])
    tester = SimpleAgent("tester", "test", ["pytest"])
    validator = SimpleAgent("validator", "validation", ["qa"])
    critic = SimpleAgent("critic", "critic", ["analysis"])
    for agent in [planner, coder, tester, validator, critic]:
        coordinator.add_agent(agent)
    team = coordinator.team
    consensus = {
        "consensus": "final",
        "contributors": [a.name for a in [planner, coder, tester, validator, critic]],
        "method": "consensus_synthesis",
    }
    mock_build = mocker.patch.object(team, "build_consensus", return_value=consensus)
    mock_dialectical = mocker.patch.object(
        team, "apply_enhanced_dialectical_reasoning", return_value={"evaluation": "ok"}
    )
    result = coordinator.delegate_task({"team_task": True})
    mock_build.assert_called_once_with({"team_task": True})
    mock_dialectical.assert_called_once_with({"team_task": True}, critic)
    assert result["method"] == "consensus_synthesis"
    assert set(result["contributors"]) == set(consensus["contributors"])
    assert result["team_result"]["consensus"] == consensus


def test_delegate_task_no_agents_succeeds():
    """Test that delegate task no agents succeeds.

    ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    with pytest.raises(TeamConfigurationError):
        coordinator.delegate_task({"team_task": True})


def test_delegate_task_invalid_task_succeeds():
    """Test that delegate task invalid task succeeds.

    ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    coordinator.add_agent(SimpleAgent("planner", "planner"))
    with pytest.raises(ValidationError):
        coordinator.delegate_task({})
