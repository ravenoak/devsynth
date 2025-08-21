from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.test import TestAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestTestAgent:
    """Unit tests for the TestAgent class."""

    @pytest.fixture
    def mock_llm_port(self):
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated tests"
        mock_port.generate_with_context.return_value = "Generated tests with context"
        return mock_port

    @pytest.fixture
    @pytest.mark.medium
    def agent(self, mock_llm_port):
        agent = TestAgent()
        config = AgentConfig(
            name="TestTestAgent",
            agent_type=AgentType.TEST,
            description="Test Agent",
            capabilities=[],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.medium
    def test_initialization_succeeds(self, agent):
        assert agent.name == "TestTestAgent"
        assert agent.agent_type == AgentType.TEST.value
        assert agent.description == "Test Agent"
        capabilities = agent.get_capabilities()
        assert "create_bdd_features" in capabilities
        assert "create_unit_tests" in capabilities
        assert "create_integration_tests" in capabilities
        assert "create_performance_tests" in capabilities
        assert "create_security_tests" in capabilities

    @pytest.mark.medium
    def test_process_succeeds(self, agent):
        inputs = {"context": "Sample project", "specifications": "Do something"}
        result = agent.process(inputs)
        agent.llm_port.generate.assert_called_once()
        assert "tests" in result
        assert "wsde" in result
        assert result["agent"] == "TestTestAgent"
        wsde = result["wsde"]
        assert result["tests"] == "Generated tests"
        assert wsde.content == result["tests"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestTestAgent"
        assert wsde.metadata["type"] == "tests"

    @pytest.mark.medium
    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        agent = TestAgent()
        config = AgentConfig(
            name="CustomTestAgent",
            agent_type=AgentType.TEST,
            description="Test Agent",
            capabilities=["custom"],
        )
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert capabilities == ["custom"]

    @patch("devsynth.application.agents.test.logger")
    @pytest.mark.medium
    def test_process_error_handling(self, mock_logger, agent):
        with patch.object(agent, "create_wsde", side_effect=Exception("err")):
            result = agent.process({})
            mock_logger.error.assert_called_once()
            assert "tests" in result
            assert result.get("wsde") is None
