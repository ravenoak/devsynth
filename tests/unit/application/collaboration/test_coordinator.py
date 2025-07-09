import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.interfaces.agent import Agent
from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.exceptions import ValidationError
from devsynth.application.collaboration.exceptions import TeamConfigurationError


class TestAgentCoordinatorPrimusSelection:
    """Tests for the AgentCoordinatorPrimusSelection component.

ReqID: N/A"""

    def setup_method(self):
        self.coordinator = AgentCoordinatorImpl({'features': {
            'wsde_collaboration': True}})
        self.python_agent = MagicMock(spec=Agent)
        self.python_agent.name = 'python'
        self.python_agent.agent_type = 'code'
        self.python_agent.expertise = ['python', 'backend']
        self.python_agent.current_role = None
        self.python_agent.process.return_value = {'solution': 'python-solution'
            }
        self.js_agent = MagicMock(spec=Agent)
        self.js_agent.name = 'javascript'
        self.js_agent.agent_type = 'code'
        self.js_agent.expertise = ['javascript']
        self.js_agent.current_role = None
        self.js_agent.process.return_value = {'solution': 'js-solution'}
        self.doc_agent = MagicMock(spec=Agent)
        self.doc_agent.name = 'docs'
        self.doc_agent.agent_type = 'documentation'
        self.doc_agent.expertise = ['documentation']
        self.doc_agent.current_role = None
        self.doc_agent.process.return_value = {'solution': 'doc-solution'}
        for agent in [self.python_agent, self.js_agent, self.doc_agent]:
            self.coordinator.add_agent(agent)

    def test_primus_selection_and_consensus_fields_succeeds(self):
        """Test that primus selection and consensus fields succeeds.

ReqID: N/A"""
        consensus = {'consensus': 'final', 'contributors': ['python',
            'javascript', 'docs'], 'method': 'consensus_synthesis'}
        with patch.object(self.coordinator.team, 'build_consensus',
            return_value=consensus):
            with patch.object(self.coordinator.team,
                'select_primus_by_expertise', wraps=self.coordinator.team.
                select_primus_by_expertise) as spy:
                task = {'team_task': True, 'language': 'python', 'type':
                    'coding'}
                result = self.coordinator.delegate_task(task)
                spy.assert_called_once_with(task)
        assert self.coordinator.team.get_primus() == self.python_agent
        assert result['contributors'] == consensus['contributors']
        assert result['method'] == consensus['method']

    def test_multi_agent_consensus_reached_succeeds(self):
        """Test that multi agent consensus reached succeeds.

ReqID: N/A"""
        consensus = {'consensus': 'final-result', 'contributors': ['python',
            'javascript', 'docs'], 'method': 'consensus_synthesis'}
        with patch.object(self.coordinator.team, 'build_consensus',
            return_value=consensus) as bc:
            task = {'team_task': True, 'language': 'python', 'type': 'coding'}
            result = self.coordinator.delegate_task(task)
        bc.assert_called_once_with(task)
        self.python_agent.process.assert_called_once()
        self.js_agent.process.assert_called_once()
        self.doc_agent.process.assert_called_once()
        assert result['result'] == consensus['consensus']
        assert result['contributors'] == consensus['contributors']
        assert result['method'] == consensus['method']

    def test_role_assignment_and_primus_selection_succeeds(self):
        """Test that role assignment and primus selection succeeds.

ReqID: N/A"""
        consensus = {'consensus': 'ok', 'contributors': ['python',
            'javascript', 'docs'], 'method': 'consensus_synthesis'}

        # Mock the assign_roles method to assign specific roles for testing
        original_assign_roles = self.coordinator.team.assign_roles

        def mock_assign_roles(*args, **kwargs):
            self.coordinator.team.roles["primus"] = self.python_agent
            self.coordinator.team.roles["supervisor"] = self.js_agent
            self.coordinator.team.roles["worker"] = self.doc_agent
            return self.coordinator.team.roles

        with patch.object(self.coordinator.team, 'build_consensus',
            return_value=consensus):
            with patch.object(self.coordinator.team, 'assign_roles', 
                side_effect=mock_assign_roles):
                self.coordinator.delegate_task({'team_task': True, 'language':
                    'python', 'type': 'coding'})

        role_map = self.coordinator.team.get_role_map()
        assert role_map[self.python_agent.name] == 'Primus'
        assert role_map[self.js_agent.name] == 'Supervisor'
        assert role_map[self.doc_agent.name] == 'Worker'


class TestAgentCoordinatorErrorPaths:
    """Tests for the AgentCoordinatorErrorPaths component.

ReqID: N/A"""

    def test_missing_agent_type_succeeds(self):
        """Test that missing agent type succeeds.

ReqID: N/A"""
        coordinator = AgentCoordinatorImpl({'features': {
            'wsde_collaboration': True}})
        agent = MagicMock(spec=Agent)
        agent.name = 'planner'
        agent.agent_type = 'planner'
        agent.current_role = None
        coordinator.add_agent(agent)
        with pytest.raises(ValidationError):
            coordinator.delegate_task({'agent_type': 'nonexistent'})

    def test_critical_decision_invokes_voting_succeeds(self):
        """Test that critical decision invokes voting succeeds.

ReqID: N/A"""
        coordinator = AgentCoordinatorImpl({'features': {
            'wsde_collaboration': True}})
        agent = MagicMock(spec=Agent)
        agent.name = 'voter'
        agent.agent_type = 'planner'
        agent.current_role = None
        coordinator.add_agent(agent)
        task = {'team_task': True, 'type': 'critical_decision',
            'is_critical': True, 'options': [{'id': 'a'}, {'id': 'b'}]}
        with patch.object(coordinator.team, 'vote_on_critical_decision',
            return_value={'result': {'winner': 'a'}}) as vote:
            result = coordinator.delegate_task(task)
        vote.assert_called_once_with(task)
        assert result['result']['winner'] == 'a'

    def test_delegate_task_no_agents_registered_succeeds(self):
        """Test that delegate task no agents registered succeeds.

ReqID: N/A"""
        coordinator = AgentCoordinatorImpl({'features': {
            'wsde_collaboration': True}})
        task = {'team_task': True}
        with pytest.raises(TeamConfigurationError):
            coordinator.delegate_task(task)
