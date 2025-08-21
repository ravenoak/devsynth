import copy
import random

import pytest

from devsynth.domain.models import wsde_voting


class DummyAgent:
    def __init__(self, name, expertise=None):
        self.name = name
        self.expertise = expertise or []


class DummyTeam:
    def __init__(self, agents, primus=None):
        self.agents = agents
        self.voting_history = []
        self.logger = type(
            "L", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None}
        )()
        self._primus = primus

    def get_primus(self):
        return self._primus


def bind(team):
    team.vote_on_critical_decision = wsde_voting.vote_on_critical_decision.__get__(team)
    team._apply_majority_voting = wsde_voting._apply_majority_voting.__get__(team)
    team._apply_weighted_voting = wsde_voting._apply_weighted_voting.__get__(team)
    team._handle_tied_vote = wsde_voting._handle_tied_vote.__get__(team)
    team.build_consensus = wsde_voting.build_consensus.__get__(team)
    team._record_voting_history = lambda *a, **k: None
    return team


@pytest.mark.fast
def test_deterministic_voting_with_seed():
    """Voting with a fixed seed yields reproducible results.

    ReqID: WSDE-VOTE-DET-1"""
    agents = [DummyAgent("a1"), DummyAgent("a2")]
    team = bind(DummyTeam(agents))
    task = {"options": ["A", "B"], "voting_method": "majority"}
    rng = random.Random(42)
    res1 = team.vote_on_critical_decision(task, rng=rng)
    rng = random.Random(42)
    res2 = team.vote_on_critical_decision(task, rng=rng)
    assert res1["result"] == res2["result"]


@pytest.mark.fast
def test_weighted_voting_deterministic_with_seed():
    """Weighted voting with a fixed seed yields reproducible results.

    ReqID: WSDE-VOTE-DET-2"""
    a1 = DummyAgent("a1", ["frontend"])
    a2 = DummyAgent("a2", ["backend"])
    team = bind(DummyTeam([a1, a2]))
    task = {
        "options": ["frontend", "backend"],
        "voting_method": "weighted",
        "domain": "frontend",
    }
    rng1 = random.Random(7)
    res1 = team.vote_on_critical_decision(task, rng=rng1)
    rng2 = random.Random(7)
    res2 = team.vote_on_critical_decision(task, rng=rng2)
    assert res1["result"] == res2["result"]


@pytest.mark.fast
def test_weighted_voting_tie_is_fair():
    """Random tie-breaking is statistically fair across options.

    ReqID: WSDE-VOTE-FAIR-1"""
    a1, a2 = DummyAgent("a1"), DummyAgent("a2")
    team = bind(DummyTeam([a1, a2]))
    base_voting = {
        "options": ["A", "B"],
        "votes": {"a1": "A", "a2": "B"},
        "status": "pending",
    }
    counts = {"A": 0, "B": 0}
    for seed in range(50):
        rng = random.Random(seed)
        res = team._apply_weighted_voting(
            {"options": ["A", "B"]},
            copy.deepcopy(base_voting),
            "none",
            rng=rng,
        )
        counts[res["result"]] += 1
    assert abs(counts["A"] - counts["B"]) < 20


@pytest.mark.fast
def test_handle_tied_vote_produces_consensus_result():
    """Tied votes include a consensus attempt in the result payload.

    ReqID: WSDE-VOTE-TIE-1"""
    agents = [DummyAgent("a1"), DummyAgent("a2")]
    team = bind(DummyTeam(agents))
    voting_result = {
        "votes": {"a1": "A", "a2": "B"},
        "options": ["A", "B"],
        "status": "pending",
    }
    res = team._handle_tied_vote(
        {"id": "t", "options": ["A", "B"]},
        voting_result,
        {"A": 1, "B": 1},
        ["A", "B"],
        rng=random.Random(0),
    )
    assert res["status"] == "tied"
    assert res["result"]["tied"] is True
    assert "consensus_result" in res["result"]
