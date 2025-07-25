from devsynth.application.collaboration.wsde_team_consensus import ConsensusBuildingMixin

class DummyTeam(ConsensusBuildingMixin):
    def __init__(self):
        self.tracked_decisions = {}


def test_summarize_voting_result_tie():
    mixin = DummyTeam()
    result = {
        'status': 'completed',
        'result': {'tied': True, 'tied_options': ['A', 'B']},
        'tie_resolution': {'winner': 'A'},
    }
    summary = mixin.summarize_voting_result(result)
    assert 'tie between a, b' in summary.lower()
    assert 'favour of a' in summary.lower()


def test_summarize_voting_result_winner():
    mixin = DummyTeam()
    result = {'status': 'completed', 'result': 'B', 'vote_counts': {'B': 3}}
    summary = mixin.summarize_voting_result(result)
    assert summary == "Option 'B' selected with 3 votes."


def test_summarize_consensus_result_methods():
    mixin = DummyTeam()
    consensus = {'method': 'synthesis', 'synthesis': {'text': 'do x'}}
    assert 'synthesis consensus' in mixin.summarize_consensus_result(consensus).lower()
    consensus = {'majority_opinion': 'opt', 'method': 'vote'}
    assert 'majority opinion chosen' in mixin.summarize_consensus_result(consensus).lower()
