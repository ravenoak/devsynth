from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.refactor import RefactorAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestRefactorAgent:
    """Unit tests for the RefactorAgent class.

    ReqID: N/A"""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated refactored code"
        mock_port.generate_with_context.return_value = (
            "Generated refactored code with context"
        )
        return mock_port

    @pytest.fixture
    def refactor_agent(self, mock_llm_port):
        """Create a RefactorAgent instance for testing."""
        agent = RefactorAgent()
        config = AgentConfig(
            name="TestRefactorAgent",
            agent_type=AgentType.REFACTOR,
            description="Test Refactor Agent",
            capabilities=[],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.medium
    def test_initialization_succeeds(self, refactor_agent):
        """Test that the agent initializes correctly.

        ReqID: N/A"""
        assert refactor_agent.name == "TestRefactorAgent"
        assert refactor_agent.agent_type == AgentType.REFACTOR.value
        assert refactor_agent.description == "Test Refactor Agent"
        capabilities = refactor_agent.get_capabilities()
        assert "refactor_code" in capabilities
        assert "improve_readability" in capabilities
        assert "improve_maintainability" in capabilities
        assert "optimize_performance" in capabilities
        assert "enhance_security" in capabilities
        assert "improve_testability" in capabilities

    @pytest.mark.medium
    def test_process_succeeds(self, refactor_agent):
        """Test the process method.

        ReqID: N/A"""
        inputs = {
            "context": "This is a test project",
            "code": "def add(a, b): return a + b",
            "validation_report": "The code is functional but could be improved",
        }
        result = refactor_agent.process(inputs)
        assert refactor_agent.llm_port.generate.call_count == 2
        assert result["refactored_code"] == "Generated refactored code"
        assert "refactored_code" in result
        assert "explanation" in result
        assert "code_wsde" in result
        assert "explanation_wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestRefactorAgent"
        code_wsde = result["code_wsde"]
        assert code_wsde.content == result["refactored_code"]
        assert code_wsde.content_type == "code"
        assert code_wsde.metadata["agent"] == "TestRefactorAgent"
        assert code_wsde.metadata["type"] == "refactored_code"
        explanation_wsde = result["explanation_wsde"]
        assert explanation_wsde.content == result["explanation"]
        assert explanation_wsde.content_type == "text"
        assert explanation_wsde.metadata["agent"] == "TestRefactorAgent"
        assert explanation_wsde.metadata["type"] == "refactor_explanation"

    @pytest.mark.medium
    def test_process_with_empty_inputs_succeeds(self, refactor_agent):
        """Test the process method with empty inputs.

        ReqID: N/A"""
        result = refactor_agent.process({})
        assert refactor_agent.llm_port.generate.call_count >= 2
        assert result["refactored_code"] == "Generated refactored code"
        assert "refactored_code" in result
        assert "explanation" in result
        assert "code_wsde" in result
        assert "explanation_wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestRefactorAgent"
        code_wsde = result["code_wsde"]
        assert code_wsde.content == result["refactored_code"]
        assert code_wsde.content_type == "code"
        assert code_wsde.metadata["agent"] == "TestRefactorAgent"
        assert code_wsde.metadata["type"] == "refactored_code"
        explanation_wsde = result["explanation_wsde"]
        assert explanation_wsde.content == result["explanation"]
        assert explanation_wsde.content_type == "text"
        assert explanation_wsde.metadata["agent"] == "TestRefactorAgent"
        assert explanation_wsde.metadata["type"] == "refactor_explanation"

    @pytest.mark.medium
    def test_get_capabilities_succeeds(self, refactor_agent):
        """Test the get_capabilities method.

        ReqID: N/A"""
        capabilities = refactor_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 6
        assert "refactor_code" in capabilities
        assert "improve_readability" in capabilities
        assert "improve_maintainability" in capabilities
        assert "optimize_performance" in capabilities
        assert "enhance_security" in capabilities
        assert "improve_testability" in capabilities

    @pytest.mark.medium
    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        """Test the get_capabilities method with custom capabilities.

        ReqID: N/A"""
        agent = RefactorAgent()
        config = AgentConfig(
            name="TestRefactorAgent",
            agent_type=AgentType.REFACTOR,
            description="Test Refactor Agent",
            capabilities=["custom_capability"],
        )
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "refactor_code" not in capabilities

    @patch("devsynth.application.agents.refactor.logger")
    @pytest.mark.medium
    def test_process_error_handling_code_wsde_fails(self, mock_logger, refactor_agent):
        """Test error handling in the process method when creating code WSDE fails.

        ReqID: N/A"""
        side_effects = [Exception("Test error"), MagicMock()]
        with patch.object(refactor_agent, "create_wsde", side_effect=side_effects):
            result = refactor_agent.process({})
            mock_logger.error.assert_called_once()
            assert "refactored_code" in result
            assert "explanation" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestRefactorAgent"
            assert result.get("code_wsde") is None
            assert result.get("explanation_wsde") is not None

    @patch("devsynth.application.agents.refactor.logger")
    @pytest.mark.medium
    def test_process_error_handling_explanation_wsde_fails(
        self, mock_logger, refactor_agent
    ):
        """Test error handling in the process method when creating explanation WSDE fails.

        ReqID: N/A"""
        side_effects = [MagicMock(), Exception("Test error")]
        with patch.object(refactor_agent, "create_wsde", side_effect=side_effects):
            result = refactor_agent.process({})
            mock_logger.error.assert_called_once()
            assert "refactored_code" in result
            assert "explanation" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestRefactorAgent"
            assert result.get("code_wsde") is not None
            assert result.get("explanation_wsde") is None
