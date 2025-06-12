"""
Unit Tests for AgentCoordinatorImpl

This file contains unit tests for the AgentCoordinatorImpl class, which is responsible
for coordinating agent collaboration using the WSDE model.
"""
import pytest
from unittest.mock import MagicMock, patch

from devsynth.domain.interfaces.agent import Agent
from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.application.collaboration.exceptions import (
    CollaborationError, 
    AgentExecutionError, 
    ConsensusError, 
    RoleAssignmentError,
    TeamConfigurationError
)
from devsynth.exceptions import ValidationError


class TestAgentCoordinatorImpl:
    """Test suite for the AgentCoordinatorImpl class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = AgentCoordinatorImpl()

        # Create mock agents
        self.agent1 = MagicMock(spec=Agent)
        self.agent1.name = "agent1"
        self.agent1.agent_type = "planner"
        self.agent1.current_role = None

        self.agent2 = MagicMock(spec=Agent)
        self.agent2.name = "agent2"
        self.agent2.agent_type = "code"
        self.agent2.current_role = None

        self.agent3 = MagicMock(spec=Agent)
        self.agent3.name = "agent3"
        self.agent3.agent_type = "test"
        self.agent3.current_role = None

        self.agent4 = MagicMock(spec=Agent)
        self.agent4.name = "agent4"
        self.agent4.agent_type = "validation"
        self.agent4.current_role = None

    def test_add_agent(self):
        """Test adding an agent to the coordinator."""
        # Arrange
        # Setup is done in setup_method

        # Act
        self.coordinator.add_agent(self.agent1)

        # Assert
        assert len(self.coordinator.agents) == 1
        assert self.coordinator.agents[0] == self.agent1
        assert len(self.coordinator.team.agents) == 1
        assert self.coordinator.team.agents[0] == self.agent1

    def test_delegate_task_to_agent_type(self):
        """Test delegating a task to a specific agent type."""
        # Arrange
        self.coordinator.add_agent(self.agent1)
        self.coordinator.add_agent(self.agent2)
        task = {"agent_type": "code", "action": "implement"}
        self.agent2.process.return_value = {"status": "success"}

        # Act
        result = self.coordinator.delegate_task(task)

        # Assert
        assert result == {"status": "success"}
        self.agent2.process.assert_called_once_with(task)
        self.agent1.process.assert_not_called()

    def test_delegate_task_to_team(self):
        """Test delegating a task to the entire team."""
        # Arrange
        self.coordinator.add_agent(self.agent1)
        self.coordinator.add_agent(self.agent2)
        self.coordinator.add_agent(self.agent3)
        self.coordinator.add_agent(self.agent4)
        
        # Configure mock returns
        self.agent1.process.return_value = {"design": "plan"}
        self.agent2.process.return_value = {"implementation": "code"}
        self.agent3.process.return_value = {"review": "feedback"}
        self.agent4.process.return_value = {"evaluation": "assessment"}
        
        task = {"team_task": True, "action": "implement"}

        # Act
        result = self.coordinator.delegate_task(task)

        # Assert
        assert "team_result" in result
        assert "design" in result["team_result"]
        assert "work" in result["team_result"]
        assert "supervision" in result["team_result"]
        assert "evaluation" in result["team_result"]
        assert "primus" in result["team_result"]

    def test_delegate_task_missing_parameters(self):
        """Test delegating a task with missing parameters."""
        # Arrange
        task = {}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task(task)

    def test_delegate_task_no_agents(self):
        """Test delegating a team task with no agents."""
        # Arrange
        task = {"team_task": True}

        # Act & Assert
        with pytest.raises(TeamConfigurationError):
            self.coordinator.delegate_task(task)

    def test_delegate_task_agent_type_not_found(self):
        """Test delegating a task to an agent type that doesn't exist."""
        # Arrange
        self.coordinator.add_agent(self.agent1)
        task = {"agent_type": "nonexistent"}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task(task)

    def test_delegate_task_agent_execution_error(self):
        """Test handling an error during agent execution."""
        # Arrange
        self.coordinator.add_agent(self.agent1)
        task = {"agent_type": "planner"}
        self.agent1.process.side_effect = Exception("Agent execution failed")

        # Act & Assert
        with pytest.raises(AgentExecutionError):
            self.coordinator.delegate_task(task)
