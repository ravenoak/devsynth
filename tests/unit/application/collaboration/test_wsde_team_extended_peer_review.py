from types import SimpleNamespace

import pytest

from devsynth.application.collaboration.wsde_team_extended import CollaborativeWSDETeam


@pytest.mark.fast
def test_peer_review_solution_excludes_author() -> None:
    """ReqID: N/A"""

    team = CollaborativeWSDETeam()
    author = SimpleNamespace(name="author")
    reviewer = SimpleNamespace(name="reviewer")
    team.agents = [author, reviewer]

    called = {}

    def dummy_conduct(work_product, auth, reviewers):
        called["args"] = (work_product, auth, reviewers)
        return {"status": "ok"}

    team.conduct_peer_review = dummy_conduct  # type: ignore[assignment]
    result = team.peer_review_solution("artifact", author)

    assert result == {"status": "ok"}
    assert called["args"][0] == "artifact"
    assert called["args"][1] is author
    assert called["args"][2] == [reviewer]
