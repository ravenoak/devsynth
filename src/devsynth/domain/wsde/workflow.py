"""WSDE workflow helpers."""

from __future__ import annotations

from typing import Dict, Optional

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
)
from devsynth.domain.models.wsde_core import WSDETeam
from devsynth.methodology.base import Phase


def progress_roles(
    team: WSDETeam, phase: Phase, memory_manager: object | None = None
) -> dict[str, str]:
    """Assign roles for an EDRR phase and flush pending memory updates.

    Args:
        team: The team whose roles should be reassigned.
        phase: The EDRR phase being entered.
        memory_manager: Optional memory manager coordinating sync operations.

    Returns:
        Mapping of agent identifiers to their assigned roles.
    """

    if hasattr(team, "assign_roles_for_phase"):
        try:
            team.assign_roles_for_phase(phase)
        except TypeError:
            team.assign_roles_for_phase(phase, {})

    assignments: dict[str, str] = {}
    for role, agent in team.roles.items():
        if agent is None:
            continue
        agent.current_role = role.capitalize()
        agent_id = getattr(agent, "id", None) or getattr(agent, "name", None)
        assignments[agent_id] = agent.current_role

    if memory_manager is not None:
        flush_memory_queue(memory_manager)

    return assignments
