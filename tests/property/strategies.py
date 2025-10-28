"""Hypothesis strategies for requirements and consensus outcomes.

These strategies are intentionally lightweight to ensure fast generation and
bounded execution time in CI. They are used by property tests to validate
structural invariants and time bounds for key workflows.

Style: follows project guidelines (PEP 8, type hints, clear docs).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from collections.abc import Mapping
from uuid import uuid4

from hypothesis import strategies as st

from devsynth.application.collaboration.dto import (
    AgentOpinionRecord,
    ConflictRecord,
    ConsensusOutcome,
    SynthesisArtifact,
)
from devsynth.application.memory.dto import MemoryRecord
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.domain.models.requirement import (
    Requirement,
    RequirementChange,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)


def _bounded_text(min_size: int = 1, max_size: int = 80) -> st.SearchStrategy[str]:
    return st.text(min_size=min_size, max_size=max_size).filter(
        lambda s: s.strip() != ""
    )


def _iso_timestamp_strategy() -> st.SearchStrategy[str]:
    return st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=[],
    ).map(lambda dt: dt.isoformat())


def _timestamp_input_strategy() -> st.SearchStrategy[Any]:
    """Return timestamp inputs accepted by DTOs (ISO string or datetime)."""

    datetime_values = st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=[],
    )
    return st.one_of(_iso_timestamp_strategy(), datetime_values)


def _json_value_strategy(max_leaves: int = 5) -> st.SearchStrategy[Any]:
    """Generate lightweight JSON-like structures for metadata fields."""

    primitives = st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-5, max_value=5),
        st.floats(
            min_value=-1.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        _bounded_text(1, 40),
    )

    return st.recursive(
        primitives,
        lambda children: st.one_of(
            st.lists(children, min_size=0, max_size=3),
            st.dictionaries(
                keys=_bounded_text(1, 12), values=children, min_size=0, max_size=3
            ),
        ),
        max_leaves=max_leaves,
    )


def _metadata_strategy() -> st.SearchStrategy[Mapping[str, Any]]:
    return st.dictionaries(
        keys=_bounded_text(1, 16),
        values=_json_value_strategy(),
        max_size=3,
    ).map(lambda data: dict(data))


def memory_item_strategy() -> st.SearchStrategy[MemoryItem]:
    identifiers = st.one_of(st.text(min_size=1, max_size=12), st.just(""))
    contents = _json_value_strategy(max_leaves=3)
    memory_types = st.sampled_from(list(MemoryType))
    metadata = _metadata_strategy()
    return st.builds(
        MemoryItem,
        id=identifiers,
        content=contents,
        memory_type=memory_types,
        metadata=metadata,
    )


def memory_record_strategy() -> st.SearchStrategy[MemoryRecord]:
    return st.builds(
        MemoryRecord,
        item=memory_item_strategy(),
        similarity=st.none()
        | st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
        source=st.none() | _bounded_text(1, 16),
        metadata=_metadata_strategy(),
    )


def _agent_opinion_record_strategy() -> st.SearchStrategy[AgentOpinionRecord]:
    return st.builds(
        AgentOpinionRecord,
        agent_id=_bounded_text(1, 12),
        opinion=_bounded_text(3, 60) | st.just(""),
        rationale=_bounded_text(3, 120) | st.just(""),
        timestamp=st.none() | _timestamp_input_strategy(),
        weight=st.none()
        | st.floats(
            min_value=0.5, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
        metadata=_metadata_strategy(),
    )


def _conflict_record_strategy() -> st.SearchStrategy[ConflictRecord]:
    return st.builds(
        ConflictRecord,
        conflict_id=_bounded_text(3, 24),
        task_id=_bounded_text(3, 24),
        agent_a=_bounded_text(1, 12),
        agent_b=_bounded_text(1, 12),
        opinion_a=_bounded_text(3, 80),
        opinion_b=_bounded_text(3, 80),
        rationale_a=_bounded_text(3, 120) | st.just(""),
        rationale_b=_bounded_text(3, 120) | st.just(""),
        severity_label=st.sampled_from(["high", "medium"]),
        severity_score=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
        metadata=_metadata_strategy(),
    )


def _synthesis_artifact_strategy() -> st.SearchStrategy[SynthesisArtifact]:
    key_points = st.lists(_bounded_text(3, 80), min_size=0, max_size=3).map(tuple)
    expertise_weights = st.dictionaries(
        keys=_bounded_text(1, 12),
        values=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
        max_size=3,
    )
    readability = st.fixed_dictionaries(
        {
            "flesch_reading_ease": st.floats(
                min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False
            ),
            "flesch_kincaid_grade": st.floats(
                min_value=0.0, max_value=12.0, allow_nan=False, allow_infinity=False
            ),
            "syllables_per_word": st.floats(
                min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False
            ),
            "words_per_sentence": st.floats(
                min_value=0.0, max_value=40.0, allow_nan=False, allow_infinity=False
            ),
        }
    )
    return st.builds(
        SynthesisArtifact,
        text=_bounded_text(3, 120) | st.just(""),
        key_points=key_points,
        expertise_weights=expertise_weights,
        conflict_resolution_method=st.sampled_from(
            ["weighted_expertise_synthesis", "consensus_blend"]
        ),
        readability_score=readability,
        metadata=_metadata_strategy(),
    )


def requirement_strategy() -> st.SearchStrategy[Requirement]:
    """Generate lightweight Requirement instances with valid enums and timestamps.

    - Timestamps are coherent: created_at <= updated_at <= now.
    - Titles/descriptions are short to keep tests fast.
    """
    titles = _bounded_text(3, 50)
    descriptions = _bounded_text(3, 200)
    status = st.sampled_from(list(RequirementStatus))
    priority = st.sampled_from(list(RequirementPriority))
    rtype = st.sampled_from(list(RequirementType))
    created_offset = st.integers(min_value=0, max_value=3600)
    updated_offset = st.integers(min_value=0, max_value=300)

    def _build(
        title: str,
        description: str,
        stt: RequirementStatus,
        pr: RequirementPriority,
        tp: RequirementType,
        c_off: int,
        u_off: int,
    ):
        now = datetime.now()
        created = now - timedelta(seconds=c_off + u_off)
        updated = created + timedelta(seconds=u_off)
        return Requirement(
            id=uuid4(),
            title=title,
            description=description,
            status=stt,
            priority=pr,
            type=tp,
            created_at=created,
            updated_at=updated,
            created_by="tester",
            dependencies=[],
            tags=["auto"],
            metadata={},
        )

    return st.builds(
        _build,
        titles,
        descriptions,
        status,
        priority,
        rtype,
        created_offset,
        updated_offset,
    )


def requirement_change_strategy() -> st.SearchStrategy[RequirementChange]:
    """Generate RequirementChange instances referencing generated Requirements."""
    req = requirement_strategy()

    def _build(change_type: str, prev: Requirement, new: Requirement):
        return RequirementChange(
            requirement_id=new.id,
            previous_state=prev,
            new_state=new,
            created_by="tester",
            reason="auto",
        )

    # Use a simple enumerated change type via names to avoid import of ChangeType in signature
    change_names = st.sampled_from(
        ["add", "remove", "modify"]
    )  # mapped by dataclass default if needed
    return st.builds(_build, change_names, req, req)


def consensus_outcome_strategy() -> st.SearchStrategy[ConsensusOutcome]:
    """Generate typed consensus outcomes for property-based testing."""

    methods = st.sampled_from(["conflict_resolution_synthesis", "majority_opinion"])
    agent_opinions = st.lists(
        _agent_opinion_record_strategy(), min_size=1, max_size=3
    ).map(tuple)
    conflict_records = st.lists(
        _conflict_record_strategy(), min_size=0, max_size=2
    ).map(tuple)
    synthesis = _synthesis_artifact_strategy()
    majority_choice = _bounded_text(3, 80)
    participants = st.lists(_bounded_text(1, 12), min_size=0, max_size=4).map(tuple)
    metadata = _metadata_strategy()
    rationale_text = st.none() | _bounded_text(5, 160)
    explanation_text = st.none() | _bounded_text(5, 200)

    def _build(
        consensus_id: str,
        task_id: str,
        method: str,
        opinions: tuple[AgentOpinionRecord, ...],
        conflicts: tuple[ConflictRecord, ...],
        synthesis_artifact: SynthesisArtifact,
        majority_opinion: str,
        timestamp: Any,
        participant_ids: tuple[str, ...],
        metadata_payload: Mapping[str, Any],
        achieved: bool,
        confidence: float,
        reported_conflicts: int,
        rationale_value: str | None,
        explanation_value: str | None,
    ) -> ConsensusOutcome:
        kwargs: dict[str, Any] = {
            "consensus_id": consensus_id,
            "task_id": task_id,
            "method": method,
            "agent_opinions": opinions,
            "conflicts": conflicts,
            "timestamp": timestamp,
            "participants": participant_ids,
            "metadata": metadata_payload,
            "achieved": achieved,
            "confidence": confidence,
            "conflicts_identified": reported_conflicts if conflicts else 0,
            "rationale": rationale_value,
            "stakeholder_explanation": explanation_value,
        }
        if method == "conflict_resolution_synthesis":
            kwargs["synthesis"] = synthesis_artifact
        else:
            kwargs["majority_opinion"] = majority_opinion
        return ConsensusOutcome(**kwargs)

    return st.builds(
        _build,
        st.uuids().map(str),
        st.uuids().map(str),
        methods,
        agent_opinions,
        conflict_records,
        synthesis,
        majority_choice,
        _timestamp_input_strategy(),
        participants,
        metadata,
        st.booleans(),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.integers(min_value=0, max_value=3),
        rationale_text,
        explanation_text,
    )


def consensus_outcome_payload_strategy() -> st.SearchStrategy[Any]:
    """Generate ConsensusOutcome instances or serialized dictionaries."""

    outcome_strategy = consensus_outcome_strategy()
    return st.one_of(
        outcome_strategy, outcome_strategy.map(lambda outcome: outcome.to_dict())
    )
