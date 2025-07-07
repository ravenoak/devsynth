"""
Unit tests for the CollaborativeWSDETeam class.

This file contains tests for the enhanced consensus building functionality
in the CollaborativeWSDETeam class.
"""
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


class TestCollaborativeWSDETeam:
    """Tests for the CollaborativeWSDETeam class."""

    def test_initialization(self):
        """Test that the CollaborativeWSDETeam initializes correctly."""
        team = CollaborativeWSDETeam()
        assert team.consensus_mode == "enabled"
        assert hasattr(team, "agent_opinions")
        assert hasattr(team, "decision_documentation")

    def test_build_consensus_no_conflicts(self, mock_agent_with_expertise):
        """Test building consensus when there are no conflicts."""
        team = CollaborativeWSDETeam()

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
            "type": "decision_task",
            "description": "Choose a database technology",
            "options": [
                {"id": "option1", "name": "PostgreSQL"},
                {"id": "option2", "name": "MongoDB"},
                {"id": "option3", "name": "MySQL"}
            ]
        }

        # Add solutions
        solution1 = {"agent": "Agent1", "content": "I recommend PostgreSQL for its robustness."}
        solution2 = {"agent": "Agent2", "content": "I recommend MongoDB for its flexibility."}
        solution3 = {"agent": "Agent3", "content": "I recommend MySQL for its simplicity."}

        team.add_solution(task, solution1)
        team.add_solution(task, solution2)
        team.add_solution(task, solution3)

        # Build consensus
        consensus_result = team.build_consensus(task)

        # Verify the result
        assert "identified_conflicts" in consensus_result
        assert len(consensus_result["identified_conflicts"]) == 0
        assert "resolution_process" in consensus_result
        assert "steps" in consensus_result["resolution_process"]
        assert consensus_result["resolution_process"]["steps"][0]["description"] == "No conflicts identified"
        assert "agent_reasoning" in consensus_result
        assert "key_concerns" in consensus_result
        assert "addressed_concerns" in consensus_result
        assert "documentation" in consensus_result

    def test_build_consensus_with_conflicts(self, mock_agent_with_expertise):
        """Test building consensus when there are conflicts."""
        team = CollaborativeWSDETeam()

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"], 8)
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"], 7)
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"], 9)

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create a task
        task = {
            "id": "task1",
            "type": "decision_task",
            "description": "Choose a database technology",
            "options": [
                {"id": "option1", "name": "PostgreSQL"},
                {"id": "option2", "name": "MongoDB"},
                {"id": "option3", "name": "MySQL"}
            ]
        }

        # Set conflicting opinions
        team.set_agent_opinion(agent1, "option1", "strongly_favor")
        team.set_agent_opinion(agent2, "option2", "strongly_favor")
        team.set_agent_opinion(agent3, "option1", "favor")

        # Add solutions
        solution1 = {"agent": "Agent1", "content": "I recommend PostgreSQL for its robustness."}
        solution2 = {"agent": "Agent2", "content": "I recommend MongoDB for its flexibility."}
        solution3 = {"agent": "Agent3", "content": "I recommend PostgreSQL for its security features."}

        team.add_solution(task, solution1)
        team.add_solution(task, solution2)
        team.add_solution(task, solution3)

        # Build consensus
        consensus_result = team.build_consensus(task)

        # Verify the result
        assert "identified_conflicts" in consensus_result
        assert len(consensus_result["identified_conflicts"]) > 0
        assert "resolution_process" in consensus_result
        assert "steps" in consensus_result["resolution_process"]
        assert "agent_reasoning" in consensus_result
        assert "key_concerns" in consensus_result
        assert "addressed_concerns" in consensus_result
        assert "consensus" in consensus_result
        assert "consensus_decision" in consensus_result
        assert "documentation" in consensus_result

    def test_vote_on_critical_decision_with_expertise_weighting(self, mock_agent_with_expertise):
        """Test voting on a critical decision with expertise weighting."""
        team = CollaborativeWSDETeam()

        # Create agents with different expertise levels
        backend_expert = mock_agent_with_expertise("BackendExpert", ["python", "databases", "sql"], 9)
        frontend_dev = mock_agent_with_expertise("FrontendDev", ["javascript", "ui"], 7)
        security_expert = mock_agent_with_expertise("SecurityExpert", ["security", "encryption"], 8)

        # Add agents to the team
        team.add_agent(backend_expert)
        team.add_agent(frontend_dev)
        team.add_agent(security_expert)

        # Create a task in the database domain
        task = {
            "id": "db_decision",
            "type": "critical_decision",
            "domain": "databases",
            "description": "Choose a database technology",
            "options": [
                {"id": "postgres", "name": "PostgreSQL"},
                {"id": "mongodb", "name": "MongoDB"}
            ]
        }

        # Mock the process method to return votes
        backend_expert.process = MagicMock(return_value={"vote": "postgres"})
        frontend_dev.process = MagicMock(return_value={"vote": "mongodb"})
        security_expert.process = MagicMock(return_value={"vote": "mongodb"})

        # Vote on the decision
        result = team.vote_on_critical_decision(task)

        # Verify the result
        assert "vote_weights" in result
        assert result["vote_weights"]["BackendExpert"] > result["vote_weights"]["FrontendDev"]
        assert result["vote_weights"]["BackendExpert"] > result["vote_weights"]["SecurityExpert"]
        assert result["result"]["method"] == "weighted_vote"
        assert result["result"]["winner"] == "postgres"  # Backend expert's vote should win due to higher weight

    def test_tie_breaking_strategies(self, mock_agent_with_expertise):
        """Test tie-breaking strategies in voting."""
        team = CollaborativeWSDETeam()

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python"], 7)
        agent2 = mock_agent_with_expertise("Agent2", ["javascript"], 7)
        agent3 = mock_agent_with_expertise("Agent3", ["security"], 7)
        agent4 = mock_agent_with_expertise("Agent4", ["devops"], 7)

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        team.add_agent(agent4)

        # Create a task
        task = {
            "id": "tie_decision",
            "type": "critical_decision",
            "description": "Choose a technology",
            "options": [
                {"id": "option1", "name": "Option 1"},
                {"id": "option2", "name": "Option 2"}
            ]
        }

        # Force a tie
        team.force_voting_tie(task)

        # Mock the process method to return votes (2 for each option)
        agent1.process = MagicMock(return_value={"vote": "option1"})
        agent2.process = MagicMock(return_value={"vote": "option1"})
        agent3.process = MagicMock(return_value={"vote": "option2"})
        agent4.process = MagicMock(return_value={"vote": "option2"})

        # Vote on the decision
        result = team.vote_on_critical_decision(task)

        # Verify the result
        assert "result_type" in result
        assert result["result_type"] == "tie"
        assert "tie_resolution" in result
        assert "strategies_applied" in result["tie_resolution"]
        assert len(result["tie_resolution"]["strategies_applied"]) > 0
        assert "selected_option" in result
        assert "tie_breaking_rationale" in result["selected_option"]

    def test_decision_tracking_and_explanation(self, mock_agent_with_expertise):
        """Test decision tracking and explanation."""
        team = CollaborativeWSDETeam()

        # Create agents
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"], 8)
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"], 7)
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"], 9)

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create a task
        task = {
            "id": "tracked_decision",
            "type": "decision_task",
            "description": "Choose a technology stack",
            "criticality": "high",
            "options": [
                {"id": "stack1", "name": "Stack 1"},
                {"id": "stack2", "name": "Stack 2"},
                {"id": "stack3", "name": "Stack 3"}
            ]
        }

        # Set opinions
        team.set_agent_opinion(agent1, "stack1", "strongly_favor")
        team.set_agent_opinion(agent2, "stack2", "favor")
        team.set_agent_opinion(agent3, "stack1", "favor")

        # Build consensus
        consensus_result = team.build_consensus(task)

        # Mark the decision as implemented
        team.mark_decision_implemented(task["id"])

        # Add implementation details
        implementation_details = {
            "implemented_by": "development_team",
            "implementation_date": "2025-07-10",
            "implementation_status": "completed",
            "verification_status": "verified"
        }

        team.add_decision_implementation_details(task["id"], implementation_details)

        # Get the tracked decision
        tracked_decision = team.get_tracked_decision(task["id"])

        # Verify the tracked decision
        assert "metadata" in tracked_decision
        assert "decision_date" in tracked_decision["metadata"]
        assert "decision_maker" in tracked_decision["metadata"]
        assert "criticality" in tracked_decision["metadata"]
        assert "implementation_status" in tracked_decision["metadata"]
        assert "verification_status" in tracked_decision["metadata"]

        assert "voting_results" in tracked_decision
        assert "rationale" in tracked_decision
        assert "expertise_references" in tracked_decision["rationale"]
        assert "considerations" in tracked_decision["rationale"]

        assert "stakeholder_explanation" in tracked_decision
        assert "readability_score" in tracked_decision

        # Query decisions
        high_criticality_decisions = team.query_decisions(criticality="high")
        assert len(high_criticality_decisions) > 0
        assert task["id"] in [decision["id"] for decision in high_criticality_decisions]

        implemented_decisions = team.query_decisions(implementation_status="completed")
        assert len(implemented_decisions) > 0
        assert task["id"] in [decision["id"] for decision in implemented_decisions]
