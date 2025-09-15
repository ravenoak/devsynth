"""Simple consensus-building utilities.

This module provides a deterministic consensus algorithm based on
majority voting. It operates over a finite set of votes and terminates
once vote counts are computed.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass(frozen=True)
class ConsensusResult:
    """Result returned by :func:`build_consensus`.

    Attributes:
        id: Unique identifier for the consensus session.
        timestamp: Time the consensus was computed.
        counts: Mapping of each option to its vote count.
        decision: Chosen option if consensus threshold met, otherwise ``None``.
        ratio: Proportion of votes supporting the decision.
        consensus: Whether consensus threshold was reached.
        dissenting: Options that did not reach consensus
        (absent when consensus achieved).
    """

    id: str
    timestamp: datetime
    counts: Mapping[Hashable, int]
    decision: Hashable | None
    ratio: float
    consensus: bool
    dissenting: Sequence[Hashable] | None = None


def build_consensus(
    votes: Sequence[Hashable], threshold: float = 0.5
) -> ConsensusResult:
    """Compute consensus from a sequence of votes.

    The algorithm counts occurrences of each option and selects the option
    with the highest frequency. Consensus is achieved when the winning option
    meets or exceeds ``threshold`` proportion of the total votes.

    Args:
        votes: Iterable of hashable vote options.
        threshold: Proportion of votes required to declare consensus.

    Returns:
        :class:`ConsensusResult` summarizing the decision.

    Raises:
        ValueError: If ``votes`` is empty or ``threshold`` is outside (0, 1].
    """

    if not votes:
        raise ValueError("votes must not be empty")
    if not (0 < threshold <= 1):
        raise ValueError("threshold must be within (0, 1]")

    counts = Counter(votes)
    option, count = counts.most_common(1)[0]
    ratio = count / len(votes)
    consensus = ratio >= threshold
    decision = option if consensus else None
    dissenting = None if consensus else list(counts.keys())

    return ConsensusResult(
        id=str(uuid4()),
        timestamp=datetime.now(),
        counts=dict(counts),
        decision=decision,
        ratio=ratio,
        consensus=consensus,
        dissenting=dissenting,
    )
