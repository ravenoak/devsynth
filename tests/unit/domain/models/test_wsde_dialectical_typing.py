"""Typing smoke tests for the dialectical dataclasses."""

from __future__ import annotations

from datetime import datetime
from collections.abc import Mapping

import pytest

from devsynth.domain.models.wsde_dialectical import (
    Critique,
    DialecticalSequence,
    DialecticalStep,
    ResolutionPlan,
)


@pytest.mark.fast
def test_dialectical_sequence_round_trip() -> None:
    """Sequences behave like mappings and support serialization."""

    critique = Critique.from_message(
        reviewer_id="critic",
        ordinal=0,
        message="Consider edge cases",
        domains=("code",),
    )
    plan = ResolutionPlan(
        plan_id="plan",
        timestamp=datetime.now(),
        integrated_critiques=(critique,),
        rejected_critiques=(),
        improvements=("Handle errors",),
        reasoning="Improve robustness",
        content="Improved solution",
    )
    step = DialecticalStep(
        step_id="step",
        timestamp=datetime.now(),
        task_id="task",
        thesis={"content": "original"},
        critiques=(critique,),
        resolution=plan,
        critic_id="critic",
    )
    sequence = DialecticalSequence(sequence_id="seq", steps=(step,))

    assert isinstance(sequence, Mapping)
    assert sequence["synthesis"]["content"] == "Improved solution"

    serialized = sequence.to_dict()
    assert serialized["steps"][0]["antithesis"]["critique_details"][0]["message"] == (
        "Consider edge cases"
    )

    reconstructed = DialecticalSequence.from_dict(serialized)
    assert reconstructed.latest() is not None
    assert reconstructed.latest().resolution.content == "Improved solution"
