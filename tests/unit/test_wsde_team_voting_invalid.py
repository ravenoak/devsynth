from devsynth.domain.models.wsde import WSDETeam


def test_vote_on_critical_decision_not_critical():
    team = WSDETeam()
    result = team.vote_on_critical_decision({"type": "other"})
    assert result["voting_initiated"] is False
    assert "error" in result


def test_vote_on_critical_decision_no_options():
    team = WSDETeam()
    task = {"type": "critical_decision", "is_critical": True, "options": []}
    result = team.vote_on_critical_decision(task)
    assert result["voting_initiated"] is False
    assert "error" in result
