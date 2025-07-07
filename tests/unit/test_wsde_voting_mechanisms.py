"""
Unit Tests for WSDE Voting Mechanisms

This file contains unit tests for the voting mechanisms in the WSDE model,
specifically testing the vote_on_critical_decision method in the WSDETeam class.
"""

import pytest
from unittest.mock import MagicMock, patch

from devsynth.domain.models.wsde import WSDETeam
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.application.agents.unified_agent import UnifiedAgent


class TestWSDEVotingMechanisms:
    """Test suite for the WSDE voting mechanisms."""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name="test_voting_mechanisms_team")

        # Create mock agents with different expertise
        self.agent1 = MagicMock()
        self.agent1.name = "agent1"
        self.agent1.config = MagicMock()
        self.agent1.config.name = "agent1"
        self.agent1.config.parameters = {"expertise": ["python", "design"]}

        self.agent2 = MagicMock()
        self.agent2.name = "agent2"
        self.agent2.config = MagicMock()
        self.agent2.config.name = "agent2"
        self.agent2.config.parameters = {"expertise": ["javascript", "testing"]}

        self.agent3 = MagicMock()
        self.agent3.name = "agent3"
        self.agent3.config = MagicMock()
        self.agent3.config.name = "agent3"
        self.agent3.config.parameters = {"expertise": ["documentation", "planning"]}

        self.agent4 = MagicMock()
        self.agent4.name = "agent4"
        self.agent4.config = MagicMock()
        self.agent4.config.name = "agent4"
        self.agent4.config.parameters = {"expertise": ["architecture", "security"]}

        # Add agents to the team
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)

        # Create a critical decision task
        self.critical_task = {
            "type": "critical_decision",
            "description": "Choose the best architecture for the system",
            "options": [
                {
                    "id": "option1",
                    "name": "Microservices",
                    "description": "Use a microservices architecture",
                },
                {
                    "id": "option2",
                    "name": "Monolith",
                    "description": "Use a monolithic architecture",
                },
                {
                    "id": "option3",
                    "name": "Serverless",
                    "description": "Use a serverless architecture",
                },
            ],
            "is_critical": True,
        }

        # Create a domain-specific critical decision task
        self.domain_task = {
            "type": "critical_decision",
            "domain": "security",
            "description": "Choose the authentication method for the system",
            "options": [
                {
                    "id": "option1",
                    "name": "OAuth",
                    "description": "Use OAuth for authentication",
                },
                {
                    "id": "option2",
                    "name": "JWT",
                    "description": "Use JWT for authentication",
                },
                {
                    "id": "option3",
                    "name": "Basic Auth",
                    "description": "Use Basic Auth for authentication",
                },
            ],
            "is_critical": True,
        }

    def test_vote_on_critical_decision_initiates_voting(self):
        """Test that vote_on_critical_decision initiates a voting process."""
        # Mock the agents' process method to return votes
        self.agent1.process = MagicMock(return_value={"vote": "option1"})
        self.agent2.process = MagicMock(return_value={"vote": "option2"})
        self.agent3.process = MagicMock(return_value={"vote": "option3"})
        self.agent4.process = MagicMock(return_value={"vote": "option1"})

        # Call the method
        result = self.team.vote_on_critical_decision(self.critical_task)

        # Verify that voting was initiated
        assert "voting_initiated" in result
        assert result["voting_initiated"] is True

        # Verify that all agents were asked to vote
        self.agent1.process.assert_called_once()
        self.agent2.process.assert_called_once()
        self.agent3.process.assert_called_once()
        self.agent4.process.assert_called_once()

        # Verify that the votes were recorded
        assert "votes" in result
        assert len(result["votes"]) == 4
        assert result["votes"]["agent1"] == "option1"
        assert result["votes"]["agent2"] == "option2"
        assert result["votes"]["agent3"] == "option3"
        assert result["votes"]["agent4"] == "option1"

    def test_vote_on_critical_decision_majority_vote(self):
        """Test that vote_on_critical_decision uses majority vote to make decisions."""
        # Mock the agents' process method to return votes
        self.agent1.process = MagicMock(return_value={"vote": "option1"})
        self.agent2.process = MagicMock(return_value={"vote": "option2"})
        self.agent3.process = MagicMock(return_value={"vote": "option1"})
        self.agent4.process = MagicMock(return_value={"vote": "option3"})

        # Call the method
        result = self.team.vote_on_critical_decision(self.critical_task)

        # Verify that the result includes the winner
        assert "result" in result
        assert result["result"] is not None
        assert "winner" in result["result"]
        assert result["result"]["winner"] == "option1"

        # Verify that the vote counts are correct
        assert "vote_counts" in result["result"]
        assert result["result"]["vote_counts"]["option1"] == 2
        assert result["result"]["vote_counts"]["option2"] == 1
        assert result["result"]["vote_counts"]["option3"] == 1

        # Verify that the method is majority_vote
        assert "method" in result["result"]
        assert result["result"]["method"] == "majority_vote"

    def test_vote_on_critical_decision_tied_vote(self):
        """Test that vote_on_critical_decision handles tied votes correctly."""
        # Mock the agents' process method to return votes that result in a tie
        self.agent1.process = MagicMock(return_value={"vote": "option1"})
        self.agent2.process = MagicMock(return_value={"vote": "option2"})
        self.agent3.process = MagicMock(return_value={"vote": "option1"})
        self.agent4.process = MagicMock(return_value={"vote": "option2"})

        # Mock the build_consensus method to return a consensus result
        self.team.build_consensus = MagicMock(
            return_value={
                "consensus": "Use a hybrid architecture combining microservices and monolith",
                "contributors": ["agent1", "agent2", "agent3", "agent4"],
                "method": "consensus_synthesis",
                "reasoning": "Combined the best elements from both options",
            }
        )

        # Call the method
        result = self.team.vote_on_critical_decision(self.critical_task)

        # Verify that the result indicates a tied vote
        assert "result" in result
        assert "tied" in result["result"]
        assert result["result"]["tied"] is True

        # Verify that the tied options are correct
        assert "tied_options" in result["result"]
        assert "option1" in result["result"]["tied_options"]
        assert "option2" in result["result"]["tied_options"]

        # Verify that the vote counts are correct
        assert "vote_counts" in result["result"]
        assert result["result"]["vote_counts"]["option1"] == 2
        assert result["result"]["vote_counts"]["option2"] == 2

        # Verify that the method is tied_vote
        assert "method" in result["result"]
        assert result["result"]["method"] == "tied_vote"

        # Verify that the consensus fallback was used
        assert "fallback" in result["result"]
        assert result["result"]["fallback"] == "consensus"
        assert "consensus_result" in result["result"]
        assert result["result"]["consensus_result"]["method"] == "consensus_synthesis"

    def test_vote_on_critical_decision_weighted_vote(self):
        """Test that vote_on_critical_decision uses weighted voting for domain-specific decisions."""
        # Set up agents with different expertise levels in the security domain
        self.agent1.config.parameters = {
            "expertise": ["security", "encryption", "authentication"],
            "expertise_level": "expert",
        }
        self.agent2.config.parameters = {
            "expertise": ["security", "firewalls"],
            "expertise_level": "intermediate",
        }
        self.agent3.config.parameters = {
            "expertise": ["security"],
            "expertise_level": "novice",
        }
        self.agent4.config.parameters = {
            "expertise": ["python", "javascript"],
            "expertise_level": "intermediate",
        }

        # Mock the agents' process method to return votes
        self.agent1.process = MagicMock(
            return_value={"vote": "option2"}
        )  # Expert votes for JWT
        self.agent2.process = MagicMock(
            return_value={"vote": "option1"}
        )  # Intermediate votes for OAuth
        self.agent3.process = MagicMock(
            return_value={"vote": "option1"}
        )  # Novice votes for OAuth
        self.agent4.process = MagicMock(
            return_value={"vote": "option3"}
        )  # Other agent votes for Basic Auth

        # Call the method
        result = self.team.vote_on_critical_decision(self.domain_task)

        # Verify that the result includes vote weights
        assert "vote_weights" in result
        assert len(result["vote_weights"]) == 4

        # Verify that the weights are assigned correctly
        assert (
            result["vote_weights"]["agent1"] > result["vote_weights"]["agent2"]
        )  # Expert > Intermediate
        assert (
            result["vote_weights"]["agent2"] > result["vote_weights"]["agent3"]
        )  # Intermediate > Novice
        assert (
            result["vote_weights"]["agent3"] > result["vote_weights"]["agent4"]
        )  # Domain novice > Non-domain

        # Verify that the weighted votes are calculated correctly
        assert "weighted_votes" in result

        # Verify that the result includes the winner
        assert "result" in result
        assert "winner" in result["result"]

        # Verify that the method is weighted_vote
        assert "method" in result["result"]
        assert result["result"]["method"] == "weighted_vote"

        # Verify that the expert's vote (option2) wins despite more agents voting for option1
        assert result["result"]["winner"] == "option2"

    def test_vote_on_critical_decision_records_results(self):
        """Test that vote_on_critical_decision records the voting results."""
        # Mock the agents' process method to return votes
        self.agent1.process = MagicMock(return_value={"vote": "option1"})
        self.agent2.process = MagicMock(return_value={"vote": "option2"})
        self.agent3.process = MagicMock(return_value={"vote": "option1"})
        self.agent4.process = MagicMock(return_value={"vote": "option1"})

        # Call the method
        result = self.team.vote_on_critical_decision(self.critical_task)

        # Verify that the result includes all the necessary information
        assert "voting_initiated" in result
        assert "votes" in result
        assert "result" in result
        assert "winner" in result["result"]
        assert "vote_counts" in result["result"]
        assert "method" in result["result"]

        # Verify that the vote counts are correct
        assert result["result"]["vote_counts"]["option1"] == 3
        assert result["result"]["vote_counts"]["option2"] == 1

        # Verify that the winning option is included
        assert "winning_option" in result["result"]
        assert result["result"]["winning_option"]["id"] == "option1"
        assert result["result"]["winning_option"]["name"] == "Microservices"

    def test_vote_on_critical_decision_updates_history(self):
        """Ensure voting history is recorded after a vote."""
        self.agent1.process = MagicMock(return_value={"vote": "option1"})
        self.agent2.process = MagicMock(return_value={"vote": "option2"})
        self.agent3.process = MagicMock(return_value={"vote": "option1"})
        self.agent4.process = MagicMock(return_value={"vote": "option1"})

        result = self.team.vote_on_critical_decision(self.critical_task)

        assert len(self.team.voting_history) == 1
        entry = self.team.voting_history[0]
        assert entry["task_id"] == self.team._get_task_id(self.critical_task)
        assert entry["result"] == result["result"]
