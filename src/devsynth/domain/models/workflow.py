from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class WorkflowStatus(Enum):
    """Status of a workflow in the DevSynth system."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""

    id: str
    name: str
    description: str
    agent_type: str
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING

    def __post_init__(self) -> None:
        if self.inputs is None:
            self.inputs = {}
        if self.outputs is None:
            self.outputs = {}


@dataclass
class Workflow:
    """A workflow in the DevSynth system."""

    id: str | None = None
    name: str = ""
    description: str = ""
    steps: list[WorkflowStep] | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid4())
        if self.steps is None:
            self.steps = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
