"""WSDE-aware EDRR phase coordination utilities.

This module bridges the WSDE team model with the EDRR methodology by
providing minimal helpers to progress through phases while ensuring role
assignments are updated and queued memory operations are flushed.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Optional, cast
from collections.abc import Callable

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
)
from devsynth.methodology.base import Phase


def _import_progress_roles() -> Callable[[Any, Phase, Any | None], dict[str, str]]:
    module = import_module("devsynth.domain.wsde." + "workflow")
    func = module.progress_roles
    return cast(Callable[[Any, Phase, Any | None], dict[str, str]], func)


class WSDEEDRRCoordinator:
    """Coordinate EDRR phases for a WSDE team.

    The coordinator keeps track of the current phase and delegates role
    assignment and memory synchronization to :func:`progress_roles` on each
    transition.  It stores the resulting assignments so callers can inspect
    how roles evolve across phases.
    """

    def __init__(self, team: Any, memory_manager: Any | None = None) -> None:
        """Initialize the coordinator.

        Args:
            team: WSDE team whose roles will be managed.
            memory_manager: Optional memory manager used for synchronization.
        """

        self.wsde_team = team
        self.memory_manager = memory_manager
        self.current_phase: Phase | None = None
        self.role_history: dict[str, dict[str, str]] = {}

    def progress_to_phase(self, phase: Phase) -> dict[str, str]:
        """Advance to ``phase`` and flush queued memory operations.

        Args:
            phase: The EDRR phase being entered.

        Returns:
            Mapping of agent identifiers to their assigned roles for the phase.
        """

        if self.memory_manager is not None:
            flush_memory_queue(self.memory_manager)
        progress_roles = _import_progress_roles()
        assignments = progress_roles(self.wsde_team, phase, self.memory_manager)
        if self.memory_manager is not None:
            flush_memory_queue(self.memory_manager)
        self.current_phase = phase
        self.role_history[phase.name] = assignments
        return assignments

    def get_role_assignments(self) -> dict[str, str]:
        """Return the most recent role assignments for the team."""

        if self.current_phase is None:
            return {}
        return self.role_history.get(self.current_phase.name, {})
