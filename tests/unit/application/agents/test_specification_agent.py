import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.agents.specification import SpecificationAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestSpecificationAgent:
    @pytest.fixture
    def mock_llm_port(self):
        port = MagicMock(spec=LLMPort)
        port.generate.return_value = "Generated specifications"
        port.generate_with_context.return_value = "Generated specifications with context"
        return port

    @pytest.fixture
    def specification_agent(self, mock_llm_port):
        agent = SpecificationAgent()
        config = AgentConfig(
            name="TestSpecificationAgent",
            agent_type=AgentType.SPECIFICATION,
            description="Test Specification Agent",
            capabilities=[],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_process_succeeds(self, specification_agent):
        inputs = {"context": "ctx", "requirements": "reqs"}
        result = specification_agent.process(inputs)
        specification_agent.llm_port.generate.assert_called_once()
        assert result["specifications"] == "Generated specifications"
        wsde = result["wsde"]
        assert wsde.content == result["specifications"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestSpecificationAgent"
        assert wsde.metadata["type"] == "specifications"

    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        agent = SpecificationAgent()
        config = AgentConfig(
            name="TestSpecificationAgent",
            agent_type=AgentType.SPECIFICATION,
            description="Test",
            capabilities=["custom"],
        )
        agent.initialize(config)
        assert agent.get_capabilities() == ["custom"]
