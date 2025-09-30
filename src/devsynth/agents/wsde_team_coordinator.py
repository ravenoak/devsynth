from __future__ import annotations

"""Agent coordinating WSDE team retrospective reviews."""

from collections.abc import Sequence
from typing import Any, Protocol, TypedDict, cast

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
)
from devsynth.application.sprint.retrospective import map_retrospective_to_summary
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class RetrospectiveNote(TypedDict, total=False):
    """Structured retrospective note provided by a WSDE team member."""

    positives: Sequence[str]
    improvements: Sequence[str]
    action_items: Sequence[str]


class RetrospectiveAggregation(TypedDict):
    """Aggregate of retrospective notes prior to summary conversion."""

    positives: list[str]
    improvements: list[str]
    action_items: list[str]


class RetrospectiveSummary(TypedDict):
    """Structured payload returned to persistence layers."""

    positives: list[str]
    improvements: list[str]
    action_items: list[str]
    sprint: int


class RetrospectiveSummaryPayload(RetrospectiveSummary, total=False):
    """Retrospective summary extended with optional telemetry."""

    research_persona_events: list[dict[str, Any]]


class SupportsRetrospectiveRecorder(Protocol):
    """Protocol for teams that can record retrospective summaries."""

    def record_retrospective(self, summary: RetrospectiveSummary) -> None:
        """Persist a retrospective summary."""


class WSDETeamCoordinatorAgent:
    """Coordinate WSDE team retrospective reviews."""

    def __init__(self, team: SupportsRetrospectiveRecorder | object) -> None:
        """Initialize the coordinator with a team object."""
        self._team = team

    def run_retrospective(
        self, notes: Sequence[RetrospectiveNote], sprint: int
    ) -> RetrospectiveSummaryPayload:
        """Aggregate notes and record a retrospective summary.

        Args:
            notes: List of retrospective notes from team members.
            sprint: Current sprint number.

        Returns:
            Summary dictionary produced by
            :func:`map_retrospective_to_summary`.
        """

        aggregated: RetrospectiveAggregation = {
            "positives": [],
            "improvements": [],
            "action_items": [],
        }
        for item in notes:
            aggregated["positives"].extend(item.get("positives", []))
            aggregated["improvements"].extend(item.get("improvements", []))
            aggregated["action_items"].extend(item.get("action_items", []))

        summary = cast(
            RetrospectiveSummaryPayload,
            map_retrospective_to_summary(aggregated, sprint),
        )

        if hasattr(self._team, "record_retrospective"):
            recorder = cast(SupportsRetrospectiveRecorder, self._team)
            recorder.record_retrospective(summary)
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
        drain = getattr(self._team, "drain_persona_events", None)
        if callable(drain):
            persona_events = drain()
            if persona_events:
                summary["research_persona_events"] = persona_events
        return summary


__all__ = [
    "RetrospectiveNote",
    "RetrospectiveSummary",
    "RetrospectiveSummaryPayload",
    "WSDETeamCoordinatorAgent",
]
