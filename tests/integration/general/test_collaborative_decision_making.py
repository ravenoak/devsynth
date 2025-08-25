import pytest

from devsynth.application.collaboration.collaborative_wsde_team import (
    CollaborativeWSDETeam,
)


class SimpleAgent:
    def __init__(self, name, expertise):
        self.name = name
        self.expertise = expertise
        self.current_role = None
        self.has_been_primus = False


def test_dynamic_role_reassignment_integration_succeeds():
    team = CollaborativeWSDETeam("team")
    doc = SimpleAgent("doc", ["documentation"])
    dev = SimpleAgent("dev", ["python"])
    team.add_agents([doc, dev])
    task = {"type": "documentation", "description": "Write API docs"}
    team.process_task(task)
    assert team.get_primus() == doc


def test_consensus_vote_tie_breaker_succeeds():
    team = CollaborativeWSDETeam("team")
    a1 = SimpleAgent("a1", ["a"])
    a2 = SimpleAgent("a2", ["b"])
    team.add_agents([a1, a2])
    task = {
        "id": "vote1",
        "type": "decision_task",
        "description": "Choose option",
        "options": ["a", "b"],
        "voting_method": "majority",
    }
    team.select_primus_by_expertise({})
    result = team.vote_on_critical_decision(task)
    assert result["status"] == "completed"
    assert result["result"] in task["options"]
    assert "Tie" in result["explanation"]
