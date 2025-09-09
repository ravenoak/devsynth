import types

import pytest

from devsynth.domain.models.wsde_facade import WSDETeam


class SimpleAgent:
    def __init__(self, name: str, expertise=None):
        self.name = name
        self.expertise = expertise or []
        self.config = types.SimpleNamespace(parameters={"expertise": self.expertise})


@pytest.mark.fast
def test_summarize_consensus_result_outputs_expected_sections():
    team = WSDETeam(name="facade")
    team.add_agents([SimpleAgent("a")])
    consensus = {
        "method": "discussion",
        "majority_opinion": "option a",
        "synthesis": {"text": "merged"},
        "conflicts_identified": 1,
        "stakeholder_explanation": "because",
    }
    summary = team.summarize_consensus_result(consensus)
    assert "Consensus was reached using discussion." in summary
    assert "The majority opinion is: option a" in summary
    assert "Synthesis: merged" in summary
    assert "1 conflict was identified and resolved." in summary
    assert "Explanation: because" in summary


@pytest.mark.fast
def test_summarize_voting_result_reports_winner_and_counts():
    team = WSDETeam(name="facade")
    team.add_agents([SimpleAgent("a"), SimpleAgent("b")])
    voting_result = {
        "status": "completed",
        "result": {
            "method": "majority",
            "winner": "A",
            "tie_broken": True,
            "tie_breaker_method": "primus",
        },
        "vote_counts": {"A": 2, "B": 1},
        "vote_weights": {"a": 1.0, "b": 1.5},
    }
    summary = team.summarize_voting_result(voting_result)
    assert "Voting was completed using majority." in summary
    assert "The winning option is: A" in summary
    assert "A: 2 votes" in summary
    assert "B: 1 votes" in summary
    assert "Vote weights: a: 1.00, b: 1.50" in summary
    assert "A tie was broken using primus." in summary
