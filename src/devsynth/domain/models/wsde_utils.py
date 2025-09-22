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


def _flush_team_memory(team: Any) -> None:
    """Flush pending memory updates for ``team`` if available."""
    memory_manager = getattr(team, "memory_manager", None)
    if memory_manager and hasattr(memory_manager, "flush_updates"):
        try:  # pragma: no cover - best effort
            memory_manager.flush_updates()
        except Exception:  # pragma: no cover - defensive
            logger.debug("Memory flush failed", exc_info=True)


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
    _flush_team_memory(team)
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
    result = {"review": review, "feedback": feedback}
    _flush_team_memory(team)
    return result


# ---------------------------------------------------------------------------
# Miscellaneous helpers
# ---------------------------------------------------------------------------


def add_solution(team: Any, task: Dict[str, Any], solution: Dict[str, Any]):
    """Add a solution to the team and trigger dialectical hooks."""
    task_id = task.get("id")
    if not task_id:
        task_id = str(uuid4())
        task["id"] = task_id
    else:
        # Normalise the identifier on the task payload so future calls reuse it.
        task["id"] = task_id

    team.solutions.setdefault(task_id, [])
    team.solutions[task_id].append(solution)
    task.setdefault("solutions", []).append(solution)
    for hook in getattr(team, "dialectical_hooks", []):
        hook(task, team.solutions[task_id])
    logger.info("Added solution for task %s", task_id)
    _flush_team_memory(team)
    return solution


def run_basic_workflow(team: Any, task: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a minimal WSDE workflow and flush memory between steps."""

    results: Dict[str, Any] = {}

    ideas = getattr(team, "generate_diverse_ideas", lambda *a, **k: [])(task)
    results["ideas"] = ideas
    _flush_team_memory(team)

    evaluations = getattr(team, "evaluate_options", lambda *a, **k: [])(ideas)
    results["evaluations"] = evaluations
    _flush_team_memory(team)

    multi = getattr(team, "apply_multi_disciplinary_dialectical_reasoning", None)
    if callable(multi):
        results["multi_disciplinary_evaluation"] = multi(
            task,
            critic_agent=None,
            disciplinary_knowledge={},
            disciplinary_agents=[],
            memory_integration=None,
        )
        _flush_team_memory(team)

    best = getattr(team, "select_best_option", lambda *a, **k: {})(evaluations)
    results["best_option"] = best
    _flush_team_memory(team)

    details = getattr(team, "elaborate_details", lambda *a, **k: [])(best)
    results["details"] = details
    _flush_team_memory(team)

    plan = getattr(team, "create_implementation_plan", lambda *a, **k: {})(details)
    results["implementation_plan"] = plan
    _flush_team_memory(team)

    optimized = getattr(team, "optimize_implementation", lambda *a, **k: {})(plan)
    results["optimized_implementation"] = optimized
    _flush_team_memory(team)

    qa = getattr(team, "perform_quality_assurance", lambda *a, **k: {})(optimized)
    results["quality_assurance"] = qa
    _flush_team_memory(team)

    learnings = getattr(team, "extract_learnings", lambda *a, **k: [])(qa)
    results["learnings"] = learnings
    _flush_team_memory(team)

    return results


__all__ = [
    "send_message",
    "broadcast_message",
    "get_messages",
    "request_peer_review",
    "conduct_peer_review",
    "add_solution",
    "run_basic_workflow",
]
