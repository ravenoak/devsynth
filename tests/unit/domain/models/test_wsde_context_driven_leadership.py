"""
Unit Tests for WSDE Context-Driven Leadership functionality.

This file contains unit tests for the enhanced Context-Driven Leadership
functionality in the WSDE model, including improved expertise scoring,
dynamic role switching, and adaptive leadership selection.
"""
import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


class SimpleAgent:
    """A simple agent class for testing."""

    def __init__(self, name, expertise=None, experience_level=None,
        performance_history=None):
        self.name = name
        self.expertise = expertise or []
        self.current_role = None
        self.has_been_primus = False
        self.experience_level = experience_level
        self.performance_history = performance_history or {}


class TestEnhancedExpertiseScoring:
    """Test suite for enhanced expertise scoring methods.

ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name='test_team')
        self.python_agent = SimpleAgent(name='python_dev', expertise=[
            'python', 'code_generation', 'api_development'],
            experience_level=5, performance_history={'code_generation': 0.9})
        self.doc_agent = SimpleAgent(name='doc_writer', expertise=[
            'documentation', 'technical_writing', 'markdown'],
            experience_level=8, performance_history={'documentation': 0.95})
        self.test_agent = SimpleAgent(name='tester', expertise=['testing',
            'test_automation', 'quality_assurance'], experience_level=3,
            performance_history={'testing': 0.8})
        self.security_agent = SimpleAgent(name='security_expert', expertise
            =['security', 'authentication', 'encryption'], experience_level
            =7, performance_history={'security': 0.85})
        self.team.add_agents([self.python_agent, self.doc_agent, self.
            test_agent, self.security_agent])

    @pytest.mark.medium
    def test_enhanced_calculate_expertise_score_exact_match_matches_expected(
        self):
        """Test enhanced expertise scoring with exact keyword matches.

ReqID: N/A"""
        task = {'type': 'code_generation', 'language': 'python'}
        score = self.team.enhanced_calculate_expertise_score(self.
            python_agent, task)
        assert score > 0
        assert score > self.team.enhanced_calculate_expertise_score(self.
            doc_agent, task)

    @pytest.mark.medium
    def test_enhanced_calculate_expertise_score_partial_match_matches_expected(
        self):
        """Test enhanced expertise scoring with partial keyword matches.

ReqID: N/A"""
        task = {'description': 'Create Python code for API integration'}
        score = self.team.enhanced_calculate_expertise_score(self.
            python_agent, task)
        assert score > 0
        assert score > self.team.enhanced_calculate_expertise_score(self.
            doc_agent, task)

    @pytest.mark.medium
    def test_enhanced_calculate_expertise_score_experience_level_succeeds(self
        ):
        """Test that experience level affects expertise scoring.

ReqID: N/A"""
        task = {'type': 'documentation', 'description':
            'Write technical documentation'}
        junior_doc = SimpleAgent(name='junior_doc', expertise=[
            'documentation', 'technical_writing'], experience_level=2)
        senior_doc = SimpleAgent(name='senior_doc', expertise=[
            'documentation', 'technical_writing'], experience_level=9)
        junior_score = self.team.enhanced_calculate_expertise_score(junior_doc,
            task)
        senior_score = self.team.enhanced_calculate_expertise_score(senior_doc,
            task)
        assert junior_score > 0
        assert senior_score > 0
        assert senior_score > junior_score

    @pytest.mark.medium
    def test_enhanced_calculate_expertise_score_performance_history_succeeds(
        self):
        """Test that past performance affects expertise scoring.

ReqID: N/A"""
        task = {'type': 'testing', 'description': 'Create automated tests'}
        good_tester = SimpleAgent(name='good_tester', expertise=['testing',
            'test_automation'], performance_history={'testing': 0.9})
        poor_tester = SimpleAgent(name='poor_tester', expertise=['testing',
            'test_automation'], performance_history={'testing': 0.5})
        good_score = self.team.enhanced_calculate_expertise_score(good_tester,
            task)
        poor_score = self.team.enhanced_calculate_expertise_score(poor_tester,
            task)
        assert good_score > 0
        assert poor_score > 0
        assert good_score > poor_score

    @pytest.mark.medium
    def test_enhanced_calculate_expertise_score_nested_task_succeeds(self):
        """Test enhanced expertise scoring with nested task structure.

ReqID: N/A"""
        task = {'type': 'security', 'details': {'requirements': [{
            'description': 'Implement authentication system'}, {
            'description': 'Use encryption for sensitive data'}]}}
        score = self.team.enhanced_calculate_expertise_score(self.
            security_agent, task)
        assert score > 0
        assert score > self.team.enhanced_calculate_expertise_score(self.
            python_agent, task)
        assert score > self.team.enhanced_calculate_expertise_score(self.
            doc_agent, task)
        assert score > self.team.enhanced_calculate_expertise_score(self.
            test_agent, task)

    @pytest.mark.medium
    def test_enhanced_calculate_phase_expertise_score_has_expected(self):
        """Test enhanced phase-specific expertise scoring.

ReqID: N/A"""
        task = {'type': 'code_generation', 'language': 'python'}
        expand_agent = SimpleAgent(name='expand_expert', expertise=[
            'python', 'brainstorming', 'idea_generation', 'exploration'])
        differentiate_agent = SimpleAgent(name='differentiate_expert',
            expertise=['python', 'analysis', 'comparison', 'critical_thinking']
            )
        expand_phase_keywords = ['exploration', 'brainstorming',
            'divergent thinking', 'idea generation']
        expand_score = self.team.enhanced_calculate_phase_expertise_score(
            expand_agent, task, expand_phase_keywords)
        differentiate_score = (self.team.
            enhanced_calculate_phase_expertise_score(differentiate_agent,
            task, expand_phase_keywords))
        differentiate_phase_keywords = ['analysis', 'comparison',
            'categorization', 'critical thinking']
        expand_score2 = self.team.enhanced_calculate_phase_expertise_score(
            expand_agent, task, differentiate_phase_keywords)
        differentiate_score2 = (self.team.
            enhanced_calculate_phase_expertise_score(differentiate_agent,
            task, differentiate_phase_keywords))
        assert expand_score > differentiate_score
        assert differentiate_score2 > expand_score2


class TestEnhancedPrimusSelection:
    """Test suite for enhanced primus selection.

ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name='test_team')
        self.python_agent = SimpleAgent(name='python_dev', expertise=[
            'python', 'code_generation', 'api_development'])
        self.doc_agent = SimpleAgent(name='doc_writer', expertise=[
            'documentation', 'technical_writing', 'markdown'])
        self.test_agent = SimpleAgent(name='tester', expertise=['testing',
            'test_automation', 'quality_assurance'])
        self.security_agent = SimpleAgent(name='security_expert', expertise
            =['security', 'authentication', 'encryption'])
        self.team.add_agents([self.python_agent, self.doc_agent, self.
            test_agent, self.security_agent])

    @pytest.mark.medium
    def test_enhanced_select_primus_by_expertise_code_task_succeeds(self):
        """Test enhanced primus selection for a code-related task.

ReqID: N/A"""
        task = {'type': 'code_generation', 'language': 'python'}
        selected_primus = self.team.enhanced_select_primus_by_expertise(task)
        assert selected_primus == self.python_agent
        assert selected_primus.has_been_primus
        assert self.team.get_primus() == self.python_agent

    @pytest.mark.medium
    def test_enhanced_select_primus_by_expertise_doc_task_succeeds(self):
        """Test enhanced primus selection for a documentation task.

ReqID: N/A"""
        task = {'type': 'documentation', 'description':
            'Write technical documentation'}
        selected_primus = self.team.enhanced_select_primus_by_expertise(task)
        assert selected_primus == self.doc_agent
        assert selected_primus.has_been_primus
        assert self.team.get_primus() == self.doc_agent

    @pytest.mark.medium
    def test_enhanced_select_primus_by_expertise_security_task_succeeds(self):
        """Test enhanced primus selection for a security task.

ReqID: N/A"""
        task = {'type': 'security', 'description':
            'Implement authentication system'}
        selected_primus = self.team.enhanced_select_primus_by_expertise(task)
        assert selected_primus == self.security_agent
        assert selected_primus.has_been_primus
        assert self.team.get_primus() == self.security_agent

    @pytest.mark.medium
    def test_enhanced_select_primus_by_expertise_rotation_succeeds(self):
        """Test that primus selection rotates after all agents have been primus.

ReqID: N/A"""
        for agent in self.team.agents:
            agent.has_been_primus = True
        task = {'type': 'code_generation', 'language': 'python'}
        selected_primus = self.team.enhanced_select_primus_by_expertise(task)
        assert selected_primus == self.python_agent
        assert not self.doc_agent.has_been_primus
        assert not self.test_agent.has_been_primus
        assert not self.security_agent.has_been_primus

    @pytest.mark.medium
    def test_enhanced_select_primus_by_expertise_unused_priority_succeeds(self
        ):
        """Test that unused agents are prioritized for primus selection.

ReqID: N/A"""
        self.python_agent.has_been_primus = True
        task = {'type': 'code_generation', 'language': 'python'}
        selected_primus = self.team.enhanced_select_primus_by_expertise(task)
        assert selected_primus != self.python_agent
        assert selected_primus.has_been_primus


class TestDynamicRoleReassignment:
    """Test suite for enhanced dynamic role reassignment.

ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name='test_team')
        self.python_agent = SimpleAgent(name='python_dev', expertise=[
            'python', 'code_generation', 'api_development'])
        self.doc_agent = SimpleAgent(name='doc_writer', expertise=[
            'documentation', 'technical_writing', 'markdown'])
        self.test_agent = SimpleAgent(name='tester', expertise=['testing',
            'test_automation', 'quality_assurance'])
        self.security_agent = SimpleAgent(name='security_expert', expertise
            =['security', 'authentication', 'encryption'])
        self.team.add_agents([self.python_agent, self.doc_agent, self.
            test_agent, self.security_agent])

    @pytest.mark.medium
    def test_dynamic_role_reassignment_enhanced_code_task_succeeds(self):
        """Test enhanced dynamic role reassignment for a code-related task.

ReqID: N/A"""
        task = {'type': 'code_generation', 'language': 'python'}
        roles = self.team.dynamic_role_reassignment_enhanced(task)
        assert roles['primus'] == self.python_agent
        assert self.python_agent.current_role == 'Primus'
        assert all(agent is not None for agent in roles.values())
        assigned_agents = set(roles.values())
        assert len(assigned_agents) == 4
        assert self.python_agent in assigned_agents
        assert self.doc_agent in assigned_agents
        assert self.test_agent in assigned_agents
        assert self.security_agent in assigned_agents

    @pytest.mark.medium
    def test_dynamic_role_reassignment_enhanced_doc_task_succeeds(self):
        """Test enhanced dynamic role reassignment for a documentation task.

ReqID: N/A"""
        task = {'type': 'documentation', 'description':
            'Write technical documentation'}
        roles = self.team.dynamic_role_reassignment_enhanced(task)
        assert roles['primus'] == self.doc_agent
        assert self.doc_agent.current_role == 'Primus'
        worker = roles['worker']
        assert worker is not None
        assert all(agent is not None for agent in roles.values())
        assigned_agents = set(roles.values())
        assert len(assigned_agents) == 4
        assert self.python_agent in assigned_agents
        assert self.doc_agent in assigned_agents
        assert self.test_agent in assigned_agents
        assert self.security_agent in assigned_agents

    @pytest.mark.medium
    def test_dynamic_role_reassignment_enhanced_testing_task_succeeds(self):
        """Test enhanced dynamic role reassignment for a testing task.

ReqID: N/A"""
        task = {'type': 'testing', 'description': 'Create automated tests'}
        roles = self.team.dynamic_role_reassignment_enhanced(task)
        assert roles['primus'] == self.test_agent
        assert self.test_agent.current_role == 'Primus'
        evaluator = roles['evaluator']
        assert evaluator is not None
        assert all(agent is not None for agent in roles.values())
        assigned_agents = set(roles.values())
        assert len(assigned_agents) == 4
        assert self.python_agent in assigned_agents
        assert self.doc_agent in assigned_agents
        assert self.test_agent in assigned_agents
        assert self.security_agent in assigned_agents

    @pytest.mark.medium
    def test_dynamic_role_reassignment_enhanced_security_task_succeeds(self):
        """Test enhanced dynamic role reassignment for a security task.

ReqID: N/A"""
        task = {'type': 'security', 'description':
            'Implement authentication system'}
        roles = self.team.dynamic_role_reassignment_enhanced(task)
        assert roles['primus'] == self.security_agent
        assert self.security_agent.current_role == 'Primus'
        assert all(agent is not None for agent in roles.values())
        assigned_agents = set(roles.values())
        assert len(assigned_agents) == 4
        assert self.python_agent in assigned_agents
        assert self.doc_agent in assigned_agents
        assert self.test_agent in assigned_agents
        assert self.security_agent in assigned_agents
