import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.application.agents.code import CodeAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestCodeAgent:
    """Unit tests for the CodeAgent class."""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated code"
        mock_port.generate_with_context.return_value = "Generated code with context"
        return mock_port

    @pytest.fixture
    def code_agent(self, mock_llm_port):
        """Create a CodeAgent instance for testing."""
        agent = CodeAgent()
        config = AgentConfig(
            name="TestCodeAgent",
            agent_type=AgentType.CODE,
            description="Test Code Agent",
            capabilities=[]  # Let the agent define its own capabilities
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization(self, code_agent):
        """Test that the agent initializes correctly."""
        assert code_agent.name == "TestCodeAgent"
        assert code_agent.agent_type == AgentType.CODE.value
        assert code_agent.description == "Test Code Agent"
        # Check that capabilities are set by the agent
        capabilities = code_agent.get_capabilities()
        assert "implement_code" in capabilities
        assert "refactor_code" in capabilities
        assert "optimize_code" in capabilities
        assert "debug_code" in capabilities
        assert "implement_apis" in capabilities

    def test_process(self, code_agent):
        """Test the process method."""
        # Create test inputs
        inputs = {
            "context": "This is a test project",
            "specifications": "Implement a function that adds two numbers",
            "tests": "def test_add(): assert add(1, 2) == 3"
        }
        
        # Call the process method
        result = code_agent.process(inputs)
        
        # Check the result
        assert "code" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestCodeAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["code"]
        assert wsde.content_type == "code"
        assert wsde.metadata["agent"] == "TestCodeAgent"
        assert wsde.metadata["type"] == "code"

    def test_process_with_empty_inputs(self, code_agent):
        """Test the process method with empty inputs."""
        # Call the process method with empty inputs
        result = code_agent.process({})
        
        # Check the result
        assert "code" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestCodeAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["code"]
        assert wsde.content_type == "code"
        assert wsde.metadata["agent"] == "TestCodeAgent"
        assert wsde.metadata["type"] == "code"

    def test_get_capabilities(self, code_agent):
        """Test the get_capabilities method."""
        capabilities = code_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "implement_code" in capabilities
        assert "refactor_code" in capabilities
        assert "optimize_code" in capabilities
        assert "debug_code" in capabilities
        assert "implement_apis" in capabilities

    def test_get_capabilities_with_custom_capabilities(self):
        """Test the get_capabilities method with custom capabilities."""
        agent = CodeAgent()
        config = AgentConfig(
            name="TestCodeAgent",
            agent_type=AgentType.CODE,
            description="Test Code Agent",
            capabilities=["custom_capability"]
        )
        agent.initialize(config)
        
        # The agent should use the custom capabilities provided in the config
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "implement_code" not in capabilities

    @patch("devsynth.application.agents.code.logger")
    def test_process_error_handling(self, mock_logger, code_agent):
        """Test error handling in the process method."""
        # Create a mock WSDE that raises an exception when created
        with patch.object(code_agent, 'create_wsde', side_effect=Exception("Test error")):
            # Call the process method
            result = code_agent.process({})
            
            # Check that an error was logged
            mock_logger.error.assert_called_once()
            
            # The method should still return a result, even if an error occurred
            assert "code" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestCodeAgent"
            
            # The WSDE should be None due to the error
            assert result.get("wsde") is None