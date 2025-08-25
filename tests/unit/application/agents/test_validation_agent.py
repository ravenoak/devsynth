from unittest.mock import MagicMock

import pytest

from devsynth.application.agents.validation import ValidationAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestValidationAgent:

    @pytest.fixture
    def mock_llm_port(self):
        port = MagicMock(spec=LLMPort)
        port.generate.return_value = "All tests pass"
        port.generate_with_context.return_value = "All tests pass"
        return port

    @pytest.fixture
    def validation_agent(self, mock_llm_port):
        agent = ValidationAgent()
        config = AgentConfig(
            name="TestValidationAgent",
            agent_type=AgentType.VALIDATION,
            description="Test Validation Agent",
            capabilities=[],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.medium
    def test_process_succeeds(self, validation_agent):
        inputs = {
            "context": "ctx",
            "specifications": "spec",
            "tests": "tests",
            "code": "code",
        }
        result = validation_agent.process(inputs)
        validation_agent.llm_port.generate.assert_called_once()
        assert result["validation_report"] == "All tests pass"
        assert result["is_valid"] is True
        wsde = result["wsde"]
        assert wsde.content == result["validation_report"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestValidationAgent"
        assert wsde.metadata["type"] == "validation_report"
