import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.application.agents.critic import CriticAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestCriticAgent:
    """Unit tests for the CriticAgent class."""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated critique"
        mock_port.generate_with_context.return_value = "Generated critique with context"
        return mock_port

    @pytest.fixture
    def critic_agent(self, mock_llm_port):
        """Create a CriticAgent instance for testing."""
        agent = CriticAgent()
        config = AgentConfig(
            name="TestCriticAgent",
            agent_type=AgentType.CRITIC,
            description="Test Critic Agent",
            capabilities=[]  # Let the agent define its own capabilities
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization(self, critic_agent):
        """Test that the agent initializes correctly."""
        assert critic_agent.name == "TestCriticAgent"
        assert critic_agent.agent_type == AgentType.CRITIC.value
        assert critic_agent.description == "Test Critic Agent"
        # Check that capabilities are set by the agent
        capabilities = critic_agent.get_capabilities()
        assert "apply_dialectical_methods" in capabilities
        assert "identify_assumptions" in capabilities
        assert "challenge_claims" in capabilities
        assert "propose_improvements" in capabilities
        assert "resolve_contradictions" in capabilities

    def test_process(self, critic_agent, mock_llm_port):
        """Test the process method."""
        # Create test inputs
        inputs = {
            "context": "This is a test project",
            "content": "This is content to critique"
        }
        
        # Call the process method
        result = critic_agent.process(inputs)
        
        # Check that the LLM port was called with the correct prompt
        mock_llm_port.generate.assert_called_once()
        prompt = mock_llm_port.generate.call_args[0][0]
        assert "Project context:" in prompt
        assert "This is a test project" in prompt
        assert "Content to critique:" in prompt
        assert "This is content to critique" in prompt
        assert "Apply dialectical methods" in prompt
        
        # Check the result
        assert "critique" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestCriticAgent"
        assert result["critique"] == "Generated critique"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == "Generated critique"
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestCriticAgent"
        assert wsde.metadata["type"] == "critique"

    def test_process_with_empty_inputs(self, critic_agent):
        """Test the process method with empty inputs."""
        # Call the process method with empty inputs
        result = critic_agent.process({})
        
        # Check the result
        assert "critique" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestCriticAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["critique"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestCriticAgent"
        assert wsde.metadata["type"] == "critique"

    def test_process_no_llm_port(self):
        """Test the process method when no LLM port is set."""
        # Create an agent without an LLM port
        agent = CriticAgent()
        config = AgentConfig(
            name="TestCriticAgent",
            agent_type=AgentType.CRITIC,
            description="Test Critic Agent",
            capabilities=[]
        )
        agent.initialize(config)
        
        # Call the process method
        with patch("devsynth.application.agents.critic.logger") as mock_logger:
            result = agent.process({"content": "Test content"})
            
            # Check that a warning was logged
            mock_logger.warning.assert_called_once()
            
            # Check the result
            assert "critique" in result
            assert "wsde" in result
            assert "agent" in result
            assert "role" in result
            assert "Critique (created by TestCriticAgent" in result["critique"]

    def test_get_capabilities(self, critic_agent):
        """Test the get_capabilities method."""
        capabilities = critic_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "apply_dialectical_methods" in capabilities
        assert "identify_assumptions" in capabilities
        assert "challenge_claims" in capabilities
        assert "propose_improvements" in capabilities
        assert "resolve_contradictions" in capabilities

    def test_get_capabilities_with_custom_capabilities(self):
        """Test the get_capabilities method with custom capabilities."""
        agent = CriticAgent()
        config = AgentConfig(
            name="TestCriticAgent",
            agent_type=AgentType.CRITIC,
            description="Test Critic Agent",
            capabilities=["custom_capability"]
        )
        agent.initialize(config)
        
        # The agent should use the custom capabilities provided in the config
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "apply_dialectical_methods" not in capabilities

    @patch("devsynth.application.agents.critic.logger")
    def test_process_error_handling(self, mock_logger, critic_agent, mock_llm_port):
        """Test error handling in the process method."""
        # Make the LLM port raise an exception
        mock_llm_port.generate.side_effect = Exception("Test error")
        
        # Call the process method
        result = critic_agent.process({"content": "Test content"})
        
        # Check that an error was logged
        mock_logger.error.assert_called_once()
        
        # The method should still return a result, even if an error occurred
        assert "critique" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert "Error generating critique" in result["critique"]
        
        # Check that the WSDE was created with the error message
        wsde = result["wsde"]
        assert "Error generating critique" in wsde.content
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestCriticAgent"
        assert wsde.metadata["type"] == "critique"

    @patch("devsynth.application.agents.critic.logger")
    def test_create_wsde_error(self, mock_logger, critic_agent):
        """Test error handling when creating a WSDE fails."""
        # Create a mock WSDE that raises an exception when created
        with patch.object(critic_agent, 'create_wsde', side_effect=Exception("Test error")):
            # Call the process method
            result = critic_agent.process({"content": "Test content"})
            
            # Check that an error was logged
            assert mock_logger.error.call_count >= 1
            
            # The method should still return a result, even if an error occurred
            assert "critique" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestCriticAgent"
            
            # The WSDE should be None due to the error
            assert result.get("wsde") is None