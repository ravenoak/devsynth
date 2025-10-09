from __future__ import annotations

"""Typed data structures for collaboration workflows."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    Protocol,
    Sequence,
    Union,
    runtime_checkable,
)
from uuid import uuid4

from devsynth.domain.models.memory import MemoryItem

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from devsynth.application.memory.memory_manager import MemoryManager

    from .dto import ConsensusOutcome


@dataclass(frozen=True)
class ReviewCycleSpec:
    """Configuration for initiating a peer review cycle."""

    work_product: Any
    author: Any
    reviewers: Sequence[Any]
    send_message: Optional[Callable[..., Any]] = None
    acceptance_criteria: Optional[Sequence[str]] = None
    quality_metrics: Optional[Mapping[str, Any]] = None
    team: Optional[Any] = None
    memory_manager: Optional["MemoryManager"] = None

    def __post_init__(self) -> None:  # pragma: no cover - simple normalization
        object.__setattr__(self, "reviewers", tuple(self.reviewers))
        if self.acceptance_criteria is not None:
            object.__setattr__(
                self,
                "acceptance_criteria",
                tuple(self.acceptance_criteria),
            )
        if self.quality_metrics is not None:
            object.__setattr__(self, "quality_metrics", dict(self.quality_metrics))


@dataclass
class ReviewCycleState:
    """Mutable state tracked for a peer review cycle."""

    review_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "pending"
    revision: Any = None
    revision_history: list[Any] = field(default_factory=list)
    quality_score: float = 0.0
    metrics_results: dict[str, Any] = field(default_factory=dict)
    consensus_result: dict[str, Any] = field(default_factory=dict)
    consensus_outcome: Optional["ConsensusOutcome"] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def touch(self) -> None:
        """Update the ``updated_at`` timestamp to now."""

        self.updated_at = datetime.now()


@dataclass(frozen=True)
class MemoryQueueEntry:
    """Structured representation of a queued memory synchronization item."""

    store: str
    item: MemoryItem

    def as_tuple(self) -> tuple[str, MemoryItem]:
        """Return the legacy tuple representation."""

        return self.store, self.item


@dataclass
class SubtaskSpec:
    """Specification for a single WSDE subtask."""

    id: str
    title: str
    description: str
    parent_task_id: str
    status: str = "pending"
    priority: str = "medium"
    assigned_to: Optional[str] = None
    progress: float = 0.0
    expertise_score: Optional[float] = None
    reassigned: bool = False
    previous_assignee: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, Any], *, parent_task_id: Optional[str] = None
    ) -> "SubtaskSpec":
        data = dict(mapping)
        subtask_id = data.pop("id", None) or str(uuid4())
        title = data.pop("title", f"Subtask {subtask_id}")
        description = data.pop("description", "")
        parent = parent_task_id or data.pop("parent_task_id", parent_task_id)
        if parent is None:
            raise ValueError("Subtask specification requires a parent_task_id")
        status = data.pop("status", "pending")
        priority = data.pop("priority", "medium")
        assigned_to = data.pop("assigned_to", None)
        progress = float(data.pop("progress", 0.0) or 0.0)
        expertise_score = data.pop("expertise_score", None)
        reassigned = bool(data.pop("reassigned", False))
        previous_assignee = data.pop("previous_assignee", None)
        return cls(
            id=str(subtask_id),
            title=str(title),
            description=str(description),
            parent_task_id=str(parent),
            status=str(status),
            priority=str(priority),
            assigned_to=(str(assigned_to) if assigned_to is not None else None),
            progress=progress,
            expertise_score=(
                float(expertise_score) if expertise_score is not None else None
            ),
            reassigned=reassigned,
            previous_assignee=(
                str(previous_assignee) if previous_assignee is not None else None
            ),
            metadata=data,
        )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "parent_task_id": self.parent_task_id,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "progress": self.progress,
            "expertise_score": self.expertise_score,
            "reassigned": self.reassigned,
            "previous_assignee": self.previous_assignee,
        }
        payload.update(self.metadata)
        return {k: v for k, v in payload.items() if v is not None}


@dataclass
class TaskSpec:
    """Specification for a WSDE task processed by the task management mixin."""

    id: str
    title: str
    description: Optional[str] = None
    requirements: list[str] = field(default_factory=list)
    status: str = "pending"
    priority: str = "medium"
    subtasks: list[SubtaskSpec] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "TaskSpec":
        data = dict(mapping)
        task_id = data.pop("id", None) or str(uuid4())
        title = data.pop("title", "Untitled task")
        description = data.pop("description", None)
        requirements_raw = data.pop("requirements", [])
        requirements = (
            list(requirements_raw) if isinstance(requirements_raw, Iterable) else []
        )
        status = data.pop("status", "pending")
        priority = data.pop("priority", "medium")
        subtasks_raw = data.pop("subtasks", [])
        subtasks = [
            SubtaskSpec.from_mapping(subtask, parent_task_id=task_id)
            for subtask in subtasks_raw
        ]
        return cls(
            id=str(task_id),
            title=str(title),
            description=(str(description) if description is not None else None),
            requirements=[str(req) for req in requirements],
            status=str(status),
            priority=str(priority),
            subtasks=subtasks,
            metadata=data,
        )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requirements": list(self.requirements),
            "status": self.status,
            "priority": self.priority,
            "subtasks": [subtask.to_payload() for subtask in self.subtasks],
        }
        payload.update(self.metadata)
        return {k: v for k, v in payload.items() if v is not None}


@dataclass(frozen=True)
class TaskDelegationResult:
    """Structured record describing a subtask delegation."""

    subtask_id: str
    assigned_to: Optional[str]
    expertise_score: float
    timestamp: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "subtask_id": self.subtask_id,
            "assigned_to": self.assigned_to,
            "expertise_score": self.expertise_score,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class TaskReassignmentResult:
    """Structured record describing a subtask reassignment."""

    subtask_id: str
    previous_assignee: Optional[str]
    new_assignee: Optional[str]
    expertise_score: float
    progress_at_reassignment: float
    timestamp: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "subtask_id": self.subtask_id,
            "previous_assignee": self.previous_assignee,
            "new_assignee": self.new_assignee,
            "expertise_score": self.expertise_score,
            "progress_at_reassignment": self.progress_at_reassignment,
            "timestamp": self.timestamp,
        }


@runtime_checkable
class TaskAgentProtocol(Protocol):
    """Protocol describing the minimal information required from a team agent."""

    name: str
    metadata: Mapping[str, Any] | None


@runtime_checkable
class TaskManagementContext(Protocol):
    """Protocol enforced for classes mixing in :class:`TaskManagementMixin`."""

    logger: Any
    agents: Sequence[TaskAgentProtocol]
    subtasks: MutableMapping[str, list[SubtaskSpec]]
    subtask_progress: MutableMapping[str, float]
    contribution_metrics: MutableMapping[str, MutableMapping[str, Dict[str, Any]]]

    def send_message(
        self,
        *,
        sender: str,
        recipients: Sequence[str],
        message_type: str,
        subject: str,
        content: Any,
    ) -> Any: ...

    def get_messages(
        self, *args: Any, **kwargs: Any
    ) -> Sequence[Mapping[str, Any]]: ...

    def _calculate_expertise_score(
        self, agent: TaskAgentProtocol, task: Mapping[str, Any]
    ) -> float: ...


TaskInput = Union[TaskSpec, Mapping[str, Any]]
SubtaskInput = Union[SubtaskSpec, Mapping[str, Any]]
