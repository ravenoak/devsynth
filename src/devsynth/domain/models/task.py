"""Domain models for tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(Enum):
    """Enum representing the status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Model representing a task to be performed by an agent."""

    id: str = field(default_factory=lambda: str(uuid4()))
    task_type: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    assigned_to: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the Task object to a dictionary representation."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "data": self.data,
            "assigned_to": self.assigned_to,
            "status": self.status.value,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Create a Task object from a dictionary representation."""
        status_value = data.get("status")
        status = TaskStatus.PENDING
        if status_value:
            for s in TaskStatus:
                if s.value == status_value:
                    status = s
                    break

        return cls(
            id=data.get("id") or "",
            task_type=data.get("task_type"),
            data=data.get("data", {}),
            assigned_to=data.get("assigned_to"),
            status=status,
            result=data.get("result", {}),
        )
