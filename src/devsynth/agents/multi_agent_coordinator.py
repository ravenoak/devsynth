from __future__ import annotations

"""Interfaces for coordinating multiple agents via simple consensus."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class ConsensusResult:
    """Outcome of a consensus round."""

    decision: Any
    rounds: int
    history: List[List[Any]] = field(default_factory=list)


class MultiAgentCoordinator:
    """Coordinate agents to reach a decision through majority consensus."""

    def __init__(
        self, agents: Iterable[Callable[[], Any]], threshold: float = 0.5
    ) -> None:
        """Store callable agents and required agreement threshold."""
        self._agents = list(agents)
        self._threshold = threshold

    def coordinate(self, max_rounds: int = 10) -> ConsensusResult:
        """Run consensus rounds until a decision meets the threshold.

        Args:
            max_rounds: Number of iterations to attempt.

        Raises:
            RuntimeError: If consensus is not reached within max_rounds.

        Returns:
            ConsensusResult capturing decision and vote history.
        """
        history: List[List[Any]] = []
        for round_idx in range(1, max_rounds + 1):
            votes = [agent() for agent in self._agents]
            history.append(votes)
            logger.debug("Round %s votes: %s", round_idx, votes)
            decision = self._majority(votes)
            if decision is not None:
                return ConsensusResult(
                    decision=decision, rounds=round_idx, history=history
                )
        raise RuntimeError("Consensus not reached")

    def _majority(self, votes: List[Any]) -> Any | None:
        """Return value meeting the threshold or ``None`` if no majority."""
        counts = Counter(votes)
        total = len(votes)
        for value, count in counts.items():
            if count / total >= self._threshold:
                logger.debug(
                    "Consensus reached on %s with %s/%s votes", value, count, total
                )
                return value
        return None
