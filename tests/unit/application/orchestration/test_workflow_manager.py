import pytest

"Tests for WorkflowManager. # ReqID: FR-09"
from unittest.mock import MagicMock

from devsynth.application.orchestration.workflow import WorkflowManager


@pytest.mark.medium
def test_get_workflow_status_delegates_to_port_succeeds():
    """Workflow status and progress tracking.

    ReqID: N/A"""
    port = MagicMock()
    manager = WorkflowManager(bridge=MagicMock())
    manager.orchestration_port = port
    manager.get_workflow_status("wf-123")
    port.get_workflow_status.assert_called_once_with("wf-123")
