"""Methodology utilities for EDRR coordination.

This module provides lightweight helpers to automate retrospective reviews
using sprint integration helpers.
"""

from __future__ import annotations

from typing import Any, Dict

from devsynth.application.sprint.retrospective import map_retrospective_to_summary


class EDRRCoordinator:
    """Coordinate simple EDRR routines for methodology adapters."""

    def automate_retrospective_review(
        self, retrospective: Dict[str, Any], sprint: int
    ) -> Dict[str, Any]:
        """Return a standardized retrospective summary.

        Args:
            retrospective: Raw results from the Retrospect phase.
            sprint: Current sprint number.

        Returns:
            Dictionary summarizing positives, improvements and action items.
        """

        return map_retrospective_to_summary(retrospective, sprint)
