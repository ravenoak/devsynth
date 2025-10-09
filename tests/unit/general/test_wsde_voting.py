"""Tests for WSDETeam voting mechanisms."""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam

pytestmark = [pytest.mark.fast]


def _make_agent(name: str, vote: str, expertise=None, level="novice"):
    agent = MagicMock()
    agent.name = name
    agent.config = MagicMock()
    agent.config.name = name
    params = {}
    if expertise:
        params["expertise"] = expertise
    params["expertise_level"] = level
    agent.config.parameters = params
    agent.process = MagicMock(return_value={"vote": vote})
    return agent


def _basic_task():
    return {
        "type": "critical_decision",
        "description": "choose option",
        "options": [{"id": "option1"}, {"id": "option2"}, {"id": "option3"}],
        "is_critical": True,
    }


def test_majority_vote_with_three_unique_choices_succeeds():
    """Test that when three agents vote for three different options, it results in a tie.

    ReqID: N/A"""
    team = WSDETeam(name="TestTeam")
    a1 = _make_agent("a1", "option1")
    a2 = _make_agent("a2", "option2")
    a3 = _make_agent("a3", "option3")
    team.add_agents([a1, a2, a3])
    task = _basic_task()
    with patch.object(team, "build_consensus", return_value={"consensus": ""}):
        result = team.vote_on_critical_decision(task)
    assert result["result"]["method"] == "tied_vote"
    assert set(result["result"]["tied_options"]) == {"option1", "option2", "option3"}


def test_tie_triggers_handle_tied_vote_succeeds():
    """Test that a tie between two options triggers the _handle_tied_vote method.

    ReqID: N/A"""
    team = WSDETeam(name="TestTeam")
    a1 = _make_agent("a1", "option1")
    a2 = _make_agent("a2", "option2")
    team.add_agents([a1, a2])
    task = _basic_task()
    with (
        patch.object(team, "build_consensus", return_value={"consensus": ""}),
        patch.object(team, "_handle_tied_vote", wraps=team._handle_tied_vote) as mocked,
    ):
        team.vote_on_critical_decision(task)
        mocked.assert_called_once()


def test_weighted_voting_prefers_expert_vote_succeeds():
    """Test that weighted voting gives preference to expert votes over novice votes.

    ReqID: N/A"""
    team = WSDETeam(name="TestTeam")
    expert = _make_agent("expert", "option2", ["security"], level="expert")
    novice1 = _make_agent("novice1", "option1", ["security"], level="novice")
    novice2 = _make_agent("novice2", "option1", ["security"], level="novice")
    team.add_agents([expert, novice1, novice2])
    task = _basic_task()
    task["domain"] = "security"
    result = team.vote_on_critical_decision(task)
    assert result["result"]["method"] == "weighted_vote"
    assert result["result"]["winner"] == "option2"


def test_vote_on_critical_decision_no_votes_succeeds():
    """Test that vote_on_critical_decision handles the case when no votes are cast.

    ReqID: N/A"""
    team = WSDETeam(name="TestTeam")
    a1 = _make_agent("a1", vote=None)
    a1.process.return_value = {}
    team.add_agent(a1)
    task = _basic_task()
    result = team.vote_on_critical_decision(task)
    assert result["voting_initiated"] is True
    assert result["votes"] == {}
    assert result["result"] is None
