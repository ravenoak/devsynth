from __future__ import annotations

"""Sprint planning and retrospective CLI helpers."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from devsynth.application.sprint.planning import map_requirements_to_plan
from devsynth.application.sprint.retrospective import map_retrospective_to_summary
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def sprint_planning_cmd(requirements: str) -> Dict[str, Any]:
    """Generate a sprint plan from requirement analysis results.

    Args:
        requirements: Path to a JSON file or a JSON string containing
            requirement analysis results from the Expand phase.

    Returns:
        Dictionary describing the planned sprint scope.
    """

    data = _load_json(requirements)
    if data is None:
        return {}

    plan = map_requirements_to_plan(data)
    logger.info(
        "Generated sprint plan with %d items", len(plan.get("planned_scope", []))
    )
    return plan


def sprint_retrospective_cmd(retrospective: str, sprint: int) -> Dict[str, Any]:
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
        return {}

    summary = map_retrospective_to_summary(data, sprint)
    logger.info("Generated retrospective summary for sprint %d", sprint)
    return summary


def _load_json(source: str) -> Optional[Dict[str, Any]]:
    """Load JSON from a file path or raw string."""

    try:
        path = Path(source)
        if path.exists():
            return json.loads(path.read_text())
        return json.loads(source)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to load JSON: %s", exc)
        return None
