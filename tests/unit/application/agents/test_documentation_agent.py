import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from devsynth.application.agents.documentation import DocumentationAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort

class TestDocumentationAgent:
    """Unit tests for the DocumentationAgent class.

ReqID: N/A"""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = 'Generated documentation'
        mock_port.generate_with_context.return_value = 'Generated documentation with context'
        return mock_port

    @pytest.fixture
    def documentation_agent(self, mock_llm_port):
        """Create a DocumentationAgent instance for testing."""
        agent = DocumentationAgent()
        config = AgentConfig(name='TestDocumentationAgent', agent_type=AgentType.DOCUMENTATION, description='Test Documentation Agent', capabilities=[])
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.medium
    def test_initialization_succeeds(self, documentation_agent):
        """Test that the agent initializes correctly.

ReqID: N/A"""
        assert documentation_agent.name == 'TestDocumentationAgent'
        assert documentation_agent.agent_type == AgentType.DOCUMENTATION.value
        assert documentation_agent.description == 'Test Documentation Agent'
        capabilities = documentation_agent.get_capabilities()
        assert 'create_user_documentation' in capabilities
        assert 'create_api_documentation' in capabilities
        assert 'create_installation_guides' in capabilities
        assert 'create_usage_examples' in capabilities
        assert 'create_troubleshooting_guides' in capabilities

    @pytest.mark.medium
    def test_process_succeeds(self, documentation_agent):
        """Test the process method.

ReqID: N/A"""
        inputs = {'context': 'This is a test project', 'specifications': 'Create documentation for a user authentication system', 'code': 'def authenticate(username, password): return True'}
        result = documentation_agent.process(inputs)
        documentation_agent.llm_port.generate.assert_called_once()
        assert 'documentation' in result
        assert 'wsde' in result
        assert 'agent' in result
        assert 'role' in result
        assert result['agent'] == 'TestDocumentationAgent'
        wsde = result['wsde']
        assert result['documentation'] == 'Generated documentation'
        assert wsde.content == result['documentation']
        assert wsde.content_type == 'text'
        assert wsde.metadata['agent'] == 'TestDocumentationAgent'
        assert wsde.metadata['type'] == 'documentation'

    @pytest.mark.medium
    def test_process_with_empty_inputs_succeeds(self, documentation_agent):
        """Test the process method with empty inputs.

ReqID: N/A"""
        result = documentation_agent.process({})
        documentation_agent.llm_port.generate.assert_called()
        assert 'documentation' in result
        assert 'wsde' in result
        assert 'agent' in result
        assert 'role' in result
        assert result['agent'] == 'TestDocumentationAgent'
        wsde = result['wsde']
        assert wsde.content == result['documentation']
        assert wsde.content_type == 'text'
        assert wsde.metadata['agent'] == 'TestDocumentationAgent'
        assert wsde.metadata['type'] == 'documentation'

    @pytest.mark.medium
    def test_get_capabilities_succeeds(self, documentation_agent):
        """Test the get_capabilities method.

ReqID: N/A"""
        capabilities = documentation_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert 'create_user_documentation' in capabilities
        assert 'create_api_documentation' in capabilities
        assert 'create_installation_guides' in capabilities
        assert 'create_usage_examples' in capabilities
        assert 'create_troubleshooting_guides' in capabilities

    @pytest.mark.medium
    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        """Test the get_capabilities method with custom capabilities.

ReqID: N/A"""
        agent = DocumentationAgent()
        config = AgentConfig(name='TestDocumentationAgent', agent_type=AgentType.DOCUMENTATION, description='Test Documentation Agent', capabilities=['custom_capability'])
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert 'custom_capability' in capabilities
        assert 'create_user_documentation' not in capabilities

    @pytest.mark.medium
    @patch('devsynth.application.agents.documentation.logger')
    def test_process_error_handling_raises_error(self, mock_logger, documentation_agent):
        """Test error handling in the process method.

ReqID: N/A"""
        with patch.object(documentation_agent, 'create_wsde', side_effect=Exception('Test error')):
            result = documentation_agent.process({})
            mock_logger.error.assert_called_once()
            assert 'documentation' in result
            assert 'agent' in result
            assert 'role' in result
            assert result['agent'] == 'TestDocumentationAgent'
            assert result.get('wsde') is None