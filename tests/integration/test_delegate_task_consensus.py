import types
from unittest.mock import MagicMock, patch

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl

class SimpleAgent:
    def __init__(self, name, agent_type):
        self.name = name
        self.agent_type = agent_type
        self.current_role = None
        self.expertise = []
        self.process = MagicMock(return_value={"solution": f"{name}-sol"})
        self.config = types.SimpleNamespace(name=name, parameters={})


def test_delegate_task_team_consensus():
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    a1 = SimpleAgent("planner", "planner")
    a2 = SimpleAgent("coder", "code")
    for a in [a1, a2]:
        coordinator.add_agent(a)

    consensus = {"consensus": "final", "contributors": ["planner", "coder"], "method": "consensus_synthesis"}

    with patch.object(coordinator.team, "build_consensus", return_value=consensus):
        result = coordinator.delegate_task({"team_task": True, "action": "do"})

    assert result["team_result"]["consensus"] == consensus
    assert result["contributors"] == ["planner", "coder"]
    assert result["method"] == "consensus_synthesis"
    assert result["result"] == "final"
    assert len(result["team_result"]["solutions"]) == 2
