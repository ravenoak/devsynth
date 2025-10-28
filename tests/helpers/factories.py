"""Factories for constructing domain model instances in tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from collections.abc import Mapping, Sequence
from uuid import uuid4

from devsynth.domain.models.wsde_dialectical import (
    Critique,
    DialecticalSequence,
    DialecticalStep,
    ResolutionPlan,
)
from devsynth.domain.models.wsde_dialectical_types import DialecticalTask


@dataclass(slots=True)
class DialecticalTaskFactory:
    """Factory helpers for creating :class:`DialecticalTask` instances."""

    default_solution: Mapping[str, Any] | None = None

    def build(self, **overrides: Any) -> DialecticalTask:
        payload: dict[str, Any] = {
            "id": overrides.pop("task_id", str(uuid4())),
            "solution": overrides.pop(
                "solution",
                self.default_solution or {"content": "Example", "code": "print('hi')"},
            ),
        }
        payload.update(overrides)
        return DialecticalTask.from_mapping(payload)


def build_resolution_plan(
    *,
    integrated_critiques: Sequence[Critique] | None = None,
    rejected_critiques: Sequence[Critique] | None = None,
    improvements: Sequence[str] | None = None,
    reasoning: str = "",
    content: str | None = None,
    code: str | None = None,
) -> ResolutionPlan:
    """Create a :class:`ResolutionPlan` with deterministic defaults."""

    now = datetime.now()
    return ResolutionPlan(
        plan_id=str(uuid4()),
        timestamp=now,
        integrated_critiques=tuple(integrated_critiques or ()),
        rejected_critiques=tuple(rejected_critiques or ()),
        improvements=tuple(improvements or ()),
        reasoning=reasoning,
        content=content,
        code=code,
    )


def build_dialectical_sequence(
    *,
    status: str = "completed",
    thesis: Mapping[str, Any] | None = None,
    resolution: ResolutionPlan | None = None,
    critiques: Sequence[Critique] | None = None,
    method: str = "dialectical_reasoning",
    critic_id: str = "critic",
    task_id: str | None = None,
) -> DialecticalSequence:
    """Assemble a :class:`DialecticalSequence` for testing flows."""

    now = datetime.now()
    thesis_payload = dict(thesis or {"content": "Initial thesis"})
    plan = resolution or build_resolution_plan(reasoning="Auto-generated plan")
    step = DialecticalStep(
        step_id=str(uuid4()),
        timestamp=now,
        task_id=task_id or str(uuid4()),
        thesis=thesis_payload,
        critiques=tuple(critiques or ()),
        resolution=plan,
        method=method,
        critic_id=critic_id,
        antithesis_id=str(uuid4()),
        antithesis_generated_at=now,
    )
    return DialecticalSequence(
        sequence_id=str(uuid4()),
        steps=(step,),
        status=status,
    )
