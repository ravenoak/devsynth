import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.application.agents.refactor import RefactorAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.ports.llm_port import LLMPort


class TestRefactorAgent:
    """Unit tests for the RefactorAgent class."""

    @pytest.fixture
    def mock_llm_port(self):
        """Create a mock LLM port."""
        mock_port = MagicMock(spec=LLMPort)
        mock_port.generate.return_value = "Generated refactored code"
        mock_port.generate_with_context.return_value = "Generated refactored code with context"
        return mock_port

    @pytest.fixture
    def refactor_agent(self, mock_llm_port):
        """Create a RefactorAgent instance for testing."""
        agent = RefactorAgent()
        config = AgentConfig(
            name="TestRefactorAgent",
            agent_type=AgentType.REFACTOR,
            description="Test Refactor Agent",
            capabilities=[]  # Let the agent define its own capabilities
        )
        agent.initialize(config)
        agent.set_llm_port(mock_llm_port)
        return agent

    def test_initialization(self, refactor_agent):
        """Test that the agent initializes correctly."""
        assert refactor_agent.name == "TestRefactorAgent"
        assert refactor_agent.agent_type == AgentType.REFACTOR.value
        assert refactor_agent.description == "Test Refactor Agent"
        # Check that capabilities are set by the agent
        capabilities = refactor_agent.get_capabilities()
        assert "refactor_code" in capabilities
        assert "improve_readability" in capabilities
        assert "improve_maintainability" in capabilities
        assert "optimize_performance" in capabilities
        assert "enhance_security" in capabilities
        assert "improve_testability" in capabilities

    def test_process(self, refactor_agent):
        """Test the process method."""
        # Create test inputs
        inputs = {
            "context": "This is a test project",
            "code": "def add(a, b): return a + b",
            "validation_report": "The code is functional but could be improved"
        }
        
        # Call the process method
        result = refactor_agent.process(inputs)
        
        # Check the result
        assert "refactored_code" in result
        assert "explanation" in result
        assert "code_wsde" in result
        assert "explanation_wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestRefactorAgent"
        
        # Check that the WSDEs were created correctly
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

    def test_process_with_empty_inputs(self, refactor_agent):
        """Test the process method with empty inputs."""
        # Call the process method with empty inputs
        result = refactor_agent.process({})
        
        # Check the result
        assert "refactored_code" in result
        assert "explanation" in result
        assert "code_wsde" in result
        assert "explanation_wsde" in result
        assert "agent" in result
        assert "role" in result
        assert result["agent"] == "TestRefactorAgent"
        
        # Check that the WSDEs were created correctly
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

    def test_get_capabilities(self, refactor_agent):
        """Test the get_capabilities method."""
        capabilities = refactor_agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 6
        assert "refactor_code" in capabilities
        assert "improve_readability" in capabilities
        assert "improve_maintainability" in capabilities
        assert "optimize_performance" in capabilities
        assert "enhance_security" in capabilities
        assert "improve_testability" in capabilities

    def test_get_capabilities_with_custom_capabilities(self):
        """Test the get_capabilities method with custom capabilities."""
        agent = RefactorAgent()
        config = AgentConfig(
            name="TestRefactorAgent",
            agent_type=AgentType.REFACTOR,
            description="Test Refactor Agent",
            capabilities=["custom_capability"]
        )
        agent.initialize(config)
        
        # The agent should use the custom capabilities provided in the config
        capabilities = agent.get_capabilities()
        assert len(capabilities) == 1
        assert "custom_capability" in capabilities
        assert "refactor_code" not in capabilities

    @patch("devsynth.application.agents.refactor.logger")
    def test_process_error_handling_code_wsde(self, mock_logger, refactor_agent):
        """Test error handling in the process method when creating code WSDE fails."""
        # Create a mock WSDE that raises an exception when created the first time (for code_wsde)
        # but succeeds the second time (for explanation_wsde)
        side_effects = [Exception("Test error"), MagicMock()]
        with patch.object(refactor_agent, 'create_wsde', side_effect=side_effects):
            # Call the process method
            result = refactor_agent.process({})
            
            # Check that an error was logged
            mock_logger.error.assert_called_once()
            
            # The method should still return a result, even if an error occurred
            assert "refactored_code" in result
            assert "explanation" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestRefactorAgent"
            
            # The code_wsde should be None due to the error
            assert result.get("code_wsde") is None
            # The explanation_wsde should still be created
            assert result.get("explanation_wsde") is not None

    @patch("devsynth.application.agents.refactor.logger")
    def test_process_error_handling_explanation_wsde(self, mock_logger, refactor_agent):
        """Test error handling in the process method when creating explanation WSDE fails."""
        # Create a mock WSDE that succeeds the first time (for code_wsde)
        # but raises an exception the second time (for explanation_wsde)
        side_effects = [MagicMock(), Exception("Test error")]
        with patch.object(refactor_agent, 'create_wsde', side_effect=side_effects):
            # Call the process method
            result = refactor_agent.process({})
            
            # Check that an error was logged
            mock_logger.error.assert_called_once()
            
            # The method should still return a result, even if an error occurred
            assert "refactored_code" in result
            assert "explanation" in result
            assert "agent" in result
            assert "role" in result
            assert result["agent"] == "TestRefactorAgent"
            
            # The code_wsde should still be created
            assert result.get("code_wsde") is not None
            # The explanation_wsde should be None due to the error
            assert result.get("explanation_wsde") is None