import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.collaboration.collaborative_wsde_team import CollaborativeWSDETeam
from devsynth.application.agents.base import BaseAgent


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock(spec=BaseAgent)
    agent.name = "MockAgent"
    agent.agent_type = "mock"
    agent.current_role = None
    agent.expertise = ["python", "testing"]
    agent.experience_level = 5
    agent.has_been_primus = False
    return agent


@pytest.fixture
def mock_agent_with_expertise():
    """Create mock agents with different expertise areas."""
    def _create_agent(name, expertise, experience_level=5):
        agent = MagicMock(spec=BaseAgent)
        agent.name = name
        agent.agent_type = "mock"
        agent.current_role = None
        agent.expertise = expertise
        agent.experience_level = experience_level
        agent.has_been_primus = False

        # Mock the process method
        def mock_process(inputs):
            # Return a simple response based on the agent's expertise
            return {
                "response": f"Response from {name} with expertise in {', '.join(expertise)}",
                "reasoning": f"Reasoning based on expertise in {', '.join(expertise)}"
            }

        agent.process = mock_process
        return agent

    return _create_agent


class TestCollaborativeWSDETeamTaskManagement:
    """Tests for the task management functionality of the CollaborativeWSDETeam class."""

    def test_process_task_non_hierarchical(self, mock_agent_with_expertise):
        """Test processing a task in non-hierarchical mode."""
        team = CollaborativeWSDETeam()
        team.collaboration_mode = "non_hierarchical"

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create a task
        task = {
            "id": "task1",
            "type": "implementation_task",
            "description": "Implement a feature",
            "required_expertise": ["python", "security"]
        }

        # Process the task
        result = team.process_task(task)

        # Verify the result
        assert result["id"] == "task1"
        assert result["task_id"] == "task1"
        assert "contributions" in result
        assert len(result["contributions"]) >= 2  # At least Agent1 and Agent3 should contribute

        # Verify contribution metrics
        metrics = team.get_contribution_metrics("task1")
        assert "Agent1" in metrics
        assert "Agent3" in metrics
        assert metrics["Agent1"]["contribution_score"] > 0
        assert metrics["Agent3"]["contribution_score"] > 0

        # Verify that no agent dominates (max 45% contribution)
        max_contribution = max(metrics[agent_name]["contribution_percentage"] for agent_name in metrics)
        assert max_contribution <= 45

    def test_process_task_hierarchical(self, mock_agent_with_expertise):
        """Test processing a task in hierarchical mode."""
        team = CollaborativeWSDETeam()
        team.collaboration_mode = "hierarchical"

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create a task
        task = {
            "id": "task2",
            "type": "implementation_task",
            "description": "Implement a feature",
            "required_expertise": ["python", "security"]
        }

        # Process the task
        result = team.process_task(task)

        # Verify the result
        assert result["id"] == "task2"
        assert result["task_id"] == "task2"
        assert "contributions" in result
        assert len(result["contributions"]) == 1  # Only primus contributes directly

        # Verify contribution metrics
        metrics = team.get_contribution_metrics("task2")
        primus_name = result["coordinator"]
        assert metrics[primus_name]["contribution_percentage"] == 80

        # Verify that other agents have minor contributions
        for agent_name in metrics:
            if agent_name != primus_name:
                assert metrics[agent_name]["contribution_percentage"] > 0
                assert metrics[agent_name]["contribution_percentage"] < 80

    def test_get_contribution_metrics(self, mock_agent_with_expertise):
        """Test getting contribution metrics for a task."""
        team = CollaborativeWSDETeam()

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)

        # Create a task
        task = {
            "id": "task3",
            "type": "implementation_task",
            "description": "Implement a feature"
        }

        # Process the task
        team.process_task(task)

        # Get contribution metrics
        metrics = team.get_contribution_metrics("task3")

        # Verify metrics
        assert "Agent1" in metrics
        assert "Agent2" in metrics
        assert "contribution_score" in metrics["Agent1"]
        assert "contribution_percentage" in metrics["Agent1"]

        # Test getting metrics for non-existent task
        non_existent_metrics = team.get_contribution_metrics("non_existent_task")
        assert non_existent_metrics == {}

    def test_get_role_history(self, mock_agent_with_expertise):
        """Test getting the history of role assignments."""
        team = CollaborativeWSDETeam()

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)

        # Create tasks
        task1 = {
            "id": "task4",
            "type": "implementation_task",
            "description": "Implement feature 1"
        }

        task2 = {
            "id": "task5",
            "type": "implementation_task",
            "description": "Implement feature 2"
        }

        # Process tasks
        team.process_task(task1)
        team.process_task(task2)

        # Get role history
        history = team.get_role_history()

        # Verify history
        assert len(history) == 2
        assert history[0]["task_id"] == "task4"
        assert history[1]["task_id"] == "task5"
        assert "primus" in history[0]
        assert "timestamp" in history[0]

    def test_associate_subtasks(self, mock_agent_with_expertise):
        """Test associating subtasks with a main task."""
        team = CollaborativeWSDETeam()

        # Create a main task
        main_task = {
            "id": "main_task",
            "type": "implementation_task",
            "description": "Implement a feature"
        }

        # Create subtasks
        subtasks = [
            {
                "id": "subtask1",
                "description": "Implement backend",
                "primary_expertise": "python"
            },
            {
                "id": "subtask2",
                "description": "Implement frontend",
                "primary_expertise": "javascript"
            }
        ]

        # Associate subtasks
        team.associate_subtasks(main_task, subtasks)

        # Verify association
        assert hasattr(team, "task_subtasks")
        assert "main_task" in team.task_subtasks
        assert len(team.task_subtasks["main_task"]) == 2
        assert "subtask1" in team.task_subtasks["main_task"]
        assert "subtask2" in team.task_subtasks["main_task"]

        # Verify progress initialization
        assert "subtask1" in team.subtask_progress
        assert "subtask2" in team.subtask_progress
        assert team.subtask_progress["subtask1"] == 0.0
        assert team.subtask_progress["subtask2"] == 0.0

    def test_delegate_subtasks(self, mock_agent_with_expertise):
        """Test delegating subtasks to agents based on expertise."""
        team = CollaborativeWSDETeam()

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create subtasks
        subtasks = [
            {
                "id": "subtask1",
                "description": "Implement backend",
                "primary_expertise": "python"
            },
            {
                "id": "subtask2",
                "description": "Implement frontend",
                "primary_expertise": "javascript"
            },
            {
                "id": "subtask3",
                "description": "Security review",
                "primary_expertise": "security"
            }
        ]

        # Delegate subtasks
        assignments = team.delegate_subtasks(subtasks)

        # Verify assignments
        assert "subtask1" in assignments
        assert "subtask2" in assignments
        assert "subtask3" in assignments
        assert assignments["subtask1"] == "Agent1"  # Python expertise
        assert assignments["subtask2"] == "Agent2"  # JavaScript expertise
        assert assignments["subtask3"] == "Agent3"  # Security expertise

        # Verify assignments are stored
        assert "subtask1" in team.subtask_assignments
        assert team.subtask_assignments["subtask1"] == "Agent1"

    def test_update_subtask_progress(self, mock_agent_with_expertise):
        """Test updating the progress of a subtask."""
        team = CollaborativeWSDETeam()

        # Create a subtask
        subtask = {
            "id": "subtask1",
            "description": "Implement backend",
            "primary_expertise": "python"
        }

        # Initialize progress
        team.subtask_progress["subtask1"] = 0.0

        # Update progress
        team.update_subtask_progress("subtask1", 0.5)

        # Verify progress
        assert team.subtask_progress["subtask1"] == 0.5

        # Test progress clamping
        team.update_subtask_progress("subtask1", 1.5)  # Should be clamped to 1.0
        assert team.subtask_progress["subtask1"] == 1.0

        team.update_subtask_progress("subtask1", -0.5)  # Should be clamped to 0.0
        assert team.subtask_progress["subtask1"] == 0.0

    def test_reassign_subtasks_based_on_progress(self, mock_agent_with_expertise):
        """Test reassigning subtasks based on progress and agent availability."""
        team = CollaborativeWSDETeam()

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["python", "security"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create subtasks
        subtasks = [
            {
                "id": "subtask1",
                "description": "Implement backend 1",
                "primary_expertise": "python"
            },
            {
                "id": "subtask2",
                "description": "Implement backend 2",
                "primary_expertise": "python"
            },
            {
                "id": "subtask3",
                "description": "Implement frontend",
                "primary_expertise": "javascript"
            }
        ]

        # Set initial assignments
        team.subtask_assignments = {
            "subtask1": "Agent1",
            "subtask2": "Agent1",  # Agent1 is overloaded
            "subtask3": "Agent2"
        }

        # Set initial progress
        team.subtask_progress = {
            "subtask1": 0.7,  # High progress, shouldn't be reassigned
            "subtask2": 0.2,  # Low progress, should be reassigned
            "subtask3": 0.5
        }

        # Reassign subtasks
        new_assignments = team.reassign_subtasks_based_on_progress(subtasks)

        # Verify reassignments
        assert new_assignments["subtask1"] == "Agent1"  # High progress, shouldn't be reassigned
        assert new_assignments["subtask2"] != "Agent1"  # Should be reassigned to Agent3 (has python expertise)
        assert new_assignments["subtask2"] == "Agent3"
        assert new_assignments["subtask3"] == "Agent2"  # Shouldn't be reassigned
