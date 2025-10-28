"""Sprint planning adapter for EDRR integration.

This module provides helpers that translate requirement analysis results
from the Expand phase into a structured sprint plan. The sprint adapter
uses this mapping to align upcoming work with documented requirements.
"""

from __future__ import annotations

from typing import Any, Dict

# EDRR phase associated with sprint planning. Stored as a string to avoid
# circular import issues with the methodology package.
SPRINT_PLANNING_PHASE = "expand"


def map_requirements_to_plan(requirement_results: dict[str, Any]) -> dict[str, Any]:
    """Return sprint planning information derived from requirement analysis.

    Args:
        requirement_results: Results produced by the Expand phase's
            requirements analysis step.

    Returns:
        Dictionary containing planned scope, objectives and success criteria
        for the next sprint.
    """

    return {
        "planned_scope": requirement_results.get("recommended_scope", []),
        "objectives": requirement_results.get("objectives", []),
        "success_criteria": requirement_results.get("success_criteria", []),
    }
