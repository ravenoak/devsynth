"""Methodology utilities for EDRR coordination.

This module provides lightweight helpers to automate retrospective reviews
using sprint integration helpers.
"""

from __future__ import annotations

from typing import Any

from devsynth.application.sprint.retrospective import map_retrospective_to_summary
from devsynth.domain.models.memory import MemoryType
from devsynth.exceptions import ConsensusError
from devsynth.logger import DevSynthLogger, log_consensus_failure

logger = DevSynthLogger(__name__)


class EDRRCoordinator:
    """Coordinate simple EDRR routines for methodology adapters."""

    def __init__(self, memory_manager: Any | None = None) -> None:
        """Initialize the coordinator.

        Args:
            memory_manager: Optional memory manager used for synchronization.
        """

        self.memory_manager = memory_manager

    def _store_phase_result(
        self, data: dict[str, Any], memory_type: MemoryType, phase: str
    ) -> None:
        """Persist phase data with the configured memory manager.

        Any exceptions raised by the memory layer are swallowed to keep
        coordination lightweight.
        """

        if self.memory_manager is None:
            return
        try:  # pragma: no cover - defensive: memory layer may be unreliable
            self.memory_manager.store_with_edrr_phase(data, memory_type, phase)
            self.memory_manager.flush_updates()
        except Exception:
            pass

    def record_expand_results(self, results: dict[str, Any]) -> dict[str, Any]:
        """Record results from the Expand phase."""

        self._store_phase_result(results, MemoryType.KNOWLEDGE, "EXPAND")
        return results

    def record_differentiate_results(self, results: dict[str, Any]) -> dict[str, Any]:
        """Record results from the Differentiate phase."""

        self._store_phase_result(results, MemoryType.KNOWLEDGE, "DIFFERENTIATE")
        return results

    def record_refine_results(self, results: dict[str, Any]) -> dict[str, Any]:
        """Record results from the Refine phase."""

        self._store_phase_result(results, MemoryType.KNOWLEDGE, "REFINE")
        return results

    def record_consensus_failure(self, error: ConsensusError) -> None:
        """Log a consensus failure for later analysis."""

        log_consensus_failure(logger, error)

    def automate_retrospective_review(
        self, retrospective: dict[str, Any], sprint: int
    ) -> dict[str, Any]:
        """Return a standardized retrospective summary.

        Args:
            retrospective: Raw results from the Retrospect phase.
            sprint: Current sprint number.

        Returns:
            Dictionary summarizing positives, improvements and action items.
        """

        summary = map_retrospective_to_summary(retrospective, sprint)
        if not summary:
            return {}

        summary["positive_count"] = len(summary.get("positives", []))
        summary["improvement_count"] = len(summary.get("improvements", []))
        summary["action_item_count"] = len(summary.get("action_items", []))

        self._store_phase_result(summary, MemoryType.PEER_REVIEW, "RETROSPECT")
        return summary
