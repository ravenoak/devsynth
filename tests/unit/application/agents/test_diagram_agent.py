import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.application.agents.diagram import DiagramAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestDiagramAgent:
    """Unit tests for the DiagramAgent class."""

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
            capabilities=[]  # Let the agent define its own capabilities
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization(self, diagram_agent):
        """Test that the agent initializes correctly."""
        assert diagram_agent.name == "TestDiagramAgent"
        assert diagram_agent.agent_type == AgentType.DIAGRAM.value
        assert diagram_agent.description == "Test Diagram Agent"
        # Check that capabilities are set by the agent
        capabilities = diagram_agent.get_capabilities()
        assert "create_architecture_diagrams" in capabilities
        assert "create_component_diagrams" in capabilities
        assert "create_sequence_diagrams" in capabilities
        assert "create_er_diagrams" in capabilities
        assert "create_state_diagrams" in capabilities

    def test_process(self, diagram_agent):
        """Test the process method."""
        # Create test inputs
        inputs = {
            "context": "This is a test project",
            "specifications": "Create diagrams for a user authentication system",
            "architecture": "Microservices architecture"
        }
        
        # Call the process method
        result = diagram_agent.process(inputs)
        
        # Check the result
        assert "diagrams" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestDiagramAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["diagrams"]
        assert wsde.content_type == "diagram"
        assert wsde.metadata["agent"] == "TestDiagramAgent"
        assert wsde.metadata["type"] == "diagrams"

    def test_process_with_empty_inputs(self, diagram_agent):
        """Test the process method with empty inputs."""
        # Call the process method with empty inputs
        result = diagram_agent.process({})
        
        # Check the result
        assert "diagrams" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestDiagramAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["diagrams"]
        assert wsde.content_type == "diagram"
        assert wsde.metadata["agent"] == "TestDiagramAgent"
        assert wsde.metadata["type"] == "diagrams"

    def test_get_capabilities(self, diagram_agent):
        """Test the get_capabilities method."""
        capabilities = diagram_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "create_architecture_diagrams" in capabilities
        assert "create_component_diagrams" in capabilities
        assert "create_sequence_diagrams" in capabilities
        assert "create_er_diagrams" in capabilities
        assert "create_state_diagrams" in capabilities

    def test_get_capabilities_with_custom_capabilities(self):
        """Test the get_capabilities method with custom capabilities."""
        agent = DiagramAgent()
        config = AgentConfig(
            name="TestDiagramAgent",
            agent_type=AgentType.DIAGRAM,
            description="Test Diagram Agent",
            capabilities=["custom_capability"]
        )
        agent.initialize(config)
        
        # The agent should use the custom capabilities provided in the config
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "create_architecture_diagrams" not in capabilities

    @patch("devsynth.application.agents.diagram.logger")
    def test_process_error_handling(self, mock_logger, diagram_agent):
        """Test error handling in the process method."""
        # Create a mock WSDE that raises an exception when created
        with patch.object(diagram_agent, 'create_wsde', side_effect=Exception("Test error")):
            # Call the process method
            result = diagram_agent.process({})
            
            # Check that an error was logged
            mock_logger.error.assert_called_once()
            
            # The method should still return a result, even if an error occurred
            assert "diagrams" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestDiagramAgent"
            
            # The WSDE should be None due to the error
            assert result.get("wsde") is None