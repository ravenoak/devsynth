from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...domain.models.workflow import Workflow, WorkflowStep

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class WorkflowEngine(Protocol):
    """Protocol for workflow execution engine."""

    @abstractmethod
    def create_workflow(self, name: str, description: str) -> Workflow:
        """Create a new workflow."""
        ...

    @abstractmethod
    def add_step(self, workflow: Workflow, step: WorkflowStep) -> Workflow:
        """Add a step to a workflow."""
        ...

    @abstractmethod
    def execute_workflow(
        self, workflow: Workflow, context: Dict[str, Any] = None
    ) -> Workflow:
        """Execute a workflow with the given context."""
        ...

    @abstractmethod
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        ...


class WorkflowRepository(Protocol):
    """Protocol for workflow storage."""

    @abstractmethod
    def save(self, workflow: Workflow) -> None:
        """Save a workflow."""
        ...

    @abstractmethod
    def get(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        ...

    @abstractmethod
    def list(self, filters: Dict[str, Any] = None) -> List[Workflow]:
        """List workflows matching the filters."""
        ...
