import pytest
from devsynth.domain.models.agent import AgentType, AgentConfig, MVP_CAPABILITIES


class TestAgentModels:
    """Tests for the AgentModels component.

ReqID: N/A"""

    def test_agent_type_enum_succeeds(self):
        """Test that agent type enum succeeds.

ReqID: N/A"""
        assert AgentType.ORCHESTRATOR.value == 'orchestrator'
        assert AgentType.PLANNER.value == 'planner'
        assert AgentType.CODER.value == 'coder'
        assert AgentType.TESTER.value == 'tester'
        assert AgentType.REVIEWER.value == 'reviewer'
        assert AgentType.DOCUMENTER.value == 'documenter'

    def test_agent_config_initialization_succeeds(self):
        """Test that agent config initialization succeeds.

ReqID: N/A"""
        agent_config = AgentConfig(name='TestAgent', agent_type=AgentType.
            ORCHESTRATOR, description='A test agent', capabilities=[
            'generate_specification', 'generate_code'])
        assert agent_config.name == 'TestAgent'
        assert agent_config.agent_type == AgentType.ORCHESTRATOR
        assert agent_config.description == 'A test agent'
        assert agent_config.capabilities == ['generate_specification',
            'generate_code']
        assert isinstance(agent_config.parameters, dict)
        assert len(agent_config.parameters) == 0

    def test_agent_config_with_parameters_succeeds(self):
        """Test that agent config with parameters succeeds.

ReqID: N/A"""
        custom_params = {'model': 'gpt-4', 'temperature': 0.7, 'max_tokens':
            1000}
        agent_config = AgentConfig(name='ParameterizedAgent', agent_type=
            AgentType.ORCHESTRATOR, description='An agent with parameters',
            capabilities=['generate_specification', 'generate_tests'],
            parameters=custom_params)
        assert agent_config.parameters == custom_params
        assert agent_config.parameters['model'] == 'gpt-4'
        assert agent_config.parameters['temperature'] == 0.7
        assert agent_config.parameters['max_tokens'] == 1000

    def test_mvp_capabilities_succeeds(self):
        """Test that mvp capabilities succeeds.

ReqID: N/A"""
        assert 'initialize_project' in MVP_CAPABILITIES
        assert 'parse_requirements' in MVP_CAPABILITIES
        assert 'generate_specification' in MVP_CAPABILITIES
        assert 'generate_tests' in MVP_CAPABILITIES
        assert 'generate_code' in MVP_CAPABILITIES
        assert 'validate_implementation' in MVP_CAPABILITIES
        assert 'track_token_usage' in MVP_CAPABILITIES
