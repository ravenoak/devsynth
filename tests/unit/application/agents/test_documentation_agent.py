import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.application.agents.documentation import DocumentationAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestDocumentationAgent:
    """Unit tests for the DocumentationAgent class."""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated documentation"
        mock_port.generate_with_context.return_value = "Generated documentation with context"
        return mock_port

    @pytest.fixture
    def documentation_agent(self, mock_llm_port):
        """Create a DocumentationAgent instance for testing."""
        agent = DocumentationAgent()
        config = AgentConfig(
            name="TestDocumentationAgent",
            agent_type=AgentType.DOCUMENTATION,
            description="Test Documentation Agent",
            capabilities=[]  # Let the agent define its own capabilities
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization(self, documentation_agent):
        """Test that the agent initializes correctly."""
        assert documentation_agent.name == "TestDocumentationAgent"
        assert documentation_agent.agent_type == AgentType.DOCUMENTATION.value
        assert documentation_agent.description == "Test Documentation Agent"
        # Check that capabilities are set by the agent
        capabilities = documentation_agent.get_capabilities()
        assert "create_user_documentation" in capabilities
        assert "create_api_documentation" in capabilities
        assert "create_installation_guides" in capabilities
        assert "create_usage_examples" in capabilities
        assert "create_troubleshooting_guides" in capabilities

    def test_process(self, documentation_agent):
        """Test the process method."""
        # Create test inputs
        inputs = {
            "context": "This is a test project",
            "specifications": "Create documentation for a user authentication system",
            "code": "def authenticate(username, password): return True"
        }
        
        # Call the process method
        result = documentation_agent.process(inputs)
        
        # Check the result
        assert "documentation" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestDocumentationAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["documentation"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestDocumentationAgent"
        assert wsde.metadata["type"] == "documentation"

    def test_process_with_empty_inputs(self, documentation_agent):
        """Test the process method with empty inputs."""
        # Call the process method with empty inputs
        result = documentation_agent.process({})
        
        # Check the result
        assert "documentation" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestDocumentationAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["documentation"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestDocumentationAgent"
        assert wsde.metadata["type"] == "documentation"

    def test_get_capabilities(self, documentation_agent):
        """Test the get_capabilities method."""
        capabilities = documentation_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "create_user_documentation" in capabilities
        assert "create_api_documentation" in capabilities
        assert "create_installation_guides" in capabilities
        assert "create_usage_examples" in capabilities
        assert "create_troubleshooting_guides" in capabilities

    def test_get_capabilities_with_custom_capabilities(self):
        """Test the get_capabilities method with custom capabilities."""
        agent = DocumentationAgent()
        config = AgentConfig(
            name="TestDocumentationAgent",
            agent_type=AgentType.DOCUMENTATION,
            description="Test Documentation Agent",
            capabilities=["custom_capability"]
        )
        agent.initialize(config)
        
        # The agent should use the custom capabilities provided in the config
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "create_user_documentation" not in capabilities

    @patch("devsynth.application.agents.documentation.logger")
    def test_process_error_handling(self, mock_logger, documentation_agent):
        """Test error handling in the process method."""
        # Create a mock WSDE that raises an exception when created
        with patch.object(documentation_agent, 'create_wsde', side_effect=Exception("Test error")):
            # Call the process method
            result = documentation_agent.process({})
            
            # Check that an error was logged
            mock_logger.error.assert_called_once()
            
            # The method should still return a result, even if an error occurred
            assert "documentation" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestDocumentationAgent"
            
            # The WSDE should be None due to the error
            assert result.get("wsde") is None