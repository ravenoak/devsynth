import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.agents.test import TestAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort

class TestTestAgent:
    """Unit tests for the TestAgent class."""

    @pytest.fixture
    def mock_llm_port(self):
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = 'Generated tests'
        mock_port.generate_with_context.return_value = 'Generated tests with context'
        return mock_port

    @pytest.mark.medium
    @pytest.fixture
    def test_agent(self, mock_llm_port):
        agent = TestAgent()
        config = AgentConfig(name='TestTestAgent', agent_type=AgentType.TEST, description='Test Agent', capabilities=[])
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.medium
    def test_initialization_succeeds(self, test_agent):
        assert test_agent.name == 'TestTestAgent'
        assert test_agent.agent_type == AgentType.TEST.value
        assert test_agent.description == 'Test Agent'
        capabilities = test_agent.get_capabilities()
        assert 'create_bdd_features' in capabilities
        assert 'create_unit_tests' in capabilities
        assert 'create_integration_tests' in capabilities
        assert 'create_performance_tests' in capabilities
        assert 'create_security_tests' in capabilities

    @pytest.mark.medium
    def test_process_succeeds(self, test_agent):
        inputs = {'context': 'Sample project', 'specifications': 'Do something'}
        result = test_agent.process(inputs)
        test_agent.llm_port.generate.assert_called_once()
        assert 'tests' in result
        assert 'wsde' in result
        assert result['agent'] == 'TestTestAgent'
        wsde = result['wsde']
        assert result['tests'] == 'Generated tests'
        assert wsde.content == result['tests']
        assert wsde.content_type == 'text'
        assert wsde.metadata['agent'] == 'TestTestAgent'
        assert wsde.metadata['type'] == 'tests'

    @pytest.mark.medium
    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        agent = TestAgent()
        config = AgentConfig(name='CustomTestAgent', agent_type=AgentType.TEST, description='Test Agent', capabilities=['custom'])
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert capabilities == ['custom']

    @pytest.mark.medium
    @patch('devsynth.application.agents.test.logger')
    def test_process_error_handling(self, mock_logger, test_agent):
        with patch.object(test_agent, 'create_wsde', side_effect=Exception('err')):
            result = test_agent.process({})
            mock_logger.error.assert_called_once()
            assert 'tests' in result
            assert result.get('wsde') is None