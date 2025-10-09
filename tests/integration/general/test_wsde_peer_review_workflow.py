import pytest

from devsynth.application.collaboration.peer_review import run_peer_review
from devsynth.domain.models.wsde_facade import WSDETeam


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


@pytest.mark.slow
def test_run_peer_review_workflow(wsde_team):
    author = wsde_team.agents[0]
    reviewers = wsde_team.agents[1:]
    result = run_peer_review({"text": "demo"}, author, reviewers)
    assert result["status"] in {"approved", "rejected"}
    assert "workflow" in result
    assert "revision_cycles" in result["workflow"]
