"""Typed primitives for Worker Self-Directed Enterprise models.

This module centralises the lightweight protocol, enum, and dataclass helpers
used by the WSDE domain model. Historically the WSDE team logic relied on
``Any`` rich dictionaries that were mutated dynamically by monkey-patched
helpers.  Static type checking therefore provided little protection.  The
structures defined here replace those ``Any`` dictionaries with explicit
schemas that make the behaviour of the WSDE orchestration code observable to
both humans and type checkers.

The primitives live in their own module to avoid circular imports between the
core team implementation, voting logic, and role assignment strategies.  They
intentionally avoid any business logic in favour of small helpers that model
domain concepts such as roles, votes, and consensus rounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Dict,
    List,
    Protocol,
    runtime_checkable,
)
from collections.abc import Callable, Iterable, MutableMapping, Sequence


class VoteMethod(str, Enum):
    """Supported WSDE voting methods."""

    MAJORITY = "majority"
    WEIGHTED = "weighted"


class VoteStatus(str, Enum):
    """Lifecycle stages for voting processes."""

    PENDING = "pending"
    COMPLETED = "completed"
    TIED = "tied"
    FAILED = "failed"


class ConsensusStatus(str, Enum):
    """Possible outcomes for consensus building."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial_consensus"
    FAILED = "failed"


class RoleName(str, Enum):
    """Canonical WSDE role identifiers."""

    PRIMUS = "primus"
    WORKER = "worker"
    SUPERVISOR = "supervisor"
    DESIGNER = "designer"
    EVALUATOR = "evaluator"

    @classmethod
    def ordered(cls) -> Sequence[RoleName]:
        """Return the deterministic rotation order for roles."""

        return (
            cls.PRIMUS,
            cls.WORKER,
            cls.SUPERVISOR,
            cls.DESIGNER,
            cls.EVALUATOR,
        )


@runtime_checkable
class SupportsTeamAgent(Protocol):
    """Protocol describing the attributes consumed by WSDE strategies.

    The real agent implementations inside the DevSynth platform are richer,
    however the WSDE domain model only needs a minimal surface:

    - ``name`` for logging and vote mapping;
    - ``expertise`` for weighted voting and role assignment;
    - ``has_been_primus``/``current_role``/``previous_role`` bookkeeping to
      support fair rotation across activities.

    The attributes are modelled as ``Protocol`` members so that unit tests may
    use lightweight dataclasses rather than the full production agents.  The
    protocol is ``runtime_checkable`` which allows defensive ``isinstance``
    assertions where appropriate.
    """

    name: str
    expertise: Sequence[str] | None
    has_been_primus: bool
    current_role: str | None
    previous_role: str | None


TaskDict = MutableMapping[str, object]
"""Convenience alias for task-like dictionaries passed between strategies."""


@dataclass(slots=True)
class RoleAssignments:
    """Strongly-typed representation of team role allocations."""

    assignments: dict[RoleName, SupportsTeamAgent | None] = field(
        default_factory=lambda: {role: None for role in RoleName}
    )

    def __getitem__(
        self, role: RoleName
    ) -> SupportsTeamAgent | None:  # pragma: no cover - trivial
        return self.assignments[role]

    def __setitem__(self, role: RoleName, agent: SupportsTeamAgent | None) -> None:
        self.assignments[role] = agent

    def get(
        self, role: RoleName, default: SupportsTeamAgent | None = None
    ) -> SupportsTeamAgent | None:
        """Return the agent assigned to ``role`` if present."""

        return self.assignments.get(role, default)

    def items(
        self,
    ) -> Iterable[
        tuple[RoleName, SupportsTeamAgent | None]
    ]:  # pragma: no cover - trivial
        return self.assignments.items()

    def as_name_mapping(self) -> dict[str, SupportsTeamAgent | None]:
        """Expose assignments using string keys to preserve legacy semantics."""

        return {role.value: agent for role, agent in self.assignments.items()}

    def from_name_mapping(
        self, mapping: MutableMapping[str, SupportsTeamAgent | None]
    ) -> None:
        """Populate assignments from a ``str`` keyed mapping."""

        for role, agent in mapping.items():
            self.assignments[RoleName(role)] = agent


@dataclass(slots=True)
class VoteRecord:
    """Captured information about a single voting process."""

    method: VoteMethod
    options: Sequence[str]
    votes: dict[str, str]
    vote_counts: dict[str, int]
    status: VoteStatus
    explanation: str
    result: object
    weights: dict[str, float] | None = None
    weighted_votes: dict[str, float] | None = None


@dataclass(slots=True)
class ConsensusRound:
    """Immutable snapshot of a consensus discussion round."""

    round_number: int
    preferences: dict[str, dict[str, float]]
    adjustments: dict[str, dict[str, float]]
    discussions: Sequence[str]


@dataclass(slots=True)
class ConsensusResult:
    """Structured result of a consensus process."""

    status: ConsensusStatus
    result: str | None
    explanation: str
    rounds: list[ConsensusRound]
    final_preferences: dict[str, dict[str, float]]


@dataclass(slots=True)
class VotingTranscript:
    """Structured description of a voting process."""

    identifier: str
    timestamp: datetime
    task_id: str
    method: VoteMethod
    options: Sequence[str]
    votes: dict[str, str]
    reasoning: dict[str, str]
    record: VoteRecord

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.identifier,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "method": self.method.value,
            "options": list(self.options),
            "votes": dict(self.votes),
            "reasoning": dict(self.reasoning),
            "status": self.record.status.value,
            "result": self.record.result,
            "vote_counts": dict(self.record.vote_counts),
            "explanation": self.record.explanation,
            "weighted_votes": dict(self.record.weighted_votes or {}),
            "weights": dict(self.record.weights or {}),
        }


@dataclass(slots=True)
class ConsensusTranscript:
    """Structured description of a consensus-building process."""

    identifier: str
    timestamp: datetime
    task_id: str
    options: Sequence[str]
    initial_preferences: dict[str, dict[str, float]]
    result: ConsensusResult

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.identifier,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "options": list(self.options),
            "initial_preferences": self.initial_preferences,
            "final_preferences": self.result.final_preferences,
            "rounds": [
                {
                    "round": round_data.round_number,
                    "preferences": round_data.preferences,
                    "adjustments": round_data.adjustments,
                    "discussions": list(round_data.discussions),
                }
                for round_data in self.result.rounds
            ],
            "status": self.result.status.value,
            "result": self.result.result,
            "explanation": self.result.explanation,
        }


HookType = Callable[[TaskDict, list[dict[str, object]]], None]
"""Type alias for dialectical hook callables."""
