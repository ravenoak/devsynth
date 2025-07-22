import pytest
from devsynth.domain.models.wsde import WSDETeam


class DummyAgent:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def wsde_team():
    team = WSDETeam(name="PeerReviewTeam")
    team.add_agent(DummyAgent("author"))
    team.add_agent(DummyAgent("reviewer1"))
    team.add_agent(DummyAgent("reviewer2"))
    return team


def test_wsde_team_peer_review_methods(wsde_team):
    author = wsde_team.agents[0]
    reviewers = wsde_team.agents[1:]
    review = wsde_team.request_peer_review({"text": "demo"}, author, reviewers)
    assert review is not None
    result = wsde_team.conduct_peer_review({"text": "demo"}, author, reviewers)
    assert "feedback" in result
    assert "review" in result
