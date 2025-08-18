from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.critic import CriticAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestCriticAgent:
    """Unit tests for the CriticAgent class.

    ReqID: N/A"""

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
            capabilities=[],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.medium
    def test_initialization_succeeds(self, critic_agent):
        """Test that the agent initializes correctly.

        ReqID: N/A"""
        assert critic_agent.name == "TestCriticAgent"
        assert critic_agent.agent_type == AgentType.CRITIC.value
        assert critic_agent.description == "Test Critic Agent"
        capabilities = critic_agent.get_capabilities()
        assert "apply_dialectical_methods" in capabilities
        assert "identify_assumptions" in capabilities
        assert "challenge_claims" in capabilities
        assert "propose_improvements" in capabilities
        assert "resolve_contradictions" in capabilities

    @pytest.mark.medium
    def test_process_succeeds(self, critic_agent, mock_llm_port):
        """Test the process method.

        ReqID: N/A"""
        inputs = {
            "context": "This is a test project",
            "content": "This is content to critique",
        }
        result = critic_agent.process(inputs)
        mock_llm_port.generate.assert_called_once()
        prompt = mock_llm_port.generate.call_args[0][0]
        assert "Project context:" in prompt
        assert "This is a test project" in prompt
        assert "Content to critique:" in prompt
        assert "This is content to critique" in prompt
        assert "Apply dialectical methods" in prompt
        assert "critique" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestCriticAgent"
        assert result["critique"] == "Generated critique"
        wsde = result["wsde"]
        assert wsde.content == "Generated critique"
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestCriticAgent"
        assert wsde.metadata["type"] == "critique"

    @pytest.mark.medium
    def test_process_with_empty_inputs_succeeds(self, critic_agent):
        """Test the process method with empty inputs.

        ReqID: N/A"""
        result = critic_agent.process({})
        assert "critique" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestCriticAgent"
        wsde = result["wsde"]
        assert wsde.content == result["critique"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestCriticAgent"
        assert wsde.metadata["type"] == "critique"

    @pytest.mark.medium
    def test_process_no_llm_port_succeeds(self):
        """Test the process method when no LLM port is set.

        ReqID: N/A"""
        agent = CriticAgent()
        config = AgentConfig(
            name="TestCriticAgent",
            agent_type=AgentType.CRITIC,
            description="Test Critic Agent",
            capabilities=[],
        )
        agent.initialize(config)
        with patch("devsynth.application.agents.critic.logger") as mock_logger:
            result = agent.process({"content": "Test content"})
            mock_logger.warning.assert_called_once()
            assert "critique" in result
            assert "wsde" in result
            assert "agent" in result
            assert "role" in result
            assert "Critique (created by TestCriticAgent" in result["critique"]

    @pytest.mark.medium
    def test_get_capabilities_succeeds(self, critic_agent):
        """Test the get_capabilities method.

        ReqID: N/A"""
        capabilities = critic_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "apply_dialectical_methods" in capabilities
        assert "identify_assumptions" in capabilities
        assert "challenge_claims" in capabilities
        assert "propose_improvements" in capabilities
        assert "resolve_contradictions" in capabilities

    @pytest.mark.medium
    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        """Test the get_capabilities method with custom capabilities.

        ReqID: N/A"""
        agent = CriticAgent()
        config = AgentConfig(
            name="TestCriticAgent",
            agent_type=AgentType.CRITIC,
            description="Test Critic Agent",
            capabilities=["custom_capability"],
        )
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "apply_dialectical_methods" not in capabilities

    @patch("devsynth.application.agents.critic.logger")
    @pytest.mark.medium
    def test_process_error_handling_raises_error(
        self, mock_logger, critic_agent, mock_llm_port
    ):
        """Test error handling in the process method.

        ReqID: N/A"""
        mock_llm_port.generate.side_effect = Exception("Test error")
        result = critic_agent.process({"content": "Test content"})
        mock_logger.error.assert_called_once()
        assert "critique" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert "Error generating critique" in result["critique"]
        wsde = result["wsde"]
        assert "Error generating critique" in wsde.content
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestCriticAgent"
        assert wsde.metadata["type"] == "critique"

    @patch("devsynth.application.agents.critic.logger")
    @pytest.mark.medium
    def test_create_wsde_error_fails(self, mock_logger, critic_agent):
        """Test error handling when creating a WSDE fails.

        ReqID: N/A"""
        with patch.object(
            critic_agent, "create_wsde", side_effect=Exception("Test error")
        ):
            result = critic_agent.process({"content": "Test content"})
            assert mock_logger.error.call_count >= 1
            assert "critique" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestCriticAgent"
            assert result.get("wsde") is None
