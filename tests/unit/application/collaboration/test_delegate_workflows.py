import pytest

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.application.collaboration.exceptions import TeamConfigurationError
from devsynth.exceptions import ValidationError

class DummyAgent:
    def __init__(self, name, agent_type):
        self.name = name
        self.agent_type = agent_type
    def process(self, task):
        return {"result": self.name}


def make_coord():
    return AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})


def test_delegate_specific_agent():
    coord = make_coord()
    agent = DummyAgent("a", "type")
    coord.add_agent(agent)
    result = coord.delegate_task({"agent_type": "type"})
    assert result == {"result": "a"}


def test_delegate_team_task(monkeypatch):
    coord = make_coord()
    monkeypatch.setattr(coord, "_handle_team_task", lambda task: {"team": True})
    result = coord.delegate_task({"team_task": True})
    assert result == {"team": True}


def test_missing_agent(monkeypatch):
    coord = make_coord()
    with pytest.raises(ValidationError):
        coord.delegate_task({"agent_type": "none"})


def test_team_task_no_agents():
    coord = make_coord()
    coord.agents = []
    with pytest.raises(TeamConfigurationError):
        coord._handle_team_task({"team_task": True})
