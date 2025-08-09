"""Utility helpers for WSDE teams.

This module contains communication helpers, peer-review utilities and other
non-core helper functions that can be attached to :class:`WSDETeam` instances.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


# ---------------------------------------------------------------------------
# Message protocol helpers
# ---------------------------------------------------------------------------


def _init_message_protocol(team: Any) -> None:
    """Initialise the message protocol for a team if available."""
    if getattr(team, "message_protocol", None) is not None:
        return
    try:  # pragma: no cover - best effort
        from devsynth.application.collaboration.message_protocol import MessageProtocol

        team.message_protocol = MessageProtocol()
    except Exception:  # pragma: no cover - fallback if protocol unavailable
        team.message_protocol = None


def send_message(
    team: Any,
    sender: str,
    recipients: List[str],
    message_type: str,
    subject: str = "",
    content: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Any:
    """Send a message using the team's message protocol."""
    _init_message_protocol(team)
    if not team.message_protocol:
        return None
    return team.message_protocol.send_message(
        sender=sender,
        recipients=recipients,
        message_type=message_type,
        subject=subject,
        content=content,
        metadata=metadata,
    )


def broadcast_message(
    team: Any,
    sender: str,
    message_type: str,
    subject: str = "",
    content: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Any:
    """Broadcast a message to all agents in the team."""
    recipients = [
        getattr(a, "name", f"agent_{i}")
        for i, a in enumerate(getattr(team, "agents", []))
        if getattr(a, "name", f"agent_{i}") != sender
    ]
    return send_message(
        team, sender, recipients, message_type, subject, content, metadata
    )


def get_messages(
    team: Any, agent: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
) -> List[Any]:
    """Retrieve messages from the team's message protocol."""
    _init_message_protocol(team)
    if not team.message_protocol:
        return []
    return team.message_protocol.get_messages(agent, filters)


# ---------------------------------------------------------------------------
# Peer review utilities
# ---------------------------------------------------------------------------


def request_peer_review(
    team: Any, work_product: Any, author: Any, reviewer_agents: Iterable[Any]
) -> Any:
    """Create and track a peer review cycle."""
    try:  # pragma: no cover - external dependency best effort
        from devsynth.application.collaboration.peer_review import PeerReview
    except Exception as exc:  # pragma: no cover - peer review unavailable
        logger.warning("Peer review failed: %s", exc)
        return None

    review = PeerReview(
        work_product=work_product,
        author=author,
        reviewers=list(reviewer_agents),
        send_message=lambda *a, **k: send_message(team, *a, **k),
        team=team,
        memory_manager=getattr(team, "memory_manager", None),
    )
    review.assign_reviews()
    team.peer_reviews.append(review)
    return review


def conduct_peer_review(
    team: Any, work_product: Any, author: Any, reviewer_agents: Iterable[Any]
) -> Dict[str, Any]:
    """Run a full peer review cycle and return aggregated feedback."""
    review = request_peer_review(team, work_product, author, reviewer_agents)
    if review is None:
        return {"review": None, "feedback": {}}
    review.collect_reviews()
    feedback = review.aggregate_feedback()
    review.status = "completed"
    return {"review": review, "feedback": feedback}


# ---------------------------------------------------------------------------
# Miscellaneous helpers
# ---------------------------------------------------------------------------


def add_solution(team: Any, task: Dict[str, Any], solution: Dict[str, Any]):
    """Add a solution to the team and trigger dialectical hooks."""
    task_id = task.get("id", str(uuid4()))
    team.solutions.setdefault(task_id, [])
    team.solutions[task_id].append(solution)
    for hook in getattr(team, "dialectical_hooks", []):
        hook(task, team.solutions[task_id])
    logger.info("Added solution for task %s", task_id)
    return solution


__all__ = [
    "send_message",
    "broadcast_message",
    "get_messages",
    "request_peer_review",
    "conduct_peer_review",
    "add_solution",
]
