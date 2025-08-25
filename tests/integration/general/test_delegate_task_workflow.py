import types
from unittest.mock import MagicMock

import pytest

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl


class SimpleAgent:

    def __init__(self, name, agent_type, expertise=None):
        self.name = name
        self.agent_type = agent_type
        self.current_role = None
        self.expertise = expertise or []
        self.config = types.SimpleNamespace(
            name=name, parameters={"expertise": self.expertise}
        )
        self.process = MagicMock(return_value={"solution": f"{name}-sol"})


def test_delegate_task_full_workflow_succeeds(mocker):
    """Test that delegate task full workflow succeeds.

    ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    planner = SimpleAgent("planner", "planner", ["planning"])
    coder = SimpleAgent("coder", "code", ["python"])
    validator = SimpleAgent("validator", "validation", ["testing"])
    critic = SimpleAgent("critic", "critic", ["analysis"])
    for agent in [planner, coder, validator, critic]:
        coordinator.add_agent(agent)
    team = coordinator.team
    consensus = {
        "consensus": "final",
        "contributors": [planner.name, coder.name, validator.name, critic.name],
        "method": "consensus_synthesis",
    }
    mock_build = mocker.patch.object(team, "build_consensus", return_value=consensus)
    mock_dialectical = mocker.patch.object(
        team, "apply_enhanced_dialectical_reasoning", return_value={"evaluation": "ok"}
    )
    task = {"team_task": True, "type": "coding", "language": "python"}
    result = coordinator.delegate_task(task)
    mock_build.assert_called_once_with(task)
    mock_dialectical.assert_called_once_with(task, critic)
    assert result["team_result"]["consensus"] == consensus
    assert result["result"] == "final"
    assert result["contributors"] == consensus["contributors"]
    assert result["method"] == "consensus_synthesis"
