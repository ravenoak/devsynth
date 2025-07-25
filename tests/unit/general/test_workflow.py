from unittest.mock import MagicMock, patch
import pytest
from devsynth.adapters.orchestration.langgraph_adapter import NeedsHumanInterventionError
from devsynth.application.orchestration.workflow import WorkflowManager
from devsynth.domain.models.workflow import WorkflowStatus


class TestWorkflowManager:
    """Tests for the WorkflowManager class.

ReqID: N/A"""

    @pytest.fixture
    def workflow_manager(self):
        """Create a workflow manager with mocked dependencies."""
        with patch(
            'devsynth.application.orchestration.workflow.OrchestrationPort'
            ) as mock_port:
            manager = WorkflowManager()
            manager.orchestration_port = mock_port
            yield manager

    def test_handle_human_intervention_succeeds(self, workflow_manager):
        """Test handling human intervention.

ReqID: N/A"""
        with patch('devsynth.application.orchestration.workflow.console'
            ) as mock_console, patch(
            'devsynth.application.orchestration.workflow.Prompt.ask',
            return_value='User input'):
            response = workflow_manager._handle_human_intervention(
                'workflow-id', 'step-id', 'Need your input')
            assert response == 'User input'
            assert mock_console.print.call_count == 2

    def test_create_workflow_for_command_succeeds(self, workflow_manager):
        """Test creating a workflow for a command.

ReqID: N/A"""
        mock_workflow = MagicMock()
        (workflow_manager.orchestration_port.create_workflow.return_value
            ) = mock_workflow
        workflow_manager._add_init_workflow_steps = MagicMock()
        workflow_manager._add_spec_workflow_steps = MagicMock()
        workflow_manager._add_test_workflow_steps = MagicMock()
        workflow_manager._add_code_workflow_steps = MagicMock()
        workflow_manager._add_run_workflow_steps = MagicMock()
        workflow_manager._add_config_workflow_steps = MagicMock()
        commands = ['init', 'spec', 'test', 'code', 'run', 'config']
        for command in commands:
            result = workflow_manager._create_workflow_for_command(command,
                {'test': 'value'})
            assert result == mock_workflow
            workflow_manager.orchestration_port.create_workflow.assert_called()
            method_name = f'_add_{command}_workflow_steps'
            getattr(workflow_manager, method_name).assert_called_with(
                mock_workflow, {'test': 'value'})

    def test_add_init_workflow_steps_succeeds(self, workflow_manager):
        """Test adding steps for init workflow.

ReqID: N/A"""
        mock_workflow = MagicMock()
        workflow_manager._add_init_workflow_steps(mock_workflow, {'path':
            './test-project'})
        assert workflow_manager.orchestration_port.add_step.call_count == 3
        calls = workflow_manager.orchestration_port.add_step.call_args_list
        assert calls[0][0][0] == mock_workflow
        assert calls[1][0][0] == mock_workflow
        assert calls[2][0][0] == mock_workflow
        assert 'validator' in str(calls[0])
        assert 'file_system' in str(calls[1])
        assert 'config_manager' in str(calls[2])

    def test_execute_command_succeeds(self, workflow_manager):
        """Test executing a command.

ReqID: N/A"""
        mock_workflow = MagicMock()
        workflow_manager._create_workflow_for_command = MagicMock(return_value
            =mock_workflow)
        mock_executed_workflow = MagicMock()
        mock_executed_workflow.status = WorkflowStatus.COMPLETED
        mock_executed_workflow.result = {'success': True, 'message':
            'Command executed successfully'}
        (workflow_manager.orchestration_port.execute_workflow.return_value
            ) = mock_executed_workflow
        result = workflow_manager.execute_command('init', {'path':
            './test-project'})
        workflow_manager._create_workflow_for_command.assert_called_once_with(
            'init', {'path': './test-project'})
        workflow_manager.orchestration_port.execute_workflow.assert_called_once(
            )
        assert result['success'] is True
        assert result['message'] == 'Command executed successfully'

    def test_execute_command_failure_fails(self, workflow_manager):
        """Test executing a command that fails.

ReqID: N/A"""
        mock_workflow = MagicMock()
        workflow_manager._create_workflow_for_command = MagicMock(return_value
            =mock_workflow)
        mock_executed_workflow = MagicMock()
        mock_executed_workflow.status = WorkflowStatus.FAILED
        mock_executed_workflow.result = {'success': False, 'message':
            'Command failed'}
        (workflow_manager.orchestration_port.execute_workflow.return_value
            ) = mock_executed_workflow
        result = workflow_manager.execute_command('init', {'path':
            './test-project'})
        assert result['success'] is False
        assert result['message'] == 'Command failed'

    def test_execute_command_human_intervention_succeeds(self, workflow_manager
        ):
        """Test executing a command that requires human intervention.

ReqID: N/A"""
        mock_workflow = MagicMock()
        workflow_manager._create_workflow_for_command = MagicMock(return_value
            =mock_workflow)
        human_error = NeedsHumanInterventionError('Need your input',
            'workflow-id', 'step-id')
        mock_executed_workflow = MagicMock()
        mock_executed_workflow.status = WorkflowStatus.COMPLETED
        mock_executed_workflow.result = {'success': True, 'message':
            'Command executed successfully'}
        workflow_manager.orchestration_port.execute_workflow.side_effect = [
            human_error, mock_executed_workflow]
        workflow_manager._handle_human_intervention = MagicMock(return_value
            ='User input')
        result = workflow_manager.execute_command('init', {'path':
            './test-project'})
        assert workflow_manager.orchestration_port.execute_workflow.call_count == 2
        workflow_manager._handle_human_intervention.assert_called_once_with(
            'workflow-id', 'step-id', 'Need your input')
        assert result['success'] is True
        assert result['message'
            ] == 'Command executed successfully after human intervention'
