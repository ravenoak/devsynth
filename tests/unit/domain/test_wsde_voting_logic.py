import types
import random
import devsynth.application.edrr.edrr_phase_transitions as _ph

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
        self.logger = types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None)
        self._primus = primus

    def get_primus(self):
        return self._primus


def bind(team):
    team.vote_on_critical_decision = wsde_voting.vote_on_critical_decision.__get__(team)
    team._apply_majority_voting = wsde_voting._apply_majority_voting.__get__(team)
    team._apply_weighted_voting = wsde_voting._apply_weighted_voting.__get__(team)
    team._handle_tied_vote = wsde_voting._handle_tied_vote.__get__(team)
    team._record_voting_history = lambda *a, **k: None
    return team


def test_majority_voting_simple(monkeypatch):
    agents = [DummyAgent("a1", ["a"]), DummyAgent("a2", ["b"]), DummyAgent("a3", ["a"])]
    team = bind(DummyTeam(agents, primus=agents[0]))
    monkeypatch.setattr(random, "choice", lambda x: x[0])
    task = {"options": ["option_a", "option_b"], "voting_method": "majority"}
    result = team.vote_on_critical_decision(task)
    assert result["status"] == "completed"
    assert result["result"] == "option_a"


def test_handle_tied_vote_primus_breaks(monkeypatch):
    agents = [DummyAgent("primus", ["x"]), DummyAgent("other", ["y"])]
    team = bind(DummyTeam(agents, primus=agents[0]))
    voting_result = {
        "votes": {"primus": "A", "other": "B"},
        "options": ["A", "B"],
        "status": "pending",
    }
    vote_counts = {"A": 1, "B": 1}
    res = team._handle_tied_vote({"options": ["A", "B"]}, voting_result, vote_counts, ["A", "B"])
    assert res["result"] == "A"
    assert res["status"] == "completed"


def test_weighted_voting_tie_primus_resolution(monkeypatch):
    a1 = DummyAgent("p", ["frontend"])
    a2 = DummyAgent("s", ["frontend"])
    team = bind(DummyTeam([a1, a2], primus=a1))
    monkeypatch.setattr(random, "choice", lambda opts: opts[0])
    task = {
        "options": ["frontend", "backend"],
        "voting_method": "weighted",
        "domain": "frontend",
    }
    # Force votes to create a tie
    voting_result = {
        "options": ["frontend", "backend"],
        "votes": {"p": "frontend", "s": "backend"},
        "method": "weighted",
        "status": "pending",
    }
    vote_counts = {"frontend": 1, "backend": 1}
    res = team._handle_tied_vote(task, voting_result, vote_counts, ["frontend", "backend"])
    assert res["result"] == "frontend"


def test_vote_on_critical_decision_majority(monkeypatch):
    agents = [DummyAgent("a1", ["opt1"]), DummyAgent("a2", ["opt1"]), DummyAgent("a3", ["opt2"])]
    team = bind(DummyTeam(agents, primus=agents[0]))
    monkeypatch.setattr(random, "choice", lambda opts: opts[0])
    task = {"id": "t", "options": ["opt1", "opt2"], "voting_method": "majority"}
    result = team.vote_on_critical_decision(task)
    assert result["result"] == "opt1"
    assert result["status"] == "completed"


def test_vote_on_critical_decision_weighted(monkeypatch):
    a1 = DummyAgent("a1", ["frontend"])
    a2 = DummyAgent("a2", ["backend"])
    team = bind(DummyTeam([a1, a2], primus=a1))
    monkeypatch.setattr(random, "choice", lambda opts: opts[0])
    task = {
        "id": "t2",
        "options": ["frontend", "backend"],
        "voting_method": "weighted",
        "domain": "frontend",
    }
    result = team.vote_on_critical_decision(task)
    assert result["status"] == "completed"
    assert result["result"] == "frontend"


def test_apply_majority_voting_no_tie(monkeypatch):
    agents = [DummyAgent('a1'), DummyAgent('a2')]
    team = bind(DummyTeam(agents, primus=agents[0]))
    voting_result = {
        'options': ['X', 'Y'],
        'votes': {'a1': 'X', 'a2': 'X'},
        'vote_counts': {'X': 2, 'Y': 0},
        'status': 'pending'
    }
    res = team._apply_majority_voting({}, voting_result)
    assert res['result'] == 'X'
    assert res['status'] == 'completed'


def test_consensus_vote(monkeypatch):
    agents = [DummyAgent('a1', ['front']), DummyAgent('a2', ['front'])]
    team = bind(DummyTeam(agents, primus=agents[0]))
    monkeypatch.setattr(random, 'choice', lambda opts: opts[0])
    task = {'options': ['front', 'back']}
    res = wsde_voting.consensus_vote(team, task)
    assert res['decision'] in {'front', 'back'}

def test_build_consensus_simple(monkeypatch):
    agents = [DummyAgent('a1', ['front']), DummyAgent('a2', ['back'])]
    team = bind(DummyTeam(agents, primus=agents[0]))
    monkeypatch.setattr(random, 'choice', lambda opts: opts[0])
    task = {
        'options': ['front', 'back'],
        'domain': 'front',
        'max_rounds': 1,
    }
    res = wsde_voting.build_consensus(team, task)
    assert 'status' in res

def test_build_consensus_rounds(monkeypatch):
    agents = [DummyAgent('a1', ['x']), DummyAgent('a2', ['y']), DummyAgent('a3', ['x'])]
    team = bind(DummyTeam(agents, primus=agents[0]))
    monkeypatch.setattr(random, 'choice', lambda opts: opts[0])
    task = {
        'options': ['x', 'y'],
        'domain': 'x',
        'consensus_threshold': 0.6,
        'max_rounds': 2,
    }
    res = wsde_voting.build_consensus(team, task)
    assert 'status' in res

def test_apply_weighted_voting_primus_tie(monkeypatch):
    p = DummyAgent('p', ['front'])
    o = DummyAgent('o', ['front'])
    team = bind(DummyTeam([p, o], primus=p))
    monkeypatch.setattr(random, 'choice', lambda opts: opts[0])
    voting_result = {
        'options': ['front', 'back'],
        'votes': {'p': 'front', 'o': 'back'},
        'status': 'pending'
    }
    res = team._apply_weighted_voting({'options': ['front', 'back']}, voting_result, 'front')
    assert res['result'] == 'front'


def test_apply_weighted_voting_random(monkeypatch):
    a1 = DummyAgent('a1')
    a2 = DummyAgent('a2')
    team = bind(DummyTeam([a1, a2], primus=None))
    monkeypatch.setattr(random, 'choice', lambda opts: opts[-1])
    voting_result = {
        'options': ['A', 'B'],
        'votes': {'a1': 'A', 'a2': 'B'},
        'status': 'pending'
    }
    res = team._apply_weighted_voting({'options': ['A', 'B']}, voting_result, 'none')
    assert res['status'] == 'completed'
    assert res['result'] in {'A', 'B'}
