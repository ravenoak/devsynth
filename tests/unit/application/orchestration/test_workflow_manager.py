"""Tests for WorkflowManager. # ReqID: FR-09"""
from unittest.mock import MagicMock

from devsynth.application.orchestration.workflow import WorkflowManager


def test_get_workflow_status_delegates_to_port():
    """Workflow status and progress tracking."""
    port = MagicMock()
    manager = WorkflowManager(bridge=MagicMock())
    manager.orchestration_port = port

    manager.get_workflow_status("wf-123")

    port.get_workflow_status.assert_called_once_with("wf-123")
