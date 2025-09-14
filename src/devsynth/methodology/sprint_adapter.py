"""Sprint ceremony helpers.

This module provides utilities for working with Agile sprint ceremonies
within DevSynth's EDRR methodology. The primary helper maps common
ceremonies such as planning, standups, review, or retrospective to their
corresponding EDRR :class:`~devsynth.methodology.base.Phase` values so
that sprint adapters can automatically link ceremonies with EDRR phases.
"""

from __future__ import annotations

from typing import Any

from .base import Phase

# Mapping of common sprint ceremonies to EDRR phases. Keys are stored in
# lower-case to allow case-insensitive lookups.
CEREMONY_PHASE_MAP: dict[str, Phase | None] = {
    # Sprint planning occurs before the Expand phase and prepares the scope
    # for the upcoming cycle.
    "planning": Phase.EXPAND,
    # Daily standups surface blockers and progress checks during the
    # Differentiate phase.
    "dailystandup": Phase.DIFFERENTIATE,
    "standup": Phase.DIFFERENTIATE,
    "review": Phase.REFINE,
    "retrospective": Phase.RETROSPECT,
}


def map_ceremony_to_phase(ceremony: str) -> Phase | None:
    """Return the EDRR phase for a sprint ceremony.

    Args:
        ceremony: Name of the Agile ceremony (e.g., ``"review"``).

    Returns:
        The corresponding :class:`Phase` value or ``None`` if the ceremony
        is not mapped to a specific phase.
    """

    return CEREMONY_PHASE_MAP.get(ceremony.lower())


def align_sprint_planning(planning_sections: dict[str, Any]) -> dict[Phase, Any]:
    """Align sprint planning data with EDRR phases.

    The provided ``planning_sections`` dictionary should have ceremony names
    (e.g., ``"planning"`` or ``"review"``) as keys. Any sections that map to a
    known EDRR phase are returned in a new dictionary keyed by that phase. This
    allows sprint tooling to quickly associate planning details with the phase
    of the upcoming EDRR cycle.

    Args:
        planning_sections: Mapping of ceremony names to planning data.

    Returns:
        Dictionary keyed by :class:`Phase` for ceremonies that have a known
        mapping. Ceremonies without a mapping are ignored.
    """

    aligned: dict[Phase, Any] = {}
    for ceremony, data in planning_sections.items():
        phase = map_ceremony_to_phase(ceremony)
        if phase is not None:
            aligned[phase] = data
    return aligned


def align_sprint_review(review_sections: dict[str, Any]) -> dict[Phase, Any]:
    """Align sprint review data with EDRR phases.

    This helper mirrors :func:`align_sprint_planning` but operates on review
    feedback from completed work. Sections keyed by ceremony name are
    translated to their corresponding EDRR phase, allowing downstream tooling
    to analyse review outcomes in phase-aware reports.

    Args:
        review_sections: Mapping of ceremony names to review data.

    Returns:
        Dictionary keyed by :class:`Phase` for ceremonies that have a known
        mapping. Ceremonies without a mapping are ignored.
    """

    aligned: dict[Phase, Any] = {}
    for ceremony, data in review_sections.items():
        phase = map_ceremony_to_phase(ceremony)
        if phase is not None:
            aligned[phase] = data
    return aligned
