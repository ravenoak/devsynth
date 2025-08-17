"""WSDE-aware EDRR phase coordination utilities.

This module bridges the WSDE team model with the EDRR methodology by
providing minimal helpers to progress through phases while ensuring role
assignments are updated and queued memory operations are flushed.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.domain.wsde.workflow import progress_roles
from devsynth.methodology.base import Phase


class WSDEEDRRCoordinator:
    """Coordinate EDRR phases for a WSDE team.

    The coordinator keeps track of the current phase and delegates role
    assignment and memory synchronization to :func:`progress_roles` on each
    transition.  It stores the resulting assignments so callers can inspect
    how roles evolve across phases.
    """

    def __init__(self, team: WSDETeam, memory_manager: Optional[Any] = None) -> None:
        """Initialize the coordinator.

        Args:
            team: WSDE team whose roles will be managed.
            memory_manager: Optional memory manager used for synchronization.
        """

        self.wsde_team = team
        self.memory_manager = memory_manager
        self.current_phase: Optional[Phase] = None
        self.role_history: Dict[str, Dict[str, str]] = {}

    def progress_to_phase(self, phase: Phase) -> Dict[str, str]:
        """Advance to ``phase`` and flush queued memory operations.

        Args:
            phase: The EDRR phase being entered.

        Returns:
            Mapping of agent identifiers to their assigned roles for the phase.
        """

        assignments = progress_roles(self.wsde_team, phase, self.memory_manager)
        self.current_phase = phase
        self.role_history[phase.name] = assignments
        return assignments

    def get_role_assignments(self) -> Dict[str, str]:
        """Return the most recent role assignments for the team."""

        if self.current_phase is None:
            return {}
        return self.role_history.get(self.current_phase.name, {})
