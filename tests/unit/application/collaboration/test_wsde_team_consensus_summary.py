import pytest

from devsynth.application.collaboration.dto import (

pytestmark = [pytest.mark.fast]
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


def test_consensus_outcome_round_trip_orders_conflicts() -> None:
    mixin = DummyTeam()
    payload = {
        "dto_type": "ConsensusOutcome",
        "consensus_id": "c3",
        "task_id": "t1",
        "method": "conflict_resolution_synthesis",
        "agent_opinions": [
            {
                "dto_type": "AgentOpinionRecord",
                "agent_id": "beta",
                "opinion": "no",
                "timestamp": "2025-01-02T00:00:00",
            },
            {
                "dto_type": "AgentOpinionRecord",
                "agent_id": "alpha",
                "opinion": "yes",
                "timestamp": "2025-01-01T00:00:00",
            },
        ],
        "conflicts": [
            {
                "dto_type": "ConflictRecord",
                "conflict_id": "c2",
                "task_id": "t1",
                "agent_a": "beta",
                "agent_b": "alpha",
                "opinion_a": "no",
                "opinion_b": "yes",
            },
            {
                "dto_type": "ConflictRecord",
                "conflict_id": "c1",
                "task_id": "t1",
                "agent_a": "alpha",
                "agent_b": "beta",
                "opinion_a": "yes",
                "opinion_b": "no",
            },
        ],
        "conflicts_identified": 0,
        "synthesis": {
            "dto_type": "SynthesisArtifact",
            "text": "resolved",
            "key_points": ["compromise"],
            "expertise_weights": {"alpha": 0.6, "beta": 0.4},
            "readability_score": {"flesch_reading_ease": 65.0},
        },
        "timestamp": "2025-01-01T00:00:00",
    }

    outcome = ConsensusOutcome.from_dict(payload)
    assert [record.agent_id for record in outcome.agent_opinions] == [
        "alpha",
        "beta",
    ]
    assert [record.conflict_id for record in outcome.conflicts] == ["c1", "c2"]
    assert outcome.conflicts_identified == 2

    serialized = outcome.to_dict()
    assert serialized["conflicts"][0]["conflict_id"] == "c1"
    assert serialized["synthesis"]["dto_type"] == "SynthesisArtifact"

    summary = mixin.summarize_consensus_result(outcome)
    assert "resolved 2 conflicts" in summary.lower()
