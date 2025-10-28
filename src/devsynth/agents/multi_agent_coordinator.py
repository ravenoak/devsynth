from __future__ import annotations

"""Utilities for coordinating multiple agents via simple consensus.

This module provides :class:`MultiAgentCoordinator`, a minimal interface for
registering agents that propose solutions and resolving a final decision via a
consensus mechanism. The implementation follows the requirements in
``docs/specifications/multi-agent-collaboration.md``.
"""

from collections import Counter
from typing import Any, Dict, Protocol
from collections.abc import Iterable

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class Proposer(Protocol):
    """Protocol for simple proposing agents.

    Agents only need to implement ``__call__`` returning a proposal for a given
    task.  They may also define ``accept`` to receive the final decision.
    """

    def __call__(self, task: Any) -> Any:  # pragma: no cover - Protocol signature
        ...

    def accept(self, decision: Any) -> None:  # pragma: no cover - optional
        ...


class MultiAgentCoordinator:
    """Coordinate multiple agents and resolve a consensus decision."""

    def __init__(self) -> None:
        self._agents: dict[str, Proposer] = {}

    def register_agent(self, name: str, agent: Proposer) -> None:
        """Register an agent by ``name``.

        Args:
            name: Unique identifier for the agent.
            agent: Callable returning a proposal for a task.
        """

        self._agents[name] = agent

    def gather_proposals(self, task: Any) -> dict[str, Any]:
        """Return proposals from all registered agents."""

        proposals: dict[str, Any] = {}
        for name, agent in self._agents.items():
            try:
                proposals[name] = agent(task)
            except Exception:  # pragma: no cover - defensive
                logger.debug(
                    "Agent %s failed to produce a proposal", name, exc_info=True
                )
        return proposals

    @staticmethod
    def _majority_vote(values: Iterable[Any]) -> Any:
        """Return the majority value with deterministic tie-breaking."""

        counts = Counter(values)
        # Sort by count descending then value string for determinism
        return sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))[0][0]

    def reach_consensus(self, task: Any) -> Any:
        """Gather proposals and broadcast the consensus decision."""

        proposals = self.gather_proposals(task)
        decision = self._majority_vote(proposals.values()) if proposals else None
        for agent in self._agents.values():
            accept = getattr(agent, "accept", None)
            if callable(accept):
                try:
                    accept(decision)
                except Exception:  # pragma: no cover - defensive
                    logger.debug("Agent failed to accept decision", exc_info=True)
        return decision


__all__ = ["MultiAgentCoordinator", "Proposer"]
