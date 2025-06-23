import pytest
from unittest.mock import MagicMock
from devsynth.domain.models.wsde import WSDETeam


class DummyAgent:
    def __init__(self, expertise):
        self.expertise = expertise
        self.current_role = None


def test_calculate_expertise_score_multiple_matches():
    team = WSDETeam()
    agent = DummyAgent(["python", "documentation"])
    team.add_agent(agent)
    task = {"language": "python", "description": "generate documentation"}
    score = team._calculate_expertise_score(agent, task)
    assert score > 1
