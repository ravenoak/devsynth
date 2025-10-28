"""Sprint retrospective adapter for EDRR integration.

Utilities in this module convert raw retrospective results from the
Retrospect phase into summaries suitable for sprint metrics.
"""

from __future__ import annotations

from typing import Any, Dict

# EDRR phase associated with sprint retrospectives, stored as a string to
# keep imports lightweight.
SPRINT_RETROSPECTIVE_PHASE = "retrospect"


def map_retrospective_to_summary(
    retrospective: dict[str, Any], sprint: int
) -> dict[str, Any]:
    """Return summarized retrospective information.

    Args:
        retrospective: Results produced by the Retrospect phase.
        sprint: Current sprint number.

    Returns:
        Summary dictionary containing positives, improvements and action
        items. If no retrospective data is provided an empty dict is
        returned.
    """

    if not retrospective:
        return {}

    return {
        "positives": retrospective.get("positives", []),
        "improvements": retrospective.get("improvements", []),
        "action_items": retrospective.get("action_items", []),
        "sprint": sprint,
    }
