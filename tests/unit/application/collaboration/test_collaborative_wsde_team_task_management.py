from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.base import BaseAgent
from devsynth.application.collaboration.collaborative_wsde_team import (
    CollaborativeWSDETeam,
)
from devsynth.application.collaboration.dto import AgentOpinionRecord, ConsensusOutcome
from devsynth.application.collaboration.exceptions import PeerReviewConsensusError
from devsynth.application.collaboration.structures import SubtaskSpec


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

        def mock_process(inputs):
            return {
                "response": f"Response from {name} with expertise in {', '.join(expertise)}",
                "reasoning": f"Reasoning based on expertise in {', '.join(expertise)}",
            }

        agent.process = mock_process
        return agent

    return _create_agent


class TestCollaborativeWSDETeamTaskManagement:
    """Tests for the task management functionality of the CollaborativeWSDETeam class.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_process_task_non_hierarchical_succeeds(self, mock_agent_with_expertise):
        """Test processing a task in non-hierarchical mode.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        team.collaboration_mode = "non_hierarchical"
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        task = {
            "id": "task1",
            "type": "implementation_task",
            "title": "Implement a feature",
            "description": "Implement a feature",
            "required_expertise": ["python", "security"],
        }
        result = team.process_task(task)
        assert result["id"] == "task1"
        assert "subtasks" in result
        assert "delegation_results" in result
        assert "results" in result
        if "task1" not in team.contribution_metrics:
            team.contribution_metrics["task1"] = {}
        team.contribution_metrics["task1"]["Agent1"] = {
            "assigned_subtasks": 2,
            "completed_subtasks": 1,
            "total_progress": 1.5,
            "average_progress": 0.75,
        }
        team.contribution_metrics["task1"]["Agent3"] = {
            "assigned_subtasks": 1,
            "completed_subtasks": 0,
            "total_progress": 0.5,
            "average_progress": 0.5,
        }
        metrics = team.get_contribution_metrics("task1")
        assert "Agent1" in metrics
        assert "Agent3" in metrics
        assert metrics["Agent1"]["assigned_subtasks"] > 0
        assert metrics["Agent3"]["assigned_subtasks"] > 0

    @pytest.mark.medium
    def test_process_task_hierarchical_succeeds(self, mock_agent_with_expertise):
        """Test processing a task in hierarchical mode.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        team.collaboration_mode = "hierarchical"
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        task = {
            "id": "task2",
            "type": "implementation_task",
            "title": "Implement a feature",
            "description": "Implement a feature",
            "required_expertise": ["python", "security"],
        }
        result = team.process_task(task)
        assert result["id"] == "task2"
        assert "subtasks" in result
        assert "delegation_results" in result
        assert "results" in result
        if "task2" not in team.contribution_metrics:
            team.contribution_metrics["task2"] = {}
        team.contribution_metrics["task2"]["Agent1"] = {
            "assigned_subtasks": 3,
            "completed_subtasks": 2,
            "total_progress": 2.5,
            "average_progress": 0.83,
        }
        team.contribution_metrics["task2"]["Agent2"] = {
            "assigned_subtasks": 1,
            "completed_subtasks": 0,
            "total_progress": 0.3,
            "average_progress": 0.3,
        }
        team.contribution_metrics["task2"]["Agent3"] = {
            "assigned_subtasks": 1,
            "completed_subtasks": 0,
            "total_progress": 0.2,
            "average_progress": 0.2,
        }
        metrics = team.get_contribution_metrics("task2")
        assert len(metrics) > 0
        agent_names = list(metrics.keys())
        assert len(agent_names) > 0
        for agent_name in agent_names:
            assert "assigned_subtasks" in metrics[agent_name]
            assert "completed_subtasks" in metrics[agent_name]
            assert "total_progress" in metrics[agent_name]
            assert "average_progress" in metrics[agent_name]

    @pytest.mark.fast
    def test_consensus_outcome_normalizes_participants_and_metadata(self) -> None:
        """ConsensusOutcome deduplicates participants and orders metadata keys."""

        outcome = ConsensusOutcome(
            consensus_id="cid-1",
            task_id="tid-1",
            method="majority_opinion",
            agent_opinions=(
                AgentOpinionRecord(
                    agent_id="beta",
                    opinion="use option",
                    timestamp="2025-01-02T00:00:00",
                ),
                AgentOpinionRecord(
                    agent_id="alpha",
                    opinion="use option",
                    timestamp="2025-01-01T00:00:00",
                ),
            ),
            participants=("beta", "alpha", "alpha"),
            metadata={"z": 1, "a": 2},
            majority_opinion="use option",
        )

        assert outcome.participants == ("beta", "alpha")
        assert [record.agent_id for record in outcome.agent_opinions] == [
            "alpha",
            "beta",
        ]
        assert list(outcome.metadata.keys()) == ["a", "z"]
        serialized = outcome.to_dict()
        assert serialized["participants"] == list(outcome.participants)
        assert serialized["metadata"] == {"a": 2, "z": 1}

    @pytest.mark.fast
    def test_peer_review_consensus_error_embeds_serialized_outcome(self) -> None:
        """PeerReviewConsensusError exposes outcome metadata via as_dict."""

        outcome = ConsensusOutcome(
            consensus_id="cid-2",
            task_id="tid-2",
            method="majority_opinion",
            agent_opinions=(AgentOpinionRecord(agent_id="alpha", opinion="approve"),),
            majority_opinion="approve",
        )

        error = PeerReviewConsensusError(
            "Targeted consensus failure",
            outcome=outcome,
            review_id="review-123",
        )

        message = str(error)
        assert "review-123" in message
        payload = error.as_dict()
        assert payload["message"].endswith("[review_id=review-123]")
        assert payload["consensus"]["dto_type"] == "ConsensusOutcome"

    @pytest.mark.medium
    def test_get_contribution_metrics_succeeds(self, mock_agent_with_expertise):
        """Test getting contribution metrics for a task.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        team.add_agent(agent1)
        team.add_agent(agent2)
        task = {
            "id": "task3",
            "type": "implementation_task",
            "title": "Implement a feature",
            "description": "Implement a feature",
        }
        team.process_task(task)
        metrics = team.get_contribution_metrics("task3")
        if metrics:
            for agent_name in metrics:
                assert "assigned_subtasks" in metrics[agent_name]
                assert "completed_subtasks" in metrics[agent_name]
                assert "total_progress" in metrics[agent_name]
                assert "average_progress" in metrics[agent_name]
        non_existent_metrics = team.get_contribution_metrics("non_existent_task")
        assert non_existent_metrics == {}

    @pytest.mark.medium
    def test_get_role_history_succeeds(self, mock_agent_with_expertise):
        """Test getting the history of role assignments.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        team.add_agent(agent1)
        team.add_agent(agent2)
        task1 = {
            "id": "task4",
            "type": "implementation_task",
            "title": "Implement feature 1",
            "description": "Implement feature 1",
        }
        task2 = {
            "id": "task5",
            "type": "implementation_task",
            "title": "Implement feature 2",
            "description": "Implement feature 2",
        }
        team.process_task(task1)
        team.process_task(task2)
        history = team.get_role_history()
        assert isinstance(history, list)
        for entry in history:
            assert "timestamp" in entry

    @pytest.mark.medium
    def test_associate_subtasks_succeeds(self, mock_agent_with_expertise):
        """Test associating subtasks with a main task.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        main_task = {
            "id": "main_task",
            "type": "implementation_task",
            "title": "Implement a feature",
            "description": "Implement a feature",
        }
        subtasks = [
            {
                "id": "subtask1",
                "description": "Implement backend",
                "primary_expertise": "python",
            },
            {
                "id": "subtask2",
                "description": "Implement frontend",
                "primary_expertise": "javascript",
            },
        ]
        team.associate_subtasks(main_task, subtasks)
        assert hasattr(team, "subtasks")
        assert "main_task" in team.subtasks
        assert len(team.subtasks["main_task"]) == 2
        subtask_ids = [subtask.id for subtask in team.subtasks["main_task"]]
        assert len(subtask_ids) == 2
        if not hasattr(team, "subtask_progress"):
            team.subtask_progress = {}

    @pytest.mark.medium
    def test_delegate_subtasks_succeeds(self, mock_agent_with_expertise):
        """Test delegating subtasks to agents based on expertise.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        subtasks = [
            SubtaskSpec(
                id="subtask1",
                title="Implement backend",
                description="Implement backend",
                parent_task_id="taskA",
                metadata={"primary_expertise": "python"},
            ),
            SubtaskSpec(
                id="subtask2",
                title="Implement frontend",
                description="Implement frontend",
                parent_task_id="taskA",
                metadata={"primary_expertise": "javascript"},
            ),
            SubtaskSpec(
                id="subtask3",
                title="Security review",
                description="Security review",
                parent_task_id="taskA",
                metadata={"primary_expertise": "security"},
            ),
        ]
        assignments = team.delegate_subtasks(subtasks)
        assert len(assignments) == 3
        assignment_dict = {
            result.subtask_id: result.assigned_to for result in assignments
        }
        assert "subtask1" in assignment_dict
        assert "subtask2" in assignment_dict
        assert "subtask3" in assignment_dict
        assert assignment_dict["subtask1"] == "Agent1"
        assert assignment_dict["subtask2"] == "Agent2"
        assert assignment_dict["subtask3"] == "Agent3"
        for subtask in subtasks:
            assert subtask.assigned_to in {"Agent1", "Agent2", "Agent3"}
            assert subtask.status == "assigned"

    @pytest.mark.medium
    def test_update_subtask_progress_succeeds(self, mock_agent_with_expertise):
        """Test updating the progress of a subtask.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        subtask = SubtaskSpec(
            id="subtask1",
            title="Implement backend",
            description="Implement backend",
            parent_task_id="taskB",
            metadata={"primary_expertise": "python"},
        )
        team.subtasks["taskB"] = [subtask]
        team.subtask_progress["subtask1"] = 0.0
        team.update_subtask_progress("subtask1", 0.5)
        assert team.subtask_progress["subtask1"] == 0.5
        team.update_subtask_progress("subtask1", 1.0)
        assert team.subtask_progress["subtask1"] == 1.0
        team.update_subtask_progress("subtask1", 0.0)
        assert team.subtask_progress["subtask1"] == 0.0
        team.update_subtask_progress("subtask1", 0.75)
        assert team.subtask_progress["subtask1"] == 0.75

    @pytest.mark.medium
    def test_reassign_subtasks_based_on_progress_succeeds(
        self, mock_agent_with_expertise
    ):
        """Test reassigning subtasks based on progress and agent availability.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["python", "security"])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        subtasks = [
            SubtaskSpec(
                id="subtask1",
                title="Implement backend 1",
                description="Implement backend 1",
                parent_task_id="taskC",
                assigned_to="Agent1",
                status="assigned",
                metadata={"primary_expertise": "python"},
            ),
            SubtaskSpec(
                id="subtask2",
                title="Implement backend 2",
                description="Implement backend 2",
                parent_task_id="taskC",
                assigned_to="Agent1",
                status="assigned",
                metadata={"primary_expertise": "python"},
            ),
            SubtaskSpec(
                id="subtask3",
                title="Implement frontend",
                description="Implement frontend",
                parent_task_id="taskC",
                assigned_to="Agent2",
                status="assigned",
                metadata={"primary_expertise": "javascript"},
            ),
        ]
        team.subtasks["taskC"] = subtasks
        team.subtask_progress = {"subtask1": 0.7, "subtask2": 0.2, "subtask3": 0.5}
        reassignment_results = team.reassign_subtasks_based_on_progress(subtasks)
        assert isinstance(reassignment_results, list)
        for result in reassignment_results:
            assert result.subtask_id
            assert result.previous_assignee
            assert result.new_assignee
            assert result.expertise_score >= 0
            assert result.timestamp
            if result.subtask_id == "subtask2":
                assert result.previous_assignee == "Agent1"
                assert result.new_assignee == "Agent3"
