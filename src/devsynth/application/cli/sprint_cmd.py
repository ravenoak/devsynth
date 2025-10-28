from __future__ import annotations

"""Sprint planning and retrospective CLI helpers."""

import json
from pathlib import Path
from typing import Optional, TypedDict, Union, cast
from collections.abc import Sequence

from devsynth.application.sprint.planning import map_requirements_to_plan
from devsynth.application.sprint.retrospective import map_retrospective_to_summary
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


JSONPrimitive = Union[str, int, float, bool, None]


class JSONMapping(TypedDict, total=False):
    """Minimal recursive JSON mapping structure used by sprint helpers."""

    # TypedDict cannot express recursive types directly; values fall back to
    # ``JSONValue`` via ``JSONLike`` alias defined below.


JSONValue = Union[JSONPrimitive, Sequence["JSONValue"], JSONMapping]


class SprintPlan(TypedDict):
    """Structured sprint planning output."""

    planned_scope: Sequence[JSONValue]
    objectives: Sequence[JSONValue]
    success_criteria: Sequence[JSONValue]


class SprintRetrospectiveSummary(TypedDict):
    """Structured summary returned by :func:`sprint_retrospective_cmd`."""

    positives: Sequence[JSONValue]
    improvements: Sequence[JSONValue]
    action_items: Sequence[JSONValue]
    sprint: int


def _empty_plan() -> SprintPlan:
    return {
        "planned_scope": [],
        "objectives": [],
        "success_criteria": [],
    }


def _empty_summary(sprint: int) -> SprintRetrospectiveSummary:
    return {
        "positives": [],
        "improvements": [],
        "action_items": [],
        "sprint": sprint,
    }


def sprint_planning_cmd(requirements: str) -> SprintPlan:
    """Generate a sprint plan from requirement analysis results.

    Args:
        requirements: Path to a JSON file or a JSON string containing
            requirement analysis results from the Expand phase.

    Returns:
        Dictionary describing the planned sprint scope.
    """

    data = _load_json(requirements)
    if data is None:
        return _empty_plan()

    plan = map_requirements_to_plan(data)
    logger.info(
        "Generated sprint plan with %d items", len(plan.get("planned_scope", []))
    )
    return SprintPlan(
        planned_scope=plan.get("planned_scope", []),
        objectives=plan.get("objectives", []),
        success_criteria=plan.get("success_criteria", []),
    )


def sprint_retrospective_cmd(
    retrospective: str, sprint: int
) -> SprintRetrospectiveSummary:
    """Summarize retrospective information for a sprint.

    Args:
        retrospective: Path to a JSON file or a JSON string containing
            retrospective notes from the Retrospect phase.
        sprint: Current sprint number.

    Returns:
        Summary dictionary with positives, improvements and action items.
    """

    data = _load_json(retrospective)
    if data is None:
        return _empty_summary(sprint)

    summary = map_retrospective_to_summary(data, sprint)
    logger.info("Generated retrospective summary for sprint %d", sprint)
    return SprintRetrospectiveSummary(
        positives=summary.get("positives", []),
        improvements=summary.get("improvements", []),
        action_items=summary.get("action_items", []),
        sprint=summary.get("sprint", sprint),
    )


def _load_json(source: str) -> JSONMapping | None:
    """Load JSON from a file path or raw string."""

    try:
        path = Path(source)
        if path.exists():
            return cast(JSONMapping, json.loads(path.read_text()))
        return cast(JSONMapping, json.loads(source))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load JSON: %s", exc)
        return None
