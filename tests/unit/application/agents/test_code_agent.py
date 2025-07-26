import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from devsynth.application.agents.code import CodeAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestCodeAgent:
    """Unit tests for the CodeAgent class.

ReqID: N/A"""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = 'Generated code'
        mock_port.generate_with_context.return_value = (
            'Generated code with context')
        return mock_port

    @pytest.fixture
    def code_agent(self, mock_llm_port):
        """Create a CodeAgent instance for testing."""
        agent = CodeAgent()
        config = AgentConfig(name='TestCodeAgent', agent_type=AgentType.
            CODE, description='Test Code Agent', capabilities=[])
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization_succeeds(self, code_agent):
        """Test that the agent initializes correctly.

ReqID: N/A"""
        assert code_agent.name == 'TestCodeAgent'
        assert code_agent.agent_type == AgentType.CODE.value
        assert code_agent.description == 'Test Code Agent'
        capabilities = code_agent.get_capabilities()
        assert 'implement_code' in capabilities
        assert 'refactor_code' in capabilities
        assert 'optimize_code' in capabilities
        assert 'debug_code' in capabilities
        assert 'implement_apis' in capabilities

    def test_process_succeeds(self, code_agent):
        """Test the process method.

ReqID: N/A"""
        inputs = {'context': 'This is a test project', 'specifications':
            'Implement a function that adds two numbers', 'tests':
            'def test_add(): assert add(1, 2) == 3'}
        result = code_agent.process(inputs)
        code_agent.llm_port.generate.assert_called_once()
        assert 'code' in result
        assert 'wsde' in result
        assert 'agent' in result
        assert 'role' in result
        assert result['agent'] == 'TestCodeAgent'
        wsde = result['wsde']
        assert result['code'] == 'Generated code'
        assert wsde.content == result['code']
        assert wsde.content_type == 'code'
        assert wsde.metadata['agent'] == 'TestCodeAgent'
        assert wsde.metadata['type'] == 'code'

    def test_process_with_empty_inputs_succeeds(self, code_agent):
        """Test the process method with empty inputs.

ReqID: N/A"""
        result = code_agent.process({})
        code_agent.llm_port.generate.assert_called()
        assert 'code' in result
        assert 'wsde' in result
        assert 'agent' in result
        assert 'role' in result
        assert result['agent'] == 'TestCodeAgent'
        wsde = result['wsde']
        assert wsde.content == result['code']
        assert wsde.content_type == 'code'
        assert wsde.metadata['agent'] == 'TestCodeAgent'
        assert wsde.metadata['type'] == 'code'

    def test_get_capabilities_succeeds(self, code_agent):
        """Test the get_capabilities method.

ReqID: N/A"""
        capabilities = code_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert 'implement_code' in capabilities
        assert 'refactor_code' in capabilities
        assert 'optimize_code' in capabilities
        assert 'debug_code' in capabilities
        assert 'implement_apis' in capabilities

    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        """Test the get_capabilities method with custom capabilities.

ReqID: N/A"""
        agent = CodeAgent()
        config = AgentConfig(name='TestCodeAgent', agent_type=AgentType.
            CODE, description='Test Code Agent', capabilities=[
            'custom_capability'])
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert 'custom_capability' in capabilities
        assert 'implement_code' not in capabilities

    @patch('devsynth.application.agents.code.logger')
    def test_process_error_handling_raises_error(self, mock_logger, code_agent
        ):
        """Test error handling in the process method.

ReqID: N/A"""
        with patch.object(code_agent, 'create_wsde', side_effect=Exception(
            'Test error')):
            result = code_agent.process({})
            mock_logger.error.assert_called_once()
            assert 'code' in result
            assert 'agent' in result
            assert 'role' in result
            assert result['agent'] == 'TestCodeAgent'
            assert result.get('wsde') is None
