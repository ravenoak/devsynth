from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.dto import (
    AgentOpinionRecord,
    ConflictRecord,
    ConsensusOutcome,
    SynthesisArtifact,
)
from devsynth.application.collaboration.wsde_team_extended import CollaborativeWSDETeam
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam

pytestmark = [pytest.mark.medium]


@pytest.mark.medium
def test_build_consensus_enriches_metadata():
    team = CollaborativeWSDETeam(name="ConsensusTeam")
    team._track_decision = MagicMock()
    team.summarize_consensus_result = MagicMock(return_value="Concise summary")

    outcome = ConsensusOutcome(
        consensus_id="cons-1",
        task_id="task-123",
        method="majority",
        achieved=True,
        agent_opinions=(
            AgentOpinionRecord(agent_id="AgentA", rationale="Prefer Option A"),
            AgentOpinionRecord(agent_id="AgentB", rationale="Prefer Option B"),
        ),
        conflicts=(
            ConflictRecord(
                conflict_id="conf-1",
                agent_a="AgentA",
                agent_b="AgentB",
                opinion_a="favor",
                opinion_b="oppose",
            ),
        ),
        synthesis=SynthesisArtifact(text="Select Option A with safeguards"),
        majority_opinion="Option A",
        metadata={"existing": "value"},
    )

    class MemoryStub:
        def __init__(self):
            self.calls = []

        def store_with_edrr_phase(self, payload, *, memory_type, edrr_phase, metadata):
            self.calls.append((payload, memory_type, edrr_phase, metadata))
            return "memory-ref-1"

    team.memory_manager = MemoryStub()

    with patch.object(WSDETeam, "build_consensus", return_value=outcome):
        result = team.build_consensus({"id": "task-123", "type": "decision"})

    assert isinstance(result, ConsensusOutcome)
    assert result.metadata["summary"] == "Concise summary"
    assert result.metadata["memory_reference"] == "memory-ref-1"
    assert "consensus_decision" in result.metadata
    assert result.metadata["consensus_decision"]["id"] == "consensus_task-123"
    assert "AgentA" in result.metadata["agent_reasoning"]
    assert any("AgentA" in concern for concern in result.metadata["key_concerns"])
    assert result.metadata["documentation"]["summary"]

    stored_doc = team.decision_documentation["task-123"]
    assert isinstance(stored_doc, ConsensusOutcome)
    assert stored_doc.metadata["consensus_decision"]["id"] == "consensus_task-123"
    team._track_decision.assert_called_once()

    assert team.memory_manager.calls
    payload, memory_type, edrr_phase, metadata = team.memory_manager.calls[0]
    assert payload["consensus_id"] == "cons-1"
    assert memory_type is MemoryType.TEAM_STATE
    assert edrr_phase == "REFINE"
    assert metadata["task_id"] == "task-123"


@pytest.mark.medium
def test_mark_and_detail_decision_updates_tracking():
    team = CollaborativeWSDETeam(name="DecisionTeam")
    decision_id = "decision-1"
    team.decision_tracking[decision_id] = {
        "id": decision_id,
        "metadata": {
            "implementation_status": "pending",
            "criticality": "high",
            "type": "refinement",
            "decision_date": "2024-01-02T00:00:00",
        },
    }
    team.decision_documentation[decision_id] = {"summary": "Initial"}

    team.mark_decision_implemented(decision_id)
    assert (
        team.implemented_decisions[decision_id]["implementation_status"] == "completed"
    )
    assert (
        team.decision_tracking[decision_id]["metadata"]["implementation_status"]
        == "completed"
    )

    team.add_decision_implementation_details(
        decision_id,
        {"verification_status": "approved", "notes": "Verified by QA"},
    )

    tracked = team.get_tracked_decision(decision_id)
    assert tracked["metadata"]["verification_status"] == "approved"
    assert tracked["metadata"]["notes"] == "Verified by QA"
    assert team.has_decision_documentation(decision_id)

    window_start = "2024-01-01T00:00:00"
    window_end = "2024-12-31T00:00:00"
    results = team.query_decisions(
        criticality="high",
        type="refinement",
        date_range=(window_start, window_end),
    )

    assert any(dec["id"] == decision_id for dec in results)
