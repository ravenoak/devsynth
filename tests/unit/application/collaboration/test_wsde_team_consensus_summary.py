import pytest

from devsynth.application.collaboration.dto import (
    AgentOpinionRecord,
    ConsensusOutcome,
    SynthesisArtifact,
)
from devsynth.application.collaboration.wsde_team_consensus import (
    ConsensusBuildingMixin,
)


class DummyTeam(ConsensusBuildingMixin):

    def __init__(self):
        self.tracked_decisions = {}


def test_summarize_voting_result_tie():
    mixin = DummyTeam()
    result = {
        "status": "completed",
        "result": {"tied": True, "tied_options": ["A", "B"]},
        "tie_resolution": {"winner": "A"},
    }
    summary = mixin.summarize_voting_result(result)
    assert "tie between a, b" in summary.lower()
    assert "favour of a" in summary.lower()


def test_summarize_voting_result_winner():
    mixin = DummyTeam()
    result = {"status": "completed", "result": "B", "vote_counts": {"B": 3}}
    summary = mixin.summarize_voting_result(result)
    assert summary == "Option 'B' selected with 3 votes."


def test_summarize_consensus_result_methods():
    mixin = DummyTeam()
    synthesis_outcome = ConsensusOutcome(
        consensus_id="c1",
        method="conflict_resolution_synthesis",
        synthesis=SynthesisArtifact(text="do x"),
        agent_opinions=(AgentOpinionRecord(agent_id="a", opinion="do x"),),
    )
    assert (
        "synthesis consensus"
        in mixin.summarize_consensus_result(synthesis_outcome).lower()
    )
    consensus = ConsensusOutcome(
        consensus_id="c2",
        method="majority_opinion",
        majority_opinion="opt",
        agent_opinions=(AgentOpinionRecord(agent_id="a", opinion="opt"),),
    )
    assert (
        "majority opinion chosen" in mixin.summarize_consensus_result(consensus).lower()
    )
