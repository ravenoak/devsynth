
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
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
    inputs: Dict[str, Any] = None
    outputs: Dict[str, Any] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    def __post_init__(self):
        if self.inputs is None:
            self.inputs = {}
        if self.outputs is None:
            self.outputs = {}

@dataclass
class Workflow:
    """A workflow in the DevSynth system."""
    id: str = None
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid4())
        if self.steps is None:
            self.steps = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at
