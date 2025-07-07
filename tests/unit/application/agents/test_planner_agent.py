import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.application.agents.planner import PlannerAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestPlannerAgent:
    """Unit tests for the PlannerAgent class."""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated development plan"
        mock_port.generate_with_context.return_value = "Generated development plan with context"
        return mock_port

    @pytest.fixture
    def planner_agent(self, mock_llm_port):
        """Create a PlannerAgent instance for testing."""
        agent = PlannerAgent()
        config = AgentConfig(
            name="TestPlannerAgent",
            agent_type=AgentType.PLANNER,
            description="Test Planner Agent",
            capabilities=[]  # Let the agent define its own capabilities
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization(self, planner_agent):
        """Test that the agent initializes correctly."""
        assert planner_agent.name == "TestPlannerAgent"
        assert planner_agent.agent_type == AgentType.PLANNER.value
        assert planner_agent.description == "Test Planner Agent"
        # Check that capabilities are set by the agent
        capabilities = planner_agent.get_capabilities()
        assert "create_development_plan" in capabilities
        assert "design_architecture" in capabilities
        assert "define_implementation_phases" in capabilities
        assert "create_testing_strategy" in capabilities
        assert "create_deployment_plan" in capabilities

    def test_process(self, planner_agent):
        """Test the process method."""
        # Create test inputs
        inputs = {
            "context": "This is a test project",
            "requirements": "Create a user authentication system"
        }
        
        # Call the process method
        result = planner_agent.process(inputs)
        
        # Check the result
        assert "plan" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestPlannerAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["plan"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestPlannerAgent"
        assert wsde.metadata["type"] == "development_plan"

    def test_process_with_empty_inputs(self, planner_agent):
        """Test the process method with empty inputs."""
        # Call the process method with empty inputs
        result = planner_agent.process({})
        
        # Check the result
        assert "plan" in result
        assert "wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestPlannerAgent"
        
        # Check that the WSDE was created correctly
        wsde = result["wsde"]
        assert wsde.content == result["plan"]
        assert wsde.content_type == "text"
        assert wsde.metadata["agent"] == "TestPlannerAgent"
        assert wsde.metadata["type"] == "development_plan"

    def test_get_capabilities(self, planner_agent):
        """Test the get_capabilities method."""
        capabilities = planner_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 5
        assert "create_development_plan" in capabilities
        assert "design_architecture" in capabilities
        assert "define_implementation_phases" in capabilities
        assert "create_testing_strategy" in capabilities
        assert "create_deployment_plan" in capabilities

    def test_get_capabilities_with_custom_capabilities(self):
        """Test the get_capabilities method with custom capabilities."""
        agent = PlannerAgent()
        config = AgentConfig(
            name="TestPlannerAgent",
            agent_type=AgentType.PLANNER,
            description="Test Planner Agent",
            capabilities=["custom_capability"]
        )
        agent.initialize(config)
        
        # The agent should use the custom capabilities provided in the config
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "create_development_plan" not in capabilities

    @patch("devsynth.application.agents.planner.logger")
    def test_process_error_handling(self, mock_logger, planner_agent):
        """Test error handling in the process method."""
        # Create a mock WSDE that raises an exception when created
        with patch.object(planner_agent, 'create_wsde', side_effect=Exception("Test error")):
            # Call the process method
            result = planner_agent.process({})
            
            # Check that an error was logged
            mock_logger.error.assert_called_once()
            
            # The method should still return a result, even if an error occurred
            assert "plan" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestPlannerAgent"
            
            # The WSDE should be None due to the error
            assert result.get("wsde") is None