"""Utility helpers for WSDE teams.

This module contains communication helpers, peer-review utilities and other
non-core helper functions that can be attached to :class:`WSDETeam` instances.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, Optional, Protocol, TypedDict, cast
from uuid import uuid4

from devsynth.domain.models.wsde_core import SolutionRecord, TaskPayload
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class MessageMetadata(TypedDict, total=False):
    """Optional metadata supported by the message protocol."""

    priority: str
    tags: Sequence[str]
    correlation_id: str


class PeerReviewResult(TypedDict):
    """Return payload from :func:`conduct_peer_review`."""

    review: object | None
    feedback: dict[str, Any]


class WorkflowResult(TypedDict, total=False):
    """Aggregated artefacts produced by :func:`run_basic_workflow`."""

    ideas: Sequence[Any]
    evaluations: Sequence[Any]
    multi_disciplinary_evaluation: Any
    best_option: Any
    details: Sequence[Any]
    implementation_plan: Any
    optimized_implementation: Any
    quality_assurance: Any
    learnings: Sequence[Any]


class SupportsMessageProtocol(Protocol):
    """Protocol for the subset of message protocol behaviour we rely on."""

    def send_message(
        self,
        *,
        sender: str,
        recipients: Sequence[str],
        message_type: str,
        subject: str = "",
        content: Any = None,
        metadata: MessageMetadata | None = None,
    ) -> object:  # pragma: no cover - simple delegation
        ...

    def get_messages(
        self, agent: str | None, filters: dict[str, Any] | None
    ) -> list[Any]:  # pragma: no cover - simple delegation
        ...


class SupportsPeerReview(Protocol):
    """Protocol capturing the methods used on peer review objects."""

    status: str

    def assign_reviews(self) -> None:  # pragma: no cover - simple delegation
        ...

    def collect_reviews(self) -> None:  # pragma: no cover - simple delegation
        ...

    def aggregate_feedback(
        self,
    ) -> dict[str, Any]:  # pragma: no cover - simple delegation
        ...


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
    recipients: Sequence[str],
    message_type: str,
    subject: str = "",
    content: Any = None,
    metadata: MessageMetadata | None = None,
) -> object | None:
    """Send a message using the team's message protocol."""
    _init_message_protocol(team)
    if not team.message_protocol:
        return None
    protocol = cast(SupportsMessageProtocol, team.message_protocol)
    return protocol.send_message(
        sender=sender,
        recipients=list(recipients),
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
    metadata: MessageMetadata | None = None,
) -> object | None:
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
    team: Any,
    agent: str | None = None,
    filters: dict[str, Any] | None = None,
) -> list[Any]:
    """Retrieve messages from the team's message protocol."""
    _init_message_protocol(team)
    if not team.message_protocol:
        return []
    protocol = cast(SupportsMessageProtocol, team.message_protocol)
    return protocol.get_messages(agent, filters)


# ---------------------------------------------------------------------------
# Peer review utilities
# ---------------------------------------------------------------------------


def request_peer_review(
    team: Any,
    work_product: Any,
    author: Any,
    reviewer_agents: Iterable[Any],
) -> SupportsPeerReview | None:
    """Create and track a peer review cycle."""
    try:  # pragma: no cover - external dependency best effort
        from devsynth.application.collaboration.peer_review import PeerReview
    except Exception as exc:  # pragma: no cover - peer review unavailable
        logger.warning("Peer review failed: %s", exc)
        return None

    review: SupportsPeerReview = PeerReview(
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
    team: Any,
    work_product: Any,
    author: Any,
    reviewer_agents: Iterable[Any],
) -> PeerReviewResult:
    """Run a full peer review cycle and return aggregated feedback."""
    review = request_peer_review(team, work_product, author, reviewer_agents)
    if review is None:
        return {"review": None, "feedback": {}}
    review.collect_reviews()
    feedback = review.aggregate_feedback()
    review.status = "completed"
    result: PeerReviewResult = {"review": review, "feedback": feedback}
    _flush_team_memory(team)
    return result


# ---------------------------------------------------------------------------
# Miscellaneous helpers
# ---------------------------------------------------------------------------


def add_solution(
    team: Any, task: TaskPayload, solution: SolutionRecord
) -> SolutionRecord:
    """Add a solution to the team and trigger dialectical hooks."""
    task_id = task.get("id")
    if not task_id:
        task_id = str(uuid4())
        task["id"] = task_id
    else:
        # Normalise the identifier on the task payload so future calls reuse it.
        task["id"] = task_id

    team.solutions.add(task_id, solution)

    task_solutions: list[SolutionRecord] | None = task.get("solutions")
    if task_solutions is None:
        task_solutions = []
        task["solutions"] = task_solutions
    task_solutions.append(solution)

    for hook in getattr(team, "dialectical_hooks", []):
        hook(task, team.solutions.for_task(task_id))
    logger.info("Added solution for task %s", task_id)
    _flush_team_memory(team)
    return solution


def run_basic_workflow(team: Any, task: TaskPayload) -> WorkflowResult:
    """Execute a minimal WSDE workflow and flush memory between steps."""

    results: WorkflowResult = {}

    ideas = cast(
        Sequence[Any],
        getattr(team, "generate_diverse_ideas", lambda *a, **k: [])(task),
    )
    results["ideas"] = ideas
    _flush_team_memory(team)

    evaluations = cast(
        Sequence[Any],
        getattr(team, "evaluate_options", lambda *a, **k: [])(ideas),
    )
    results["evaluations"] = evaluations
    _flush_team_memory(team)

    multi = getattr(team, "apply_multi_disciplinary_dialectical_reasoning", None)
    if callable(multi):
        multi_result = multi(
            task,
            critic_agent=None,
            disciplinary_knowledge={},
            disciplinary_agents=[],
            memory_integration=None,
        )
        results["multi_disciplinary_evaluation"] = multi_result
        _flush_team_memory(team)

    best: Any = getattr(team, "select_best_option", lambda *a, **k: {})(evaluations)
    results["best_option"] = best
    _flush_team_memory(team)

    details = cast(
        Sequence[Any], getattr(team, "elaborate_details", lambda *a, **k: [])(best)
    )
    results["details"] = details
    _flush_team_memory(team)

    plan: Any = getattr(team, "create_implementation_plan", lambda *a, **k: {})(details)
    results["implementation_plan"] = plan
    _flush_team_memory(team)

    optimized: Any = getattr(team, "optimize_implementation", lambda *a, **k: {})(plan)
    results["optimized_implementation"] = optimized
    _flush_team_memory(team)

    qa: Any = getattr(team, "perform_quality_assurance", lambda *a, **k: {})(optimized)
    results["quality_assurance"] = qa
    _flush_team_memory(team)

    learnings = cast(
        Sequence[Any], getattr(team, "extract_learnings", lambda *a, **k: [])(qa)
    )
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
