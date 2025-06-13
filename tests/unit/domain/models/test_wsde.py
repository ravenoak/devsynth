"""
Unit Tests for WSDE Models

This file contains unit tests for the WSDE (Worker Self-Directed Enterprise) models,
focusing on the WSDETeam class and its functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDETeam, WSDE
from datetime import datetime
from typing import Dict, List, Any


class TestWSDETeam:
    """Test suite for the WSDETeam class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam()

        # Create mock agents
        self.agent1 = MagicMock()
        self.agent1.name = "agent1"
        self.agent1.current_role = None
        self.agent1.parameters = {"expertise": ["python", "code_generation"]}

        self.agent2 = MagicMock()
        self.agent2.name = "agent2"
        self.agent2.current_role = None
        self.agent2.parameters = {"expertise": ["testing", "test_generation"]}

        self.agent3 = MagicMock()
        self.agent3.name = "agent3"
        self.agent3.current_role = None
        self.agent3.parameters = {"expertise": ["documentation", "markdown"]}

        self.agent4 = MagicMock()
        self.agent4.name = "agent4"
        self.agent4.current_role = None
        self.agent4.parameters = {"expertise": ["design", "architecture"]}

        # Create a critic agent for dialectical reasoning
        self.critic_agent = MagicMock()
        self.critic_agent.name = "critic"
        self.critic_agent.current_role = None
        self.critic_agent.parameters = {"expertise": ["critique", "dialectical_reasoning"]}

    def test_add_agent(self):
        """Test adding an agent to the team."""
        # Arrange
        # Setup is done in setup_method

        # Act
        self.team.add_agent(self.agent1)

        # Assert
        assert len(self.team.agents) == 1
        assert self.team.agents[0] == self.agent1

    def test_dialectical_hook_invoked_on_add_solution(self):
        """Registered dialectical hooks should run when a solution is added."""

        called: Dict[str, Any] = {}

        def hook(task: Dict[str, Any], solutions: List[Dict[str, Any]]):
            called["task"] = task
            called["solutions"] = list(solutions)

        self.team.register_dialectical_hook(hook)

        task = {"id": "task1"}
        solution = {"agent": "a1", "content": "foo"}

        self.team.add_solution(task, solution)

        assert called["task"] == task
        assert called["solutions"][0] == solution

    def test_rotate_primus(self):
        """Test rotating the Primus role."""
        # Arrange
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        initial_primus_index = self.team.primus_index

        # Act
        self.team.rotate_primus()

        # Assert
        assert self.team.primus_index != initial_primus_index
        assert self.team.primus_index == (initial_primus_index + 1) % len(self.team.agents)

    def test_get_primus(self):
        """Test getting the current Primus agent."""
        # Arrange
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.primus_index = 1

        # Act
        primus = self.team.get_primus()

        # Assert
        assert primus == self.agent2

    def test_get_primus_empty_team(self):
        """Test getting the Primus agent from an empty team."""
        # Arrange
        # Empty team is created in setup_method

        # Act
        primus = self.team.get_primus()

        # Assert
        assert primus is None

    def test_assign_roles(self):
        """Test assigning WSDE roles to agents."""
        # Arrange
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)
        self.team.primus_index = 0

        # Act
        self.team.assign_roles()

        # Assert
        assert self.agent1.current_role == "Primus"
        assert self.agent2.current_role in ["Worker", "Supervisor", "Designer", "Evaluator"]
        assert self.agent3.current_role in ["Worker", "Supervisor", "Designer", "Evaluator"]
        assert self.agent4.current_role in ["Worker", "Supervisor", "Designer", "Evaluator"]

        # Ensure each role is assigned exactly once
        roles = [self.agent2.current_role, self.agent3.current_role, self.agent4.current_role]
        assert "Worker" in roles
        assert "Supervisor" in roles
        # Since we can't assign all 4 roles to 3 agents, we check for either Designer or Evaluator
        assert "Designer" in roles or "Evaluator" in roles

    def test_get_agent_by_role(self):
        """Test getting agents by their role."""
        # Arrange
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)
        self.team.primus_index = 0
        self.team.assign_roles()

        # Act & Assert
        assert self.team.get_primus() == self.agent1

        # Find which agent was assigned the Worker role
        worker_agent = None
        for agent in [self.agent2, self.agent3, self.agent4]:
            if agent.current_role == "Worker":
                worker_agent = agent
                break

        assert self.team.get_worker() == worker_agent

        # Similar checks for other roles
        for role, method in [
            ("Supervisor", self.team.get_supervisor),
            ("Designer", self.team.get_designer),
            ("Evaluator", self.team.get_evaluator)
        ]:
            role_agent = None
            for agent in [self.agent2, self.agent3, self.agent4]:
                if agent.current_role == role:
                    role_agent = agent
                    break

            assert method() == role_agent

    def test_assign_roles_with_rotation(self):
        """Test that role assignments change when the Primus rotates."""
        # Arrange
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)
        self.team.primus_index = 0
        self.team.assign_roles()

        # Record initial roles
        initial_roles = {
            self.agent1.name: self.agent1.current_role,
            self.agent2.name: self.agent2.current_role,
            self.agent3.name: self.agent3.current_role,
            self.agent4.name: self.agent4.current_role
        }

        # Act
        self.team.rotate_primus()
        self.team.assign_roles()

        # Assert
        # Verify that roles have changed
        assert self.agent1.current_role != initial_roles[self.agent1.name]
        assert self.agent2.current_role == "Primus"  # New Primus

        # Ensure each role is still assigned exactly once
        roles = [self.agent1.current_role, self.agent3.current_role, self.agent4.current_role]
        assert "Worker" in roles
        assert "Supervisor" in roles
        # Since we can't assign all 4 roles to 3 agents, we check for either Designer or Evaluator
        assert "Designer" in roles or "Evaluator" in roles

    def test_apply_dialectical_reasoning_with_knowledge_graph(self):
        """Test applying dialectical reasoning with knowledge graph integration."""
        # Arrange
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)

        # Create a mock task and solution
        task = {
            "id": "task1",
            "type": "code_generation",
            "description": "Implement a secure authentication system",
            "requirements": ["user authentication", "password security"]
        }

        solution = {
            "id": "solution1",
            "agent": "agent1",
            "content": "def authenticate(username, password):\n    return username == 'admin' and password == 'password'",
            "description": "Simple authentication function"
        }

        # Add the solution to the team
        self.team.solutions = {task["id"]: [solution]}

        # Create a mock WSDEMemoryIntegration
        mock_wsde_memory = MagicMock()

        # Mock the knowledge graph query methods
        mock_wsde_memory.query_knowledge_for_task.return_value = [
            {"concept": "authentication", "relevance": 0.9},
            {"concept": "password", "relevance": 0.8},
            {"concept": "security", "relevance": 0.7}
        ]

        mock_wsde_memory.query_concept_relationships.return_value = [
            {"relationship": "requires", "direction": "outgoing"}
        ]

        # Act
        result = self.team.apply_dialectical_reasoning_with_knowledge_graph(
            task, 
            self.critic_agent, 
            mock_wsde_memory
        )

        # Assert
        # Verify the structure of the result
        assert "thesis" in result
        assert "antithesis" in result
        assert "synthesis" in result
        assert "evaluation" in result
        assert "knowledge_graph_insights" in result

        # Verify knowledge graph insights
        assert "relevant_concepts" in result["knowledge_graph_insights"]
        assert "concept_relationships" in result["knowledge_graph_insights"]
        assert "task_relevant_knowledge" in result["knowledge_graph_insights"]

        # Verify that the knowledge graph was queried
        mock_wsde_memory.query_knowledge_for_task.assert_called_once_with(task)
        assert mock_wsde_memory.query_concept_relationships.called

        # Verify that the antithesis contains critique categories
        assert "critique_categories" in result["antithesis"]
        assert "security" in result["antithesis"]["critique_categories"]

        # Verify that the synthesis contains addressed critiques
        assert "addressed_critiques" in result["synthesis"]

        # Verify that the evaluation contains knowledge alignment
        assert "knowledge_alignment" in result["evaluation"]
        assert "alignment_score" in result["evaluation"]
        assert "alignment_level" in result["evaluation"]


class TestWSDE:
    """Test suite for the WSDE class."""

    def test_initialization(self):
        """Test that a WSDE is initialized correctly."""
        # Arrange & Act
        wsde = WSDE(content="Test content", content_type="text")

        # Assert
        assert wsde.content == "Test content"
        assert wsde.content_type == "text"
        assert wsde.id is not None
        assert wsde.metadata == {}
        assert isinstance(wsde.created_at, datetime)
        assert wsde.updated_at == wsde.created_at

    def test_initialization_with_metadata(self):
        """Test that a WSDE is initialized correctly with metadata."""
        # Arrange & Act
        metadata = {"key": "value", "another_key": 123}
        wsde = WSDE(content="Test content", content_type="text", metadata=metadata)

        # Assert
        assert wsde.metadata == metadata
        assert wsde.metadata["key"] == "value"
        assert wsde.metadata["another_key"] == 123
