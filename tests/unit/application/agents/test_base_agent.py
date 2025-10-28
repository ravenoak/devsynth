from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.base import BaseAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestBaseAgent:
    """Unit tests for the BaseAgent class.

    ReqID: N/A"""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated text"
        mock_port.generate_with_context.return_value = "Generated text with context"
        return mock_port

    @pytest.fixture
    def base_agent(self, mock_llm_port):
        """Create a BaseAgent instance for testing."""

        class ConcreteAgent(BaseAgent):

            def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
                return {"result": "Processed " + str(inputs.get("input", ""))}

        agent = ConcreteAgent()
        config = AgentConfig(
            name="TestAgent",
            agent_type=AgentType.ORCHESTRATOR,
            description="Test Agent",
            capabilities=["test", "example"],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.fast
    def test_initialization_succeeds(self, base_agent):
        """Test that the agent initializes correctly.

        ReqID: N/A"""
        assert base_agent.name == "TestAgent"
        assert base_agent.agent_type == AgentType.ORCHESTRATOR.value
        assert base_agent.description == "Test Agent"
        assert base_agent.get_capabilities() == ["test", "example"]

    @pytest.mark.fast
    def test_generate_text_succeeds(self, base_agent, mock_llm_port):
        """Test the generate_text method.

        ReqID: N/A"""
        result = base_agent.generate_text("Test prompt")
        mock_llm_port.generate.assert_called_once_with("Test prompt", None)
        assert result == "Generated text"

    @pytest.mark.fast
    def test_generate_text_with_context_succeeds(self, base_agent, mock_llm_port):
        """Test the generate_text_with_context method.

        ReqID: N/A"""
        context = [{"role": "user", "content": "Hello"}]
        result = base_agent.generate_text_with_context("Test prompt", context)
        mock_llm_port.generate_with_context.assert_called_once_with(
            "Test prompt", context, None
        )
        assert result == "Generated text with context"

    @pytest.mark.fast
    def test_generate_text_no_llm_port_succeeds(self):
        """Test generate_text when no LLM port is set.

        ReqID: N/A"""

        class ConcreteAgent(BaseAgent):

            def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
                return {"result": "Processed"}

        agent = ConcreteAgent()
        result = agent.generate_text("Test prompt")
        assert "Placeholder text for prompt" in result

    @pytest.mark.fast
    def test_generate_text_with_context_no_llm_port_succeeds(self):
        """Test generate_text_with_context when no LLM port is set.

        ReqID: N/A"""

        class ConcreteAgent(BaseAgent):

            def process(self, inputs: dict[str, Any]) -> dict[str, Any]:
                return {"result": "Processed"}

        agent = ConcreteAgent()
        context = [{"role": "user", "content": "Hello"}]
        result = agent.generate_text_with_context("Test prompt", context)
        assert "Placeholder text for prompt with context" in result

    @pytest.mark.fast
    def test_process_abstract_method_succeeds(self):
        """Test that the process method is abstract and must be implemented.

        ReqID: N/A"""
        with pytest.raises(TypeError):
            BaseAgent()

    @pytest.mark.fast
    def test_create_wsde_succeeds(self, base_agent):
        """Test the create_wsde method.

        ReqID: N/A"""
        wsde = base_agent.create_wsde("Test content", "text", {"key": "value"})
        assert wsde.content == "Test content"
        assert wsde.content_type == "text"
        assert wsde.metadata == {"key": "value"}

    @pytest.mark.fast
    def test_update_wsde_succeeds(self, base_agent):
        """Test the update_wsde method.

        ReqID: N/A"""
        wsde = base_agent.create_wsde("Initial content", "text", {"key": "value"})
        updated_wsde = base_agent.update_wsde(
            wsde, "Updated content", {"new_key": "new_value"}
        )
        assert updated_wsde.content == "Updated content"
        assert updated_wsde.metadata == {"key": "value", "new_key": "new_value"}

    @pytest.mark.fast
    def test_get_role_prompt_succeeds(self, base_agent):
        """Test the get_role_prompt method.

        ReqID: N/A"""
        base_agent.current_role = "Worker"
        assert "Worker" in base_agent.get_role_prompt()
        base_agent.current_role = "Supervisor"
        assert "Supervisor" in base_agent.get_role_prompt()
        base_agent.current_role = "Designer"
        assert "Designer" in base_agent.get_role_prompt()
        base_agent.current_role = "Evaluator"
        assert "Evaluator" in base_agent.get_role_prompt()
        base_agent.current_role = "Primus"
        assert "Primus" in base_agent.get_role_prompt()
        base_agent.current_role = "Unknown"
        assert base_agent.get_role_prompt() == ""

    @patch("devsynth.application.agents.base.logger")
    @pytest.mark.fast
    def test_generate_text_error_raises_error(
        self, mock_logger, base_agent, mock_llm_port
    ):
        """Test error handling in generate_text.

        ReqID: N/A"""
        mock_llm_port.generate.side_effect = Exception("Test error")
        result = base_agent.generate_text("Test prompt")
        assert "Error generating text" in result
        mock_logger.error.assert_called_once()

    @patch("devsynth.application.agents.base.logger")
    @pytest.mark.fast
    def test_generate_text_with_context_error_raises_error(
        self, mock_logger, base_agent, mock_llm_port
    ):
        """Test error handling in generate_text_with_context.

        ReqID: N/A"""
        mock_llm_port.generate_with_context.side_effect = Exception("Test error")
        context = [{"role": "user", "content": "Hello"}]
        result = base_agent.generate_text_with_context("Test prompt", context)
        assert "Error generating text with context" in result
        mock_logger.error.assert_called_once()
