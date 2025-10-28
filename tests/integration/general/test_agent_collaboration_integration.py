"""
Integration test for the AgentCollaborationSystem class.

This test verifies that the AgentCollaborationSystem can enable collaboration
between specialized agents to work together on complex tasks.
"""

import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.agent_collaboration import (
    AgentCollaborationSystem,
    AgentMessage,
    CollaborationTask,
    MessageType,
    TaskStatus,
)
from devsynth.application.collaboration.message_protocol import (
    MessageProtocol,
    MessageStore,
)
from devsynth.application.collaboration.message_protocol import (
    MessageType as ProtocolMessageType,
)
from devsynth.application.collaboration.peer_review import run_peer_review
from devsynth.domain.interfaces.agent import Agent


class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(self, agent_id: str, capabilities: list = None):
        self.id = agent_id
        self.capabilities = capabilities or []
        self.expertise = self.capabilities
        self.current_role = None
        self._process_mock = MagicMock(
            return_value={"status": "success", "message": f"Processed by {agent_id}"}
        )

    def get_capabilities(self) -> list:
        """Get the agent's capabilities."""
        return self.capabilities

    def initialize(self, config: dict[str, Any] = None) -> None:
        """Initialize the agent with the given configuration."""
        pass

    def process(self, task: dict[str, Any]) -> dict[str, Any]:
        """Process a task and return the result."""
        return self._process_mock(task)

    def set_llm_port(self, llm_port):
        """Set the LLM port for the agent."""
        pass


class TestAgentCollaborationSystem:
    """Test the AgentCollaborationSystem class.

    ReqID: N/A"""

    def test_register_agent_succeeds(self):
        """Test registering an agent with the collaboration system.

        ReqID: N/A"""
        collaboration_system = AgentCollaborationSystem()
        agent = MockAgent("agent1", ["planning", "coding"])
        agent_id = collaboration_system.register_agent(agent)
        assert agent_id == "agent1"
        assert agent_id in collaboration_system.agents
        assert collaboration_system.agents[agent_id] == agent
        assert collaboration_system.agent_capabilities[agent_id] == {
            "planning",
            "coding",
        }

    def test_create_team_succeeds(self):
        """Test creating a team of agents.

        ReqID: N/A"""
        collaboration_system = AgentCollaborationSystem()
        agent1 = MockAgent("agent1", ["planning", "design"])
        agent2 = MockAgent("agent2", ["coding", "review"])
        agent3 = MockAgent("agent3", ["testing", "qa"])
        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)
        collaboration_system.register_agent(agent3)
        team = collaboration_system.create_team("team1", ["agent1", "agent2", "agent3"])
        assert "team1" in collaboration_system.teams
        assert collaboration_system.teams["team1"] == team
        assert len(team.agents) == 3
        assert any(agent.current_role == "Primus" for agent in team.agents)
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
        assert sum(1 for count in role_counts.values() if count > 0) >= 2

    def test_create_and_assign_task_succeeds(self):
        """Test creating and assigning a task.

        ReqID: N/A"""
        collaboration_system = AgentCollaborationSystem()
        agent1 = MockAgent("agent1", ["planning"])
        agent2 = MockAgent("agent2", ["coding"])
        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)
        task = collaboration_system.create_task(
            task_type="coding",
            description="Implement a feature",
            inputs={"feature": "login"},
            required_capabilities=["coding"],
        )
        assert task.id in collaboration_system.tasks
        assert task.task_type == "coding"
        assert task.description == "Implement a feature"
        assert task.inputs == {"feature": "login"}
        assert task.required_capabilities == ["coding"]
        assert task.status == TaskStatus.PENDING
        result = collaboration_system.assign_task(task.id)
        assert result is True
        assert task.status == TaskStatus.ASSIGNED
        assert task.assigned_agent_id == "agent2"

    def test_execute_task_succeeds(self):
        """Test executing a task.

        ReqID: N/A"""
        collaboration_system = AgentCollaborationSystem()
        agent = MockAgent("agent1", ["coding"])
        collaboration_system.register_agent(agent)
        task = collaboration_system.create_task(
            task_type="coding",
            description="Implement a feature",
            inputs={"feature": "login"},
            required_capabilities=["coding"],
        )
        collaboration_system.assign_task(task.id, "agent1")
        result = collaboration_system.execute_task(task.id)
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["status"] == "success"
        assert result["result"]["message"] == "Processed by agent1"
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result["result"]

    def test_send_message_succeeds(self):
        """Test sending a message between agents.

        ReqID: N/A"""
        collaboration_system = AgentCollaborationSystem()
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)
        message = collaboration_system.send_message(
            sender_id="agent1",
            recipient_id="agent2",
            message_type=MessageType.QUESTION,
            content={"question": "How do I implement this feature?"},
        )
        assert message.id in collaboration_system.messages
        assert message.sender_id == "agent1"
        assert message.recipient_id == "agent2"
        assert message.message_type == MessageType.QUESTION
        assert message.content == {"question": "How do I implement this feature?"}

    def test_execute_workflow_succeeds(self):
        """Test executing a workflow of tasks.

        ReqID: N/A"""
        collaboration_system = AgentCollaborationSystem()
        agent1 = MockAgent("agent1", ["planning"])
        agent2 = MockAgent("agent2", ["coding"])
        agent3 = MockAgent("agent3", ["testing"])
        collaboration_system.register_agent(agent1)
        collaboration_system.register_agent(agent2)
        collaboration_system.register_agent(agent3)
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
        task2.add_dependency(task1.id)
        task3.add_dependency(task2.id)
        result = collaboration_system.execute_workflow([task1, task2, task3])
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

    def test_message_protocol_persistence_succeeds(self, tmp_path, monkeypatch):
        """Ensure messages are persisted to storage.

        ReqID: N/A"""
        storage_file = tmp_path / "messages.json"
        monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
        store = MessageStore(str(storage_file))
        proto = MessageProtocol(store)
        proto.send_message(
            sender="a",
            recipients=["b"],
            message_type=ProtocolMessageType.STATUS_UPDATE,
            subject="s",
            content="c",
        )
        proto2 = MessageProtocol(MessageStore(str(storage_file)))
        msgs = proto2.get_messages()
        assert len(msgs) == 1
        assert msgs[0].sender == "a"

    def test_peer_review_workflow_succeeds(self):
        """Run a full peer review using workflow helpers.

        ReqID: N/A"""
        author = MockAgent("author")
        reviewer1 = MockAgent("r1")
        reviewer2 = MockAgent("r2")
        result = run_peer_review(
            work_product={"text": "demo"},
            author=author,
            reviewers=[reviewer1, reviewer2],
        )
        assert result["status"] == "approved"
        assert result["feedback"]["feedback"]

    def test_peer_review_with_team_builds_consensus_and_rotates_roles(self):
        """Peer review integrates WSDETeam role rotation and consensus."""

        from devsynth.domain.models.wsde_facade import WSDETeam

        class DummyAgent(MockAgent):
            def __init__(self, name):
                super().__init__(name)
                self.name = name

        team = WSDETeam(name="PRTeam")
        author = DummyAgent("author")
        reviewer1 = DummyAgent("r1")
        reviewer2 = DummyAgent("r2")
        team.add_agents([author, reviewer1, reviewer2])

        with (
            patch.object(team, "rotate_roles", wraps=team.rotate_roles) as rot_spy,
            patch.object(
                team, "build_consensus", wraps=team.build_consensus
            ) as cons_spy,
        ):
            result = run_peer_review(
                {"text": "demo"}, author, [reviewer1, reviewer2], team=team
            )

        assert rot_spy.called
        assert cons_spy.called
        assert "consensus" in result


if __name__ == "__main__":
    pytest.main(["-v", "test_agent_collaboration.py"])
