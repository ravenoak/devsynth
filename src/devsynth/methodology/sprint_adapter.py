"""Sprint ceremony helpers.

This module provides utilities for working with Agile sprint ceremonies
within DevSynth's EDRR methodology. The primary helper maps common
ceremonies such as planning or review to their corresponding EDRR
:class:`~devsynth.methodology.base.Phase` values so that sprint adapters
can automatically link ceremonies with EDRR phases.
"""

from __future__ import annotations

from typing import Dict, Optional

from .base import Phase

# Mapping of common sprint ceremonies to EDRR phases. Keys are stored in
# lower-case to allow case-insensitive lookups.
CEREMONY_PHASE_MAP: Dict[str, Optional[Phase]] = {
    # Sprint planning occurs before the Expand phase and prepares the scope
    # for the upcoming cycle.
    "planning": Phase.EXPAND,
    "review": Phase.REFINE,
    "retrospective": Phase.RETROSPECT,
    # Daily standups track progress but are not tied to a specific phase.
    "dailystandup": None,
}


def map_ceremony_to_phase(ceremony: str) -> Optional[Phase]:
    """Return the EDRR phase for a sprint ceremony.

    Args:
        ceremony: Name of the Agile ceremony (e.g., ``"review"``).

    Returns:
        The corresponding :class:`Phase` value or ``None`` if the ceremony
        is not mapped to a specific phase.
    """

    return CEREMONY_PHASE_MAP.get(ceremony.lower())
