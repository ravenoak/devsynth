"""Hypothesis strategies for requirements and consensus outcomes.

These strategies are intentionally lightweight to ensure fast generation and
bounded execution time in CI. They are used by property tests to validate
structural invariants and time bounds for key workflows.

Style: follows .junie/guidelines.md (PEP 8, type hints, clear docs).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID, uuid4

from hypothesis import strategies as st

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


def requirement_strategy() -> st.SearchStrategy[Requirement]:
    """Generate lightweight Requirement instances with valid enums and timestamps.

    - Timestamps are coherent: created_at <= updated_at.
    - Titles/descriptions are short to keep tests fast.
    """
    titles = _bounded_text(3, 50)
    descriptions = _bounded_text(3, 200)
    status = st.sampled_from(list(RequirementStatus))
    priority = st.sampled_from(list(RequirementPriority))
    rtype = st.sampled_from(list(RequirementType))

    def _build(
        title: str,
        description: str,
        stt: RequirementStatus,
        pr: RequirementPriority,
        tp: RequirementType,
    ):
        created = datetime.now()
        updated = created + timedelta(
            seconds=st.integers(min_value=0, max_value=5).example()
        )
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

    return st.builds(_build, titles, descriptions, status, priority, rtype)


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


def consensus_outcome_strategy() -> st.SearchStrategy[Dict[str, Any]]:
    """Generate a simplified consensus outcome dict matching WSDE dialectical shape.

    Keys:
    - id (str), task_id (str), timestamp (datetime)
    - thesis (dict), antithesis (dict), synthesis (dict)
    - method == "dialectical_reasoning"
    """
    small_text = _bounded_text(3, 60)
    code_snip = st.one_of(
        small_text.map(lambda s: f"print('{s}')"), st.just("x = 1\nprint(x)")
    )

    thesis = st.fixed_dictionaries(
        {
            "content": small_text,
            "code": code_snip,
        }
    )

    antithesis = st.fixed_dictionaries(
        {
            "critiques": st.lists(small_text, min_size=1, max_size=3),
            "improvement_suggestions": st.lists(small_text, min_size=1, max_size=3),
            "alternative_approaches": st.lists(small_text, min_size=0, max_size=2),
        }
    )

    synthesis = st.fixed_dictionaries(
        {
            "integrated_critiques": st.lists(small_text, min_size=0, max_size=3),
            "improvements": st.lists(small_text, min_size=0, max_size=3),
            "content": small_text | st.just(""),
            "code": code_snip | st.just(""),
        }
    )

    return st.builds(
        lambda t, a, s: {
            "id": str(uuid4()),
            "task_id": str(uuid4()),
            "timestamp": datetime.now(),
            "thesis": t,
            "antithesis": a,
            "synthesis": s,
            "method": "dialectical_reasoning",
        },
        thesis,
        antithesis,
        synthesis,
    )
