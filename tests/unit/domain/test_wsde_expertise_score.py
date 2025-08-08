from unittest.mock import MagicMock

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


class DummyAgent:

    def __init__(self, expertise):
        self.expertise = expertise
        self.current_role = None


def test_calculate_expertise_score_multiple_matches():
    """Test that calculate expertise score multiple matches.

    ReqID: N/A"""
    team = WSDETeam(name="TestWsdeExpertiseScoreTeam")
    agent = DummyAgent(["python", "documentation"])
    team.add_agent(agent)
    task = {"language": "python", "description": "generate documentation"}
    score = team._calculate_expertise_score(agent, task)
    assert score > 1
