import types
from unittest.mock import MagicMock, patch

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl

class SimpleAgent:
    def __init__(self, name, agent_type, expertise=None):
        self.name = name
        self.agent_type = agent_type
        self.current_role = None
        self.expertise = expertise or []
        self.process = MagicMock(return_value={"solution": f"{name}-sol"})
        self.config = types.SimpleNamespace(name=name, parameters={})


def test_delegate_task_team_consensus():
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})

    planner = SimpleAgent("planner", "planner", ["planning"])
    coder = SimpleAgent("coder", "code", ["python"])
    writer = SimpleAgent("writer", "docs", ["documentation"])

    for a in [planner, coder, writer]:
        coordinator.add_agent(a)

    def fake_consensus(_task):
        primus_name = coordinator.team.get_primus().name
        return {
            "consensus": "final",
            "contributors": [primus_name, writer.name],
            "method": "consensus_synthesis",
        }

    with patch.object(coordinator.team, "build_consensus", side_effect=fake_consensus):
        result = coordinator.delegate_task({"team_task": True, "type": "coding", "language": "python"})

    primus = coordinator.team.get_primus()
    assert primus == coder
    assert coordinator.team.primus_index == coordinator.team.agents.index(coder)
    assert primus.name in result["team_result"]["consensus"]["contributors"]
    assert result["contributors"] == [coder.name, writer.name]
    assert result["method"] == "consensus_synthesis"
    assert result["result"] == "final"
    assert len(result["team_result"]["solutions"]) == 3
