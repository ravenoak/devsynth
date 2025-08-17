from __future__ import annotations

"""Agent coordinating WSDE team retrospective reviews."""

from typing import Any, Dict, List

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
)
from devsynth.application.sprint.retrospective import map_retrospective_to_summary
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class WSDETeamCoordinatorAgent:
    """Coordinate WSDE team retrospective reviews."""

    def __init__(self, team: Any) -> None:
        """Initialize the coordinator with a team object."""
        self._team = team

    def run_retrospective(
        self, notes: List[Dict[str, Any]], sprint: int
    ) -> Dict[str, Any]:
        """Aggregate notes and record a retrospective summary.

        Args:
            notes: List of retrospective notes from team members.
            sprint: Current sprint number.

        Returns:
            Summary dictionary produced by
            :func:`map_retrospective_to_summary`.
        """

        aggregated: Dict[str, Any] = {
            "positives": [],
            "improvements": [],
            "action_items": [],
        }
        for item in notes:
            aggregated["positives"].extend(item.get("positives", []))
            aggregated["improvements"].extend(item.get("improvements", []))
            aggregated["action_items"].extend(item.get("action_items", []))

        summary = map_retrospective_to_summary(aggregated, sprint)

        if hasattr(self._team, "record_retrospective"):
            self._team.record_retrospective(summary)
        else:  # pragma: no cover - defensive
            logger.debug("Team object lacks 'record_retrospective' method")

        memory_manager = getattr(self._team, "memory_manager", None)
        if memory_manager:
            try:
                flush_memory_queue(memory_manager)
            except Exception:  # pragma: no cover - defensive
                logger.debug(
                    "Memory synchronization failed during retrospective",
                    exc_info=True,
                )
        return summary
