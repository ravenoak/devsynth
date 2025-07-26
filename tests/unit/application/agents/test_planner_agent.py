import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from devsynth.application.agents.planner import PlannerAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestPlannerAgent:
    """Unit tests for the PlannerAgent class.

ReqID: N/A"""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = 'Generated development plan'
        mock_port.generate_with_context.return_value = (
            'Generated development plan with context')
        return mock_port

    @pytest.fixture
    def planner_agent(self, mock_llm_port):
        """Create a PlannerAgent instance for testing."""
        agent = PlannerAgent()
        config = AgentConfig(name='TestPlannerAgent', agent_type=AgentType.
            PLANNER, description='Test Planner Agent', capabilities=[])
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization_succeeds(self, planner_agent):
        """Test that the agent initializes correctly.

ReqID: N/A"""
        assert planner_agent.name == 'TestPlannerAgent'
        assert planner_agent.agent_type == AgentType.PLANNER.value
        assert planner_agent.description == 'Test Planner Agent'
        capabilities = planner_agent.get_capabilities()
        assert 'create_development_plan' in capabilities
        assert 'design_architecture' in capabilities
        assert 'define_implementation_phases' in capabilities
        assert 'create_testing_strategy' in capabilities
        assert 'create_deployment_plan' in capabilities

    def test_process_succeeds(self, planner_agent):
        """Test the process method.

ReqID: N/A"""
        inputs = {'context': 'This is a test project', 'requirements':
            'Create a user authentication system'}
        result = planner_agent.process(inputs)
        planner_agent.llm_port.generate.assert_called_once()
        assert 'plan' in result
        assert 'wsde' in result
        assert 'agent' in result
        assert 'role' in result
        assert result['agent'] == 'TestPlannerAgent'
        wsde = result['wsde']
        assert result['plan'] == 'Generated development plan'
        assert wsde.content == result['plan']
        assert wsde.content_type == 'text'
        assert wsde.metadata['agent'] == 'TestPlannerAgent'
        assert wsde.metadata['type'] == 'development_plan'

    def test_process_with_empty_inputs_succeeds(self, planner_agent):
        """Test the process method with empty inputs.

ReqID: N/A"""
        result = planner_agent.process({})
        planner_agent.llm_port.generate.assert_called()
        assert 'plan' in result
        assert 'wsde' in result
        assert 'agent' in result
        assert 'role' in result
        assert result['agent'] == 'TestPlannerAgent'
        wsde = result['wsde']
        assert wsde.content == result['plan']
        assert wsde.content_type == 'text'
        assert wsde.metadata['agent'] == 'TestPlannerAgent'
        assert wsde.metadata['type'] == 'development_plan'

    def test_get_capabilities_succeeds(self, planner_agent):
        """Test the get_capabilities method.

ReqID: N/A"""
        capabilities = planner_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert 'create_development_plan' in capabilities
        assert 'design_architecture' in capabilities
        assert 'define_implementation_phases' in capabilities
        assert 'create_testing_strategy' in capabilities
        assert 'create_deployment_plan' in capabilities

    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        """Test the get_capabilities method with custom capabilities.

ReqID: N/A"""
        agent = PlannerAgent()
        config = AgentConfig(name='TestPlannerAgent', agent_type=AgentType.
            PLANNER, description='Test Planner Agent', capabilities=[
            'custom_capability'])
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert 'custom_capability' in capabilities
        assert 'create_development_plan' not in capabilities

    @patch('devsynth.application.agents.planner.logger')
    def test_process_error_handling_raises_error(self, mock_logger,
        planner_agent):
        """Test error handling in the process method.

ReqID: N/A"""
        with patch.object(planner_agent, 'create_wsde', side_effect=
            Exception('Test error')):
            result = planner_agent.process({})
            mock_logger.error.assert_called_once()
            assert 'plan' in result
            assert 'agent' in result
            assert 'role' in result
            assert result['agent'] == 'TestPlannerAgent'
            assert result.get('wsde') is None
