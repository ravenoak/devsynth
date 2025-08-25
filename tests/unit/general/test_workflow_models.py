from datetime import datetime
from uuid import UUID

import pytest

from devsynth.domain.models.workflow import Workflow, WorkflowStatus, WorkflowStep


class TestWorkflowModels:
    """Tests for the WorkflowModels component.

    ReqID: N/A"""

    def test_workflow_status_enum_succeeds(self):
        """Test that workflow status enum succeeds.

        ReqID: N/A"""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.PAUSED.value == "paused"

    def test_workflow_step_initialization_succeeds(self):
        """Test that workflow step initialization succeeds.

        ReqID: N/A"""
        step = WorkflowStep(
            id="step-1",
            name="Analyze Requirements",
            description="Analyze project requirements",
            agent_type="planner",
        )
        assert step.id == "step-1"
        assert step.name == "Analyze Requirements"
        assert step.description == "Analyze project requirements"
        assert step.agent_type == "planner"
        assert isinstance(step.inputs, dict)
        assert isinstance(step.outputs, dict)
        assert step.status == WorkflowStatus.PENDING

    def test_workflow_initialization_succeeds(self):
        """Test that workflow initialization succeeds.

        ReqID: N/A"""
        workflow = Workflow()
        assert workflow.name == ""
        assert workflow.description == ""
        assert isinstance(workflow.steps, list)
        assert workflow.status == WorkflowStatus.PENDING
        assert isinstance(workflow.created_at, datetime)
        assert isinstance(workflow.updated_at, datetime)
        assert workflow.created_at == workflow.updated_at
        try:
            UUID(workflow.id)
        except ValueError:
            pytest.fail("Workflow id is not a valid UUID")

    def test_workflow_with_steps_succeeds(self):
        """Test that workflow with steps succeeds.

        ReqID: N/A"""
        step1 = WorkflowStep(
            id="step-1",
            name="Analyze Requirements",
            description="Analyze project requirements",
            agent_type="planner",
        )
        step2 = WorkflowStep(
            id="step-2",
            name="Generate Tests",
            description="Generate test cases",
            agent_type="tester",
        )
        workflow = Workflow(
            id="workflow-1",
            name="Test Workflow",
            description="A test workflow",
            steps=[step1, step2],
            status=WorkflowStatus.RUNNING,
        )
        assert workflow.id == "workflow-1"
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert len(workflow.steps) == 2
        assert workflow.steps[0].id == "step-1"
        assert workflow.steps[1].id == "step-2"
        assert workflow.status == WorkflowStatus.RUNNING
