"""Core WSDE models.

This module defines the minimal WSDE dataclass and a lightweight WSDETeam
implementation that only provides essential team-management behaviour.  More
advanced capabilities such as communication helpers and peer review utilities
are provided in :mod:`wsde_utils` and monkey patched in via
:mod:`wsde_facade`.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, MutableMapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, TypedDict
from uuid import uuid4

from devsynth.domain.models.wsde_typing import (
    HookType,
    RoleAssignments,
    RoleName,
    SupportsTeamAgent,
)
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class SolutionRecord(TypedDict, total=False):
    """Typed representation of a WSDE solution payload."""

    id: str
    content: str
    description: str
    rationale: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    author: str


class TaskPayload(TypedDict, total=False):
    """Structure describing a WSDE task exchanged between helpers."""

    id: str
    title: str
    description: str
    domain: str
    metadata: dict[str, Any]
    solutions: list[SolutionRecord]


class TaskContext(TypedDict, total=False):
    """Lightweight summary of a task stored alongside history entries."""

    id: str
    description: str
    domain: str


class VotingHistoryEntry(TypedDict, total=False):
    """Recorded snapshot of a voting process for later auditing."""

    options: list[str]
    votes: dict[str, str]
    status: str
    result: object
    reasoning: dict[str, str]
    weighted_votes: dict[str, float]
    weights: dict[str, float]
    explanation: str
    task_context: TaskContext


@dataclass(slots=True)
class SolutionsRegistry(MutableMapping[str, list[SolutionRecord]]):
    """Mapping of task identifiers to the solutions proposed for them."""

    _solutions: dict[str, list[SolutionRecord]] = field(default_factory=dict)

    def __getitem__(self, task_id: str) -> list[SolutionRecord]:
        return self._solutions[task_id]

    def __setitem__(
        self, task_id: str, value: list[SolutionRecord]
    ) -> None:  # pragma: no cover - trivial
        self._solutions[task_id] = value

    def __delitem__(self, task_id: str) -> None:  # pragma: no cover - defensive
        del self._solutions[task_id]

    def __iter__(self) -> Iterator[str]:  # pragma: no cover - trivial
        return iter(self._solutions)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._solutions)

    def add(self, task_id: str, solution: SolutionRecord) -> None:
        """Append ``solution`` to the collection for ``task_id``."""

        self._solutions.setdefault(task_id, []).append(solution)

    def for_task(self, task_id: str) -> list[SolutionRecord]:
        """Return the list of solutions registered for ``task_id``."""

        return self._solutions.setdefault(task_id, [])

    def setdefault(
        self, task_id: str, default: Optional[list[SolutionRecord]] = None
    ) -> list[SolutionRecord]:  # pragma: no cover - trivial
        if default is None:
            default = []
        return self._solutions.setdefault(task_id, default)


@dataclass(slots=True)
class VotingHistoryLog:
    """Lightweight container capturing historical voting outcomes."""

    _entries: list[VotingHistoryEntry] = field(default_factory=list)

    def append(self, value: VotingHistoryEntry) -> None:
        """Add a new voting history entry."""

        self._entries.append(value)

    def extend(
        self, values: Iterable[VotingHistoryEntry]
    ) -> None:  # pragma: no cover - trivial
        self._entries.extend(list(values))

    def __iter__(self) -> Iterator[VotingHistoryEntry]:  # pragma: no cover - trivial
        return iter(self._entries)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._entries)

    def __getitem__(
        self, index: int
    ) -> VotingHistoryEntry:  # pragma: no cover - trivial
        return self._entries[index]


@dataclass(slots=True)
class AgentOpinionRegistry(MutableMapping[str, dict[str, str]]):
    """Store for agent decision opinions keyed by option identifier."""

    _opinions: dict[str, dict[str, str]] = field(default_factory=dict)

    def __getitem__(
        self, agent_name: str
    ) -> dict[str, str]:  # pragma: no cover - trivial
        return self._opinions[agent_name]

    def __setitem__(
        self, agent_name: str, value: dict[str, str]
    ) -> None:  # pragma: no cover - trivial
        self._opinions[agent_name] = value

    def __delitem__(self, agent_name: str) -> None:  # pragma: no cover - defensive
        del self._opinions[agent_name]

    def __iter__(self) -> Iterator[str]:  # pragma: no cover - trivial
        return iter(self._opinions)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._opinions)

    def record(self, agent_name: str, option_id: str, opinion: str) -> None:
        """Persist ``opinion`` for ``agent_name`` on ``option_id``."""

        self._opinions.setdefault(agent_name, {})[option_id] = opinion

    def get_opinion(self, agent_name: str, option_id: str) -> Optional[str]:
        """Retrieve a previously recorded opinion if available."""

        return self._opinions.get(agent_name, {}).get(option_id)


@dataclass
class WSDE:
    """Working Structured Document Entity.

    A WSDE represents a piece of structured content that can be manipulated by
    agents and stored in the memory system.
    """

    id: Optional[str] = None
    content: str = ""
    content_type: str = "text"  # e.g. text, code, image
    metadata: Optional[MutableMapping[str, Any]] = None
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
        self.solutions = SolutionsRegistry()
        self.dialectical_hooks: list[HookType] = []
        self.voting_history = VotingHistoryLog()
        self.agent_opinions = AgentOpinionRegistry()
        self.logger = logger
        self.primus_index = 0
        self.message_protocol: Optional[object] = None
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
        agent_name: str = str(
            getattr(getattr(agent, "config", None), "name", None)
            or getattr(agent, "name", "Agent")
        )
        self.agent_opinions.record(agent_name, option_id, opinion)

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

    def get_primus(self) -> Optional[SupportsTeamAgent]:
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


__all__ = [
    "WSDE",
    "WSDETeam",
    "SolutionRecord",
    "TaskPayload",
    "TaskContext",
    "VotingHistoryEntry",
    "SolutionsRegistry",
    "VotingHistoryLog",
    "AgentOpinionRegistry",
]
