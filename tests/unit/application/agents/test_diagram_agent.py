from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.diagram import DiagramAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestDiagramAgent:
    """Unit tests for the DiagramAgent class.

    ReqID: N/A"""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated diagrams"
        mock_port.generate_with_context.return_value = "Generated diagrams with context"
        return mock_port

    @pytest.fixture
    def diagram_agent(self, mock_llm_port):
        """Create a DiagramAgent instance for testing."""
        agent = DiagramAgent()
        config = AgentConfig(
            name="TestDiagramAgent",
            agent_type=AgentType.DIAGRAM,
            description="Test Diagram Agent",
            capabilities=[],
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    @pytest.mark.medium
    def test_initialization_succeeds(self, diagram_agent):
        """Test that the agent initializes correctly.

        ReqID: N/A"""
        assert diagram_agent.name == "TestDiagramAgent"
        assert diagram_agent.agent_type == AgentType.DIAGRAM.value
        assert diagram_agent.description == "Test Diagram Agent"
        capabilities = diagram_agent.get_capabilities()
        assert "create_architecture_diagrams" in capabilities
        assert "create_component_diagrams" in capabilities
        assert "create_sequence_diagrams" in capabilities
        assert "create_er_diagrams" in capabilities
        assert "create_state_diagrams" in capabilities

    @pytest.mark.medium
    def test_process_succeeds(self, diagram_agent):
        """Test the process method.

        ReqID: N/A"""
        inputs = {
            "context": "This is a test project",
            "specifications": "Create diagrams for a user authentication system",
            "architecture": "Microservices architecture",
        }
        result = diagram_agent.process(inputs)
        diagram_agent.llm_port.generate.assert_called_once()
        assert "diagrams" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestDiagramAgent"
        wsde = result["wsde"]
        assert result["diagrams"] == "Generated diagrams"
        assert wsde.content == result["diagrams"]
        assert wsde.content_type == "diagram"
        assert wsde.metadata["agent"] == "TestDiagramAgent"
        assert wsde.metadata["type"] == "diagrams"

    @pytest.mark.medium
    def test_process_with_empty_inputs_succeeds(self, diagram_agent):
        """Test the process method with empty inputs.

        ReqID: N/A"""
        result = diagram_agent.process({})
        diagram_agent.llm_port.generate.assert_called()
        assert "diagrams" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestDiagramAgent"
        wsde = result["wsde"]
        assert wsde.content == result["diagrams"]
        assert wsde.content_type == "diagram"
        assert wsde.metadata["agent"] == "TestDiagramAgent"
        assert wsde.metadata["type"] == "diagrams"

    @pytest.mark.medium
    def test_get_capabilities_succeeds(self, diagram_agent):
        """Test the get_capabilities method.

        ReqID: N/A"""
        capabilities = diagram_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "create_architecture_diagrams" in capabilities
        assert "create_component_diagrams" in capabilities
        assert "create_sequence_diagrams" in capabilities
        assert "create_er_diagrams" in capabilities
        assert "create_state_diagrams" in capabilities

    @pytest.mark.medium
    def test_get_capabilities_with_custom_capabilities_succeeds(self):
        """Test the get_capabilities method with custom capabilities.

        ReqID: N/A"""
        agent = DiagramAgent()
        config = AgentConfig(
            name="TestDiagramAgent",
            agent_type=AgentType.DIAGRAM,
            description="Test Diagram Agent",
            capabilities=["custom_capability"],
        )
        agent.initialize(config)
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "create_architecture_diagrams" not in capabilities

    @patch("devsynth.application.agents.diagram.logger")
    @pytest.mark.medium
    def test_process_error_handling_raises_error(self, mock_logger, diagram_agent):
        """Test error handling in the process method.

        ReqID: N/A"""
        with patch.object(
            diagram_agent, "create_wsde", side_effect=Exception("Test error")
        ):
            result = diagram_agent.process({})
            mock_logger.error.assert_called_once()
            assert "diagrams" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestDiagramAgent"
            assert result.get("wsde") is None
