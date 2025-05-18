
import pytest
from datetime import datetime
from uuid import UUID
from devsynth.domain.models.workflow import WorkflowStatus, WorkflowStep, Workflow

class TestWorkflowModels:
    def test_workflow_status_enum(self):
        # Test that all expected workflow statuses are defined
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.PAUSED.value == "paused"
    
    def test_workflow_step_initialization(self):
        # Test default initialization
        step = WorkflowStep(
            id="step-1",
            name="Analyze Requirements",
            description="Analyze project requirements",
            agent_type="planner"
        )
        
        assert step.id == "step-1"
        assert step.name == "Analyze Requirements"
        assert step.description == "Analyze project requirements"
        assert step.agent_type == "planner"
        assert isinstance(step.inputs, dict)
        assert isinstance(step.outputs, dict)
        assert step.status == WorkflowStatus.PENDING
    
    def test_workflow_initialization(self):
        # Test default initialization
        workflow = Workflow()
        
        assert workflow.name == ""
        assert workflow.description == ""
        assert isinstance(workflow.steps, list)
        assert workflow.status == WorkflowStatus.PENDING
        assert isinstance(workflow.created_at, datetime)
        assert isinstance(workflow.updated_at, datetime)
        assert workflow.created_at == workflow.updated_at
        
        # Verify UUID format
        try:
            UUID(workflow.id)
        except ValueError:
            pytest.fail("Workflow id is not a valid UUID")
    
    def test_workflow_with_steps(self):
        # Test initialization with steps
        step1 = WorkflowStep(
            id="step-1",
            name="Analyze Requirements",
            description="Analyze project requirements",
            agent_type="planner"
        )
        
        step2 = WorkflowStep(
            id="step-2",
            name="Generate Tests",
            description="Generate test cases",
            agent_type="tester"
        )
        
        workflow = Workflow(
            id="workflow-1",
            name="Test Workflow",
            description="A test workflow",
            steps=[step1, step2],
            status=WorkflowStatus.RUNNING
        )
        
        assert workflow.id == "workflow-1"
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert len(workflow.steps) == 2
        assert workflow.steps[0].id == "step-1"
        assert workflow.steps[1].id == "step-2"
        assert workflow.status == WorkflowStatus.RUNNING
