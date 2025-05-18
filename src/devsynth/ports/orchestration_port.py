
from typing import Any, Dict, List, Optional
from ..domain.interfaces.orchestration import WorkflowEngine, WorkflowRepository
from ..domain.models.workflow import Workflow, WorkflowStep

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class OrchestrationPort:
    """Port for the orchestration system."""
    
    def __init__(self, workflow_engine: WorkflowEngine, workflow_repository: WorkflowRepository):
        self.workflow_engine = workflow_engine
        self.workflow_repository = workflow_repository
    
    def create_workflow(self, name: str, description: str) -> Workflow:
        """Create a new workflow."""
        workflow = self.workflow_engine.create_workflow(name, description)
        self.workflow_repository.save(workflow)
        return workflow
    
    def add_step(self, workflow: Workflow, step: WorkflowStep) -> Workflow:
        """Add a step to a workflow."""
        updated_workflow = self.workflow_engine.add_step(workflow, step)
        self.workflow_repository.save(updated_workflow)
        return updated_workflow
    
    def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> Workflow:
        """Execute a workflow with the given context."""
        workflow = self.workflow_repository.get(workflow_id)
        if workflow:
            executed_workflow = self.workflow_engine.execute_workflow(workflow, context)
            self.workflow_repository.save(executed_workflow)
            return executed_workflow
        return None
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        return self.workflow_engine.get_workflow_status(workflow_id)
