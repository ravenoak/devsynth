from __future__ import annotations

"""Core WSDE models.

This module defines the minimal WSDE dataclass and a lightweight WSDETeam
implementation that only provides essential team-management behaviour.  More
advanced capabilities such as communication helpers and peer review utilities
are provided in :mod:`wsde_utils` and monkey patched in via
:mod:`wsde_facade`.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional
from uuid import uuid4

from devsynth.logging_setup import DevSynthLogger
from devsynth.domain.models.wsde_typing import (
    HookType,
    RoleAssignments,
    RoleName,
    SupportsTeamAgent,
)

logger = DevSynthLogger(__name__)


@dataclass
class WSDE:
    """Working Structured Document Entity.

    A WSDE represents a piece of structured content that can be manipulated by
    agents and stored in the memory system.
    """

    id: Optional[str] = None
    content: str = ""
    content_type: str = "text"  # e.g. text, code, image
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid4())
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at


class WSDETeam:
    """Minimal WSDE team implementation.

    This class focuses purely on managing a collection of agents and basic role
    tracking.  Behavioural extensions such as role assignment, voting and
    dialectical reasoning are attached dynamically by :mod:`wsde_facade`.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        agents: Optional[Iterable[SupportsTeamAgent]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.agents: list[SupportsTeamAgent] = []
        self.roles = RoleAssignments()
        self.solutions: dict[str, list[dict[str, object]]] = {}
        self.dialectical_hooks: list[HookType] = []
        self.voting_history: list[dict[str, object]] = []
        self.agent_opinions: dict[str, dict[str, str]] = {}
        self.logger = logger
        self.primus_index = 0
        self.message_protocol = None
        self.peer_reviews: list[object] = []
        self.external_knowledge: dict[str, object] = {}
        self._force_tie_for_task_id: Optional[str] = None
        self._force_tie_options: Optional[list[str]] = None
        self.tracked_decisions: dict[str, object] = {}
        self._knowledge_memory: dict[str, object] = {}
        if agents:
            self.add_agents(list(agents))

    # ------------------------------------------------------------------
    # Agent management
    # ------------------------------------------------------------------
    def add_agent(self, agent: SupportsTeamAgent) -> None:
        """Add an agent to the team."""
        if not hasattr(agent, "has_been_primus"):
            agent.has_been_primus = False
        if not hasattr(agent, "id"):
            agent.id = str(uuid4())
        self.agents.append(agent)
        self.logger.info(
            "Added agent %s to team %s",
            getattr(agent, "name", "agent"),
            self.name,
        )

    def add_agents(self, agents: Iterable[SupportsTeamAgent]) -> None:
        """Add multiple agents to the team."""
        for agent in agents:
            self.add_agent(agent)

    # ------------------------------------------------------------------
    # Opinion and hook management
    # ------------------------------------------------------------------
    def set_agent_opinion(
        self, agent: SupportsTeamAgent, option_id: str, opinion: str
    ) -> None:
        """Record an agent's opinion on a decision option."""
        agent_name: str = str(getattr(
            getattr(agent, "config", None), "name", None
        ) or getattr(agent, "name", "Agent"))
        self.agent_opinions.setdefault(agent_name, {})[option_id] = opinion

    def register_dialectical_hook(self, hook: HookType) -> None:
        """Register a callback to run when a new solution is added."""
        self.dialectical_hooks.append(hook)

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------
    def rotate_primus(self) -> None:
        """Rotate the primus role to the next agent."""
        if not self.agents:
            return
        self.primus_index = (self.primus_index + 1) % len(self.agents)
        if all(getattr(a, "has_been_primus", False) for a in self.agents):
            for a in self.agents:
                a.has_been_primus = False
        primus = self.agents[self.primus_index]
        primus.has_been_primus = True
        self.roles[RoleName.PRIMUS] = primus

    def get_primus(self) -> Optional[Any]:
        """Return the current primus agent, assigning a default if needed."""

        primus = self.roles.get(RoleName.PRIMUS)
        if primus is None and self.agents:
            primus = self.agents[0]
            self.roles[RoleName.PRIMUS] = primus
        return primus

    def get_agent_by_role(self, role: str) -> SupportsTeamAgent | None:
        """Get an agent with the specified role."""
        if role.lower() == "primus":
            return self.get_primus()
        role_cap = role.capitalize()
        for agent in self.agents:
            if getattr(agent, "current_role", None) == role_cap:
                return agent
        return None


__all__ = ["WSDE", "WSDETeam"]
