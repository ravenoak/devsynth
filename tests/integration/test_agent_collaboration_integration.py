"""
Integration test for the AgentCollaborationSystem class.

This test verifies that the AgentCollaborationSystem can enable collaboration
between specialized agents to work together on complex tasks.
"""

import os
import pytest
from unittest.mock import MagicMock
from typing import Dict, Any

from devsynth.application.collaboration.agent_collaboration import (
    AgentCollaborationSystem,
    CollaborationTask,
    AgentMessage,
    MessageType,
    TaskStatus,
)
from devsynth.domain.interfaces.agent import Agent


class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(self, agent_id: str, capabilities: list = None):
        self.id = agent_id
        self.capabilities = capabilities or []
        self.current_role = None
        self._process_mock = MagicMock(
            return_value={"status": "success", "message": f"Processed by {agent_id}"}
        )

    def get_capabilities(self) -> list:
        """Get the agent's capabilities."""
        return self.capabilities

    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize the agent with the given configuration."""
        pass

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task and return the result."""
        return self._process_mock(task)

    def set_llm_port(self, llm_port):
        """Set the LLM port for the agent."""
        pass


class TestAgentCollaborationSystem:
    """Test the AgentCollaborationSystem class."""

    def test_register_agent(self):
        """Test registering an agent with the collaboration system."""
        # Create a collaboration system
        collaboration_system = AgentCollaborationSystem()

        # Create a mock agent
        agent = MockAgent("agent1", ["planning", "coding"])

        # Register the agent
        agent_id = collaboration_system.register_agent(agent)

        # Verify that the agent was registered
        assert agent_id == "agent1"
        assert agent_id in collaboration_system.agents
        assert collaboration_system.agents[agent_id] == agent
        assert collaboration_system.agent_capabilities[agent_id] == {
            "planning",
            "coding",
        }

    def test_create_team(self):
        """Test creating a team of agents."""
        # Create a collaboration system
        collaboration_system = AgentCollaborationSystem()

        # Create and register mock agents
        agent1 = MockAgent("agent1", ["planning"])
        agent2 = MockAgent("agent2", ["coding"])
        agent3 = MockAgent("agent3", ["testing"])

        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)
        collaboration_system.register_agent(agent3)

        # Create a team
        team = collaboration_system.create_team("team1", ["agent1", "agent2", "agent3"])

        # Verify that the team was created
        assert "team1" in collaboration_system.teams
        assert collaboration_system.teams["team1"] == team
        assert len(team.agents) == 3

        # Verify that roles were assigned
        # With 3 agents, we should have Primus and at least 2 of the other roles
        assert any(agent.current_role == "Primus" for agent in team.agents)

        # Count the number of agents with each role
        role_counts = {
            "Worker": sum(1 for agent in team.agents if agent.current_role == "Worker"),
            "Supervisor": sum(
                1 for agent in team.agents if agent.current_role == "Supervisor"
            ),
            "Designer": sum(
                1 for agent in team.agents if agent.current_role == "Designer"
            ),
            "Evaluator": sum(
                1 for agent in team.agents if agent.current_role == "Evaluator"
            ),
        }

        # Verify that at least 2 of the other roles are assigned
        assert sum(1 for count in role_counts.values() if count > 0) >= 2

    def test_create_and_assign_task(self):
        """Test creating and assigning a task."""
        # Create a collaboration system
        collaboration_system = AgentCollaborationSystem()

        # Create and register mock agents
        agent1 = MockAgent("agent1", ["planning"])
        agent2 = MockAgent("agent2", ["coding"])

        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)

        # Create a task
        task = collaboration_system.create_task(
            task_type="coding",
            description="Implement a feature",
            inputs={"feature": "login"},
            required_capabilities=["coding"],
        )

        # Verify that the task was created
        assert task.id in collaboration_system.tasks
        assert task.task_type == "coding"
        assert task.description == "Implement a feature"
        assert task.inputs == {"feature": "login"}
        assert task.required_capabilities == ["coding"]
        assert task.status == TaskStatus.PENDING

        # Assign the task
        result = collaboration_system.assign_task(task.id)

        # Verify that the task was assigned
        assert result is True
        assert task.status == TaskStatus.ASSIGNED
        assert (
            task.assigned_agent_id == "agent2"
        )  # Should be assigned to agent2 because it has the "coding" capability

    def test_execute_task(self):
        """Test executing a task."""
        # Create a collaboration system
        collaboration_system = AgentCollaborationSystem()

        # Create and register a mock agent
        agent = MockAgent("agent1", ["coding"])
        collaboration_system.register_agent(agent)

        # Create a task
        task = collaboration_system.create_task(
            task_type="coding",
            description="Implement a feature",
            inputs={"feature": "login"},
            required_capabilities=["coding"],
        )

        # Assign the task
        collaboration_system.assign_task(task.id, "agent1")

        # Execute the task
        result = collaboration_system.execute_task(task.id)

        # Verify that the task was executed
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["status"] == "success"
        assert result["result"]["message"] == "Processed by agent1"
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result["result"]

    def test_send_message(self):
        """Test sending a message between agents."""
        # Create a collaboration system
        collaboration_system = AgentCollaborationSystem()

        # Create and register mock agents
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")

        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)

        # Send a message
        message = collaboration_system.send_message(
            sender_id="agent1",
            recipient_id="agent2",
            message_type=MessageType.QUESTION,
            content={"question": "How do I implement this feature?"},
        )

        # Verify that the message was sent
        assert message.id in collaboration_system.messages
        assert message.sender_id == "agent1"
        assert message.recipient_id == "agent2"
        assert message.message_type == MessageType.QUESTION
        assert message.content == {"question": "How do I implement this feature?"}

    def test_execute_workflow(self):
        """Test executing a workflow of tasks."""
        # Create a collaboration system
        collaboration_system = AgentCollaborationSystem()

        # Create and register mock agents
        agent1 = MockAgent("agent1", ["planning"])
        agent2 = MockAgent("agent2", ["coding"])
        agent3 = MockAgent("agent3", ["testing"])

        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)
        collaboration_system.register_agent(agent3)

        # Create tasks
        task1 = collaboration_system.create_task(
            task_type="planning",
            description="Plan the feature",
            inputs={"feature": "login"},
            required_capabilities=["planning"],
        )

        task2 = collaboration_system.create_task(
            task_type="coding",
            description="Implement the feature",
            inputs={"feature": "login"},
            required_capabilities=["coding"],
        )

        task3 = collaboration_system.create_task(
            task_type="testing",
            description="Test the feature",
            inputs={"feature": "login"},
            required_capabilities=["testing"],
        )

        # Add dependencies
        task2.add_dependency(task1.id)  # task2 depends on task1
        task3.add_dependency(task2.id)  # task3 depends on task2

        # Execute the workflow
        result = collaboration_system.execute_workflow([task1, task2, task3])

        # Verify that the workflow was executed
        assert result["success"] is True
        assert "results" in result
        assert task1.id in result["results"]
        assert task2.id in result["results"]
        assert task3.id in result["results"]
        assert result["results"][task1.id]["success"] is True
        assert result["results"][task2.id]["success"] is True
        assert result["results"][task3.id]["success"] is True
        assert task1.status == TaskStatus.COMPLETED
        assert task2.status == TaskStatus.COMPLETED
        assert task3.status == TaskStatus.COMPLETED


if __name__ == "__main__":
    pytest.main(["-v", "test_agent_collaboration.py"])
