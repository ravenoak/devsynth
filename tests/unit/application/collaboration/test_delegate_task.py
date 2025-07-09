import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.application.collaboration.exceptions import TeamConfigurationError, RoleAssignmentError, CollaborationError
from devsynth.domain.interfaces.agent import Agent
from devsynth.exceptions import ValidationError


class TestDelegateTask:
    """Tests for the DelegateTask component.

ReqID: N/A"""

    def setup_method(self) ->None:
        self.coordinator = AgentCoordinatorImpl({'features': {
            'wsde_collaboration': True}})
        self.designer = MagicMock(spec=Agent)
        self.designer.name = 'designer'
        self.designer.agent_type = 'planner'
        self.designer.expertise = ['design']
        self.designer.current_role = None
        self.designer.process.return_value = {'solution': 'design'}
        self.worker = MagicMock(spec=Agent)
        self.worker.name = 'worker'
        self.worker.agent_type = 'code'
        self.worker.expertise = ['python']
        self.worker.current_role = None
        self.worker.process.return_value = {'solution': 'code'}
        self.tester = MagicMock(spec=Agent)
        self.tester.name = 'tester'
        self.tester.agent_type = 'test'
        self.tester.expertise = ['testing']
        self.tester.current_role = None
        self.tester.process.return_value = {'solution': 'tests'}
        for agent in (self.designer, self.worker, self.tester):
            self.coordinator.add_agent(agent)

    def test_team_task_returns_consensus_succeeds(self) ->None:
        """Test that team task returns consensus succeeds.

ReqID: N/A"""
        consensus = {'consensus': 'final', 'contributors': ['designer',
            'worker', 'tester'], 'method': 'consensus_synthesis'}
        task = {'team_task': True, 'type': 'coding'}
        with patch.object(self.coordinator.team, 'build_consensus',
            return_value=consensus) as bc:
            with patch.object(self.coordinator.team,
                'select_primus_by_expertise', wraps=self.coordinator.team.
                select_primus_by_expertise) as sp:
                result = self.coordinator.delegate_task(task)
                sp.assert_called_once_with(task)
        bc.assert_called_once_with(task)
        assert result['result'] == consensus['consensus']
        assert result['contributors'] == consensus['contributors']
        assert result['method'] == consensus['method']

    def test_team_task_no_agents_succeeds(self) ->None:
        """Test that team task no agents succeeds.

ReqID: N/A"""
        coordinator = AgentCoordinatorImpl({'features': {
            'wsde_collaboration': True}})
        with pytest.raises(TeamConfigurationError):
            coordinator.delegate_task({'team_task': True})

    def test_invalid_task_format_succeeds(self) ->None:
        """Test that invalid task format succeeds.

ReqID: N/A"""
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task({})

    def test_delegate_task_propagates_agent_error_succeeds(self) ->None:
        """Test that delegate task propagates agent error succeeds.

ReqID: N/A"""
        with patch.object(self.coordinator, '_delegate_to_agent_type',
            side_effect=Exception('boom')) as del_mock:
            with pytest.raises(Exception):
                self.coordinator.delegate_task({'agent_type': 'planner'})
        del_mock.assert_called_once()

    def test_delegate_task_role_assignment_error_succeeds(self) ->None:
        """Test that delegate task role assignment error succeeds.

ReqID: N/A"""
        with patch.object(self.coordinator, '_handle_team_task',
            side_effect=RoleAssignmentError('no primus')) as handler:
            with pytest.raises(CollaborationError):
                self.coordinator.delegate_task({'team_task': True})
        handler.assert_called_once()
