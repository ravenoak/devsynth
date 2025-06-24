import types
from unittest.mock import MagicMock, patch

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl


class SimpleAgent:
    def __init__(self, name, agent_type, expertise):
        self.name = name
        self.agent_type = agent_type
        self.current_role = None
        self.expertise = expertise
        self.config = types.SimpleNamespace(name=name, parameters={})
        self.process = MagicMock(return_value={"solution": name})


def test_delegate_task_calls_select_primus_by_expertise_and_updates_primus():
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    doc = SimpleAgent("doc", "docs", ["documentation", "markdown"])
    coder = SimpleAgent("coder", "code", ["python"])
    coordinator.add_agent(doc)
    coordinator.add_agent(coder)

    consensus = {"consensus": "x", "contributors": ["doc", "coder"], "method": "consensus_synthesis"}
    with patch.object(coordinator.team, "build_consensus", return_value=consensus), \
         patch.object(coordinator.team, "select_primus_by_expertise", wraps=coordinator.team.select_primus_by_expertise) as spy:
        result1 = coordinator.delegate_task({"team_task": True, "type": "coding", "language": "python"})
        first_primus = coordinator.team.get_primus().name
        result2 = coordinator.delegate_task({"team_task": True, "type": "documentation"})
        second_primus = coordinator.team.get_primus().name

    assert spy.call_count == 2
    assert first_primus == "coder"
    assert second_primus == "doc"
    assert result1["method"] == "consensus_synthesis"
    assert result2["method"] == "consensus_synthesis"
