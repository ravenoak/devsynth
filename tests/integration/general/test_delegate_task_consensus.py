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


def test_delegate_task_team_consensus_succeeds():
    """Test that delegate task team consensus succeeds.

    ReqID: N/A"""
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
        result = coordinator.delegate_task(
            {"team_task": True, "type": "coding", "language": "python"}
        )
    primus = coordinator.team.get_primus()
    assert primus == coder
    assert coordinator.team.primus_index == coordinator.team.agents.index(coder)
    assert primus.name in result["team_result"]["consensus"]["contributors"]
    assert result["contributors"] == [coder.name, writer.name]
    assert result["method"] == "consensus_synthesis"
    assert result["result"] == "final"
    assert len(result["team_result"]["solutions"]) == 3


class VotingAgent:

    def __init__(self, name, vote):
        self.name = name
        self.vote = vote
        self.agent_type = "voter"
        self.current_role = None
        self.config = types.SimpleNamespace(name=name, parameters={})

    def process(self, task):
        if task.get("type") == "critical_decision":
            return {"vote": self.vote}
        return {"solution": f"{self.name}-sol"}


def test_critical_decision_majority_vote_succeeds():
    """Test that critical decision majority vote succeeds.

    ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    a1 = VotingAgent("a1", "o1")
    a2 = VotingAgent("a2", "o2")
    a3 = VotingAgent("a3", "o2")
    for a in [a1, a2, a3]:
        coordinator.add_agent(a)
    task = {
        "team_task": True,
        "type": "critical_decision",
        "is_critical": True,
        "options": [{"id": "o1"}, {"id": "o2"}],
    }
    with (
        patch.object(
            coordinator.team,
            "vote_on_critical_decision",
            wraps=coordinator.team.vote_on_critical_decision,
        ) as vote_spy,
        patch.object(
            coordinator.team, "build_consensus", wraps=coordinator.team.build_consensus
        ) as consensus_spy,
    ):
        result = coordinator.delegate_task(task)
    vote_spy.assert_called_once_with(task)
    consensus_spy.assert_not_called()
    assert result["result"]["winner"] == "o2"
    assert result["result"]["method"] == "majority_vote"


def test_critical_decision_tied_vote_falls_back_to_consensus_succeeds():
    """Test that critical decision tied vote falls back to consensus succeeds.

    ReqID: N/A"""
    coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
    a1 = VotingAgent("a1", "o1")
    a2 = VotingAgent("a2", "o2")
    a3 = VotingAgent("a3", "o1")
    a4 = VotingAgent("a4", "o2")
    for a in [a1, a2, a3, a4]:
        coordinator.add_agent(a)
    consensus_result = {
        "consensus": "combined",
        "contributors": [a.name for a in [a1, a2, a3, a4]],
        "method": "consensus_synthesis",
    }
    task = {
        "team_task": True,
        "type": "critical_decision",
        "is_critical": True,
        "options": [{"id": "o1"}, {"id": "o2"}],
    }
    with (
        patch.object(
            coordinator.team, "build_consensus", return_value=consensus_result
        ) as consensus_spy,
        patch.object(
            coordinator.team,
            "vote_on_critical_decision",
            wraps=coordinator.team.vote_on_critical_decision,
        ) as vote_spy,
    ):
        result = coordinator.delegate_task(task)
    vote_spy.assert_called_once_with(task)
    consensus_spy.assert_called_once()
    assert result["result"]["tied"] is True
    assert result["result"]["fallback"] == "consensus"
    assert result["result"]["consensus_result"] == consensus_result
