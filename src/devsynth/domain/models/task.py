"""
Domain models for tasks.
"""

from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class TaskStatus(Enum):
    """Enum representing the status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """Model representing a task to be performed by an agent."""

    def __init__(
        self,
        id: Optional[str] = None,
        task_type: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        assigned_to: Optional[str] = None,
        status: TaskStatus = TaskStatus.PENDING,
        result: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a Task instance.

        Args:
            id: Unique identifier for the task
            task_type: Type of the task (e.g., "analyze", "transform", "refine")
            data: Dictionary containing task-specific data
            assigned_to: Name of the agent assigned to the task
            status: Current status of the task
            result: Dictionary containing the result of the task
        """
        self.id = id if id is not None else str(uuid4())
        self.task_type = task_type
        self.data = data or {}
        self.assigned_to = assigned_to
        self.status = status
        self.result = result or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Task object to a dictionary representation."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "data": self.data,
            "assigned_to": self.assigned_to,
            "status": (
                self.status.value if isinstance(self.status, Enum) else self.status
            ),
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a Task object from a dictionary representation."""
        status_value = data.get("status")
        status: TaskStatus = TaskStatus.PENDING
        if status_value:
            for s in TaskStatus:
                if s.value == status_value:
                    status = s
                    break

        return cls(
            id=data.get("id"),
            task_type=data.get("task_type"),
            data=data.get("data", {}),
            assigned_to=data.get("assigned_to"),
            status=status,
            result=data.get("result", {}),
        )
