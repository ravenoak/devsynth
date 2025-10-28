"""Property-based tests for requirement consensus utilities.

Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
"""

import time
from typing import Any
from collections.abc import Mapping

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from devsynth.application.collaboration.dto import (
    AgentOpinionRecord,
    ConflictRecord,
    ConsensusOutcome,
    SynthesisArtifact,
)
from devsynth.domain.models.requirement import Requirement
from devsynth.domain.models.wsde_dialectical import (
    DialecticalSequence,
    apply_dialectical_reasoning,
)
from tests.helpers.dummies import _DummyTeam

from .strategies import (
    consensus_outcome_payload_strategy,
    requirement_strategy,
)


@pytest.mark.property
@pytest.mark.medium
@settings(deadline=300)  # 300ms per example to keep CI stable
@given(req=requirement_strategy())
def test_requirement_update_timestamp_is_monotonic(req: Requirement):
    """Updating a requirement should not regress its timestamp.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """
    before = req.updated_at
    req.update(title=req.title + "!")
    after = req.updated_at

    assert after >= before, "updated_at should be monotonically non-decreasing"


class _DummyCritic:
    name = "critic"

    def critique(self, *_args, **_kwargs):  # not used by current implementation
        return {"notes": "ok"}


@pytest.mark.property
@pytest.mark.fast
@settings(max_examples=10, deadline=500)
@given(thesis_content=st.text(min_size=5, max_size=80))
@pytest.mark.no_network
def test_dialectical_reasoning_returns_expected_shape_quickly(thesis_content: str):
    """dialectical reasoning yields expected keys quickly.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """
    team = _DummyTeam()
    task: dict[str, Any] = {
        "solution": {"content": thesis_content, "code": "x=1\nprint(x)"}
    }
    critic = _DummyCritic()

    start = time.perf_counter()
    result = apply_dialectical_reasoning(team, task, critic, memory_integration=None)
    elapsed = time.perf_counter() - start

    # Shape assertions
    assert isinstance(result, DialecticalSequence)
    payload = result.to_dict()
    for key in (
        "id",
        "timestamp",
        "task_id",
        "thesis",
        "antithesis",
        "synthesis",
        "method",
    ):
        assert key in payload, f"missing key: {key}"
    assert payload["method"] == "dialectical_reasoning"

    # Time bound: keep very generous to remain stable across CI runners
    assert (
        elapsed < 0.5
    ), f"dialectical reasoning should be fast for simple input, took {elapsed:.3f}s"


@pytest.mark.property
@pytest.mark.medium
@settings(max_examples=15, deadline=400)
@given(payload=consensus_outcome_payload_strategy())
def test_consensus_outcome_serialization_preserves_invariants(payload: Any) -> None:
    """ConsensusOutcome payloads round-trip with normalized ordering and metadata.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

    if isinstance(payload, ConsensusOutcome):
        outcome = payload
        serialized = payload.to_dict()
    else:
        assert isinstance(payload, Mapping)
        serialized = dict(payload)
        outcome = ConsensusOutcome.from_dict(serialized)

    assert isinstance(outcome, ConsensusOutcome)
    assert serialized["dto_type"] == "ConsensusOutcome"
    assert ConsensusOutcome.from_dict(serialized) == outcome
    assert ConsensusOutcome.from_dict(outcome.to_dict()) == outcome

    # Timestamps are normalized to ISO strings when provided.
    if outcome.timestamp is not None:
        assert isinstance(outcome.timestamp, str)
        assert "T" in outcome.timestamp

    # Agent opinions are converted to deterministic ordering.
    assert all(
        isinstance(opinion, AgentOpinionRecord) for opinion in outcome.agent_opinions
    )
    expected_opinion_order = tuple(
        sorted(
            outcome.agent_opinions,
            key=lambda opinion: ((opinion.agent_id or ""), opinion.timestamp or ""),
        )
    )
    assert outcome.agent_opinions == expected_opinion_order

    # Participants default to unique agent IDs in order of normalized opinions.
    expected_participants = tuple(
        dict.fromkeys(
            record.agent_id for record in outcome.agent_opinions if record.agent_id
        )
    )
    assert outcome.participants == expected_participants

    # Conflicts are sorted deterministically and counted accurately.
    assert all(isinstance(conflict, ConflictRecord) for conflict in outcome.conflicts)
    expected_conflict_order = tuple(
        sorted(
            outcome.conflicts,
            key=lambda conflict: ((conflict.conflict_id or ""), conflict.agent_a or ""),
        )
    )
    assert outcome.conflicts == expected_conflict_order
    assert outcome.conflicts_identified == len(outcome.conflicts)

    # Metadata is normalized to dictionaries with ordered keys.
    assert isinstance(outcome.metadata, dict)
    if outcome.metadata:
        assert list(outcome.metadata.keys()) == sorted(outcome.metadata.keys())
        for value in outcome.metadata.values():
            if isinstance(value, dict):
                assert list(value.keys()) == sorted(value.keys())

    # Method-specific invariants.
    assert outcome.method in {"conflict_resolution_synthesis", "majority_opinion"}
    if outcome.method == "conflict_resolution_synthesis":
        assert isinstance(outcome.synthesis, SynthesisArtifact)
        assert outcome.majority_opinion is None
    else:
        assert outcome.synthesis is None
        assert outcome.majority_opinion is None or isinstance(
            outcome.majority_opinion, str
        )

    # Serialized payload preserves ordering guarantees.
    round_trip = outcome.to_dict()
    serialized_opinion_ids = [
        record["agent_id"] for record in round_trip["agent_opinions"]
    ]
    assert serialized_opinion_ids == [
        record.agent_id for record in outcome.agent_opinions
    ]
    serialized_conflict_ids = [
        record["conflict_id"] for record in round_trip["conflicts"]
    ]
    assert serialized_conflict_ids == [
        record.conflict_id for record in outcome.conflicts
    ]
