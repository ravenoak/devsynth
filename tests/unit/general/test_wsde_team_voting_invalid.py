import pytest

from devsynth.domain.models.wsde_facade import WSDETeam

pytestmark = [pytest.mark.fast]


def test_vote_on_critical_decision_not_critical_raises_error():
    """Test that vote_on_critical_decision returns an error when task is not critical.

    ReqID: N/A"""
    team = WSDETeam(name="TestTeam")
    result = team.vote_on_critical_decision({"type": "other"})
    assert result["voting_initiated"] is False
    assert "error" in result


def test_vote_on_critical_decision_no_options_raises_error():
    """Test that vote_on_critical_decision returns an error when no options are provided.

    ReqID: N/A"""
    team = WSDETeam(name="TestTeam")
    task = {"type": "critical_decision", "is_critical": True, "options": []}
    result = team.vote_on_critical_decision(task)
    assert result["voting_initiated"] is False
    assert "error" in result
