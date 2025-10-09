"""
Unit tests for the CollaborativeWSDETeam class.

This file contains tests for the enhanced consensus building functionality
in the CollaborativeWSDETeam class.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.dto import (
    ConflictRecord,
    ConsensusOutcome,
    SynthesisArtifact,
)
from devsynth.application.collaboration.wsde_team_extended import CollaborativeWSDETeam


class _StubAgent:
    """Minimal protocol for agent mocks used in collaboration tests."""

    name: str
    agent_type: str
    current_role: str | None
    expertise: list[str]
    experience_level: int
    has_been_primus: bool

    def process(
        self, inputs: dict[str, Any]
    ) -> dict[str, Any]:  # pragma: no cover - protocol
        raise NotImplementedError


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock(spec=_StubAgent)
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
        agent = MagicMock(spec=_StubAgent)
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
                "solution": f"Solution crafted by {name}",
                "confidence": 0.9,
            }

        agent.process = mock_process
        return agent

    return _create_agent


class TestCollaborativeWSDETeam:
    """Tests for the CollaborativeWSDETeam class.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_initialization_succeeds(self):
        """Test that the CollaborativeWSDETeam initializes correctly.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TestTeam")
        assert hasattr(team, "tracked_decisions")
        assert hasattr(team, "subtasks")
        assert hasattr(team, "subtask_progress")
        assert hasattr(team, "contribution_metrics")
        assert hasattr(team, "role_history")

    @pytest.mark.medium
    def test_build_consensus_no_conflicts_succeeds(self, mock_agent_with_expertise):
        """Test building consensus when there are no conflicts.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="ConsensusTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"])
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"])
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        task = {
            "id": "task1",
            "type": "decision_task",
            "description": "Choose a database technology",
            "options": [
                {"id": "option1", "name": "PostgreSQL"},
                {"id": "option2", "name": "MongoDB"},
                {"id": "option3", "name": "MySQL"},
            ],
        }

        def mock_get_messages(agent=None, filters=None):
            if agent == "Agent1" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent1",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer PostgreSQL",
                            "rationale": "It's robust and reliable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            elif agent == "Agent2" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent2",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer PostgreSQL",
                            "rationale": "It has good performance",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            elif agent == "Agent3" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent3",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer PostgreSQL",
                            "rationale": "It's secure and stable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            return []

        with patch.object(team, "get_messages", side_effect=mock_get_messages):
            with patch.object(team, "_identify_conflicts", return_value=[]):
                consensus_result = team.build_consensus(task)
                assert isinstance(consensus_result, ConsensusOutcome)
                assert consensus_result.task_id == task["id"]
                assert consensus_result.method == "majority_opinion"
                assert len(consensus_result.agent_opinions) == 3
                assert consensus_result.majority_opinion is not None
                assert consensus_result.timestamp is not None
                assert consensus_result.conflicts_identified == 0
                assert tuple(consensus_result.participants) == (
                    "Agent1",
                    "Agent2",
                    "Agent3",
                )
                opinion_ids = [
                    record.agent_id for record in consensus_result.agent_opinions
                ]
                assert opinion_ids == sorted(opinion_ids)
                serialized = consensus_result.to_dict()
                assert serialized["dto_type"] == "ConsensusOutcome"
                assert serialized["agent_opinions"][0]["agent_id"] == "Agent1"
                assert "Next steps" in (consensus_result.stakeholder_explanation or "")

    @pytest.mark.medium
    def test_research_persona_assignments_emit_telemetry(
        self, mock_agent_with_expertise
    ) -> None:
        """Research personas should drive primus selection and telemetry."""

        team = CollaborativeWSDETeam(name="ResearchTeam")
        lead = mock_agent_with_expertise(
            "Lead",
            ["leadership coordination", "strategic research"],
        )
        bibliographer = mock_agent_with_expertise(
            "Biblio",
            ["evaluator analysis", "source catalogue"],
        )
        synthesist = mock_agent_with_expertise(
            "Synth",
            ["design synthesis", "analysis integration"],
        )

        team.add_agent(lead)
        team.add_agent(bibliographer)
        team.add_agent(synthesist)
        team.configure_research_personas(
            ["Research Lead", "Bibliographer", "Synthesist"]
        )

        task = {
            "id": "research-001",
            "type": "research_task",
            "description": "Investigate coordination approaches for architecture",
            "phase": "explore",
            "is_research": True,
            "required_expertise": ["leadership", "analysis", "design"],
        }

        result = team.process_task(task)
        primus = team.get_primus()
        assert primus is lead

        persona_assignments = result.get("research_persona_assignments", {})
        assert persona_assignments["Research Lead"] == "Lead"
        assert persona_assignments["Bibliographer"] == "Biblio"

        events = team.drain_persona_events()
        assert events and any(event["persona"] == "Synthesist" for event in events)

        transitions = team.transition_metrics.get("persona_transitions", [])
        assert transitions
        latest_transition = transitions[-1]
        assert latest_transition["assignments"]["Research Lead"] == "Lead"
        assert latest_transition["fallback"] is False

    @pytest.mark.medium
    def test_build_consensus_with_conflicts_succeeds(self, mock_agent_with_expertise):
        """Test building consensus when there are conflicts.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="ConflictTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"], 8)
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"], 7)
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"], 9)
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        task = {
            "id": "task1",
            "type": "decision_task",
            "description": "Choose a database technology",
            "options": [
                {"id": "option1", "name": "PostgreSQL"},
                {"id": "option2", "name": "MongoDB"},
                {"id": "option3", "name": "MySQL"},
            ],
        }

        def mock_get_messages(agent=None, filters=None):
            if agent == "Agent1" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent1",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer PostgreSQL",
                            "rationale": "It's robust and reliable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            elif agent == "Agent2" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent2",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer MongoDB",
                            "rationale": "It's flexible and scalable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            elif agent == "Agent3" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent3",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer PostgreSQL",
                            "rationale": "It's secure and stable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            return []

        conflicts = [
            ConflictRecord(
                conflict_id="conflict-0",
                task_id=task["id"],
                agent_a="Agent1",
                agent_b="Agent2",
                opinion_a="I prefer PostgreSQL",
                opinion_b="I prefer MongoDB",
                rationale_a="It's robust and reliable",
                rationale_b="It's flexible and scalable",
                severity_label="high",
                severity_score=0.8,
            )
        ]
        synthesis = SynthesisArtifact(
            text=(
                "After considering all perspectives, PostgreSQL is recommended for "
                "its robustness, security, and stability."
            ),
            key_points=(
                "PostgreSQL is robust",
                "PostgreSQL is secure",
                "PostgreSQL is stable",
            ),
            readability_score={"flesch_reading_ease": 75.0},
        )
        with patch.object(team, "get_messages", side_effect=mock_get_messages):
            with patch.object(team, "_identify_conflicts", return_value=conflicts):
                with patch.object(
                    team,
                    "_generate_conflict_resolution_synthesis",
                    return_value=synthesis,
                ):
                    consensus_result = team.build_consensus(task)
                    assert isinstance(consensus_result, ConsensusOutcome)
                    assert consensus_result.task_id == task["id"]
                    assert consensus_result.method == "conflict_resolution_synthesis"
                    assert consensus_result.conflicts_identified == len(conflicts)
                    assert consensus_result.synthesis is not None
                    assert len(consensus_result.agent_opinions) == 3
                    assert consensus_result.timestamp is not None
                    assert consensus_result.majority_opinion is None
                    conflict_ids = [
                        conflict.conflict_id for conflict in consensus_result.conflicts
                    ]
                    assert conflict_ids == sorted(conflict_ids)
                    serialized = consensus_result.to_dict()
                    assert serialized["conflicts"] == [
                        conflict.to_dict() if hasattr(conflict, "to_dict") else conflict
                        for conflict in consensus_result.conflicts
                    ]
                    assert serialized["synthesis"]["dto_type"] == "SynthesisArtifact"
                    assert "Next steps" in (
                        consensus_result.stakeholder_explanation or ""
                    )

    @pytest.mark.medium
    def test_vote_on_critical_decision_with_expertise_weighting_succeeds(
        self, mock_agent_with_expertise
    ):
        """Test voting on a critical decision with expertise weighting.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="VotingTeam")
        backend_expert = mock_agent_with_expertise(
            "BackendExpert", ["python", "databases", "sql"], 9
        )
        frontend_dev = mock_agent_with_expertise("FrontendDev", ["javascript", "ui"], 7)
        security_expert = mock_agent_with_expertise(
            "SecurityExpert", ["security", "encryption"], 8
        )
        team.add_agent(backend_expert)
        team.add_agent(frontend_dev)
        team.add_agent(security_expert)
        task = {
            "id": "db_decision",
            "type": "critical_decision",
            "domain": "databases",
            "description": "Choose a database technology",
            "options": [
                {"id": "postgres", "name": "PostgreSQL"},
                {"id": "mongodb", "name": "MongoDB"},
            ],
        }
        backend_expert.process = MagicMock(return_value={"vote": "postgres"})
        frontend_dev.process = MagicMock(return_value={"vote": "mongodb"})
        security_expert.process = MagicMock(return_value={"vote": "mongodb"})
        expected_result = {
            "vote_weights": {
                "BackendExpert": 0.9,
                "FrontendDev": 0.3,
                "SecurityExpert": 0.5,
            },
            "votes": {
                "BackendExpert": "postgres",
                "FrontendDev": "mongodb",
                "SecurityExpert": "mongodb",
            },
            "result": {"method": "weighted_vote", "winner": "postgres"},
        }
        with patch.object(
            team, "vote_on_critical_decision", return_value=expected_result
        ):
            result = team.vote_on_critical_decision(task)
            assert "vote_weights" in result
            assert (
                result["vote_weights"]["BackendExpert"]
                > result["vote_weights"]["FrontendDev"]
            )
            assert (
                result["vote_weights"]["BackendExpert"]
                > result["vote_weights"]["SecurityExpert"]
            )
            assert result["result"]["method"] == "weighted_vote"
            assert result["result"]["winner"] == "postgres"

    @pytest.mark.medium
    def test_tie_breaking_strategies_succeeds(self, mock_agent_with_expertise):
        """Test tie-breaking strategies in voting.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TieBreakingTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python"], 7)
        agent2 = mock_agent_with_expertise("Agent2", ["javascript"], 7)
        agent3 = mock_agent_with_expertise("Agent3", ["security"], 7)
        agent4 = mock_agent_with_expertise("Agent4", ["devops"], 7)
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        team.add_agent(agent4)
        task = {
            "id": "tie_decision",
            "type": "critical_decision",
            "description": "Choose a technology",
            "options": [
                {"id": "option1", "name": "Option 1"},
                {"id": "option2", "name": "Option 2"},
            ],
        }
        tie_result = team.force_voting_tie(task)
        assert "task_id" in tie_result
        assert tie_result["task_id"] == task["id"]
        assert "votes" in tie_result
        assert len(tie_result["votes"]) == 4
        assert "options" in tie_result
        assert len(tie_result["options"]) == 2
        assert "tied" in tie_result
        assert tie_result["tied"] is True
        assert "tied_options" in tie_result
        assert len(tie_result["tied_options"]) == 2
        assert "timestamp" in tie_result
        expected_result = {
            "result_type": "tie",
            "votes": {
                "Agent1": "option1",
                "Agent2": "option1",
                "Agent3": "option2",
                "Agent4": "option2",
            },
            "tie_resolution": {
                "strategies_applied": ["expertise_weighting", "random_selection"],
                "selected_option": "option1",
            },
            "selected_option": {
                "id": "option1",
                "name": "Option 1",
                "tie_breaking_rationale": "Selected based on expertise weighting and random selection",
            },
        }
        with patch.object(
            team, "vote_on_critical_decision", return_value=expected_result
        ):
            result = team.vote_on_critical_decision(task)
            assert "result_type" in result
            assert result["result_type"] == "tie"
            assert "tie_resolution" in result
            assert "strategies_applied" in result["tie_resolution"]
            assert len(result["tie_resolution"]["strategies_applied"]) > 0
            assert "selected_option" in result
            assert "tie_breaking_rationale" in result["selected_option"]

    @pytest.mark.medium
    def test_decision_tracking_and_explanation_succeeds(
        self, mock_agent_with_expertise
    ):
        """Test decision tracking and explanation.

        ReqID: N/A"""
        team = CollaborativeWSDETeam(name="TrackingTeam")
        agent1 = mock_agent_with_expertise("Agent1", ["python", "backend"], 8)
        agent2 = mock_agent_with_expertise("Agent2", ["javascript", "frontend"], 7)
        agent3 = mock_agent_with_expertise("Agent3", ["security", "devops"], 9)
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        task = {
            "id": "tracked_decision",
            "type": "decision_task",
            "description": "Choose a technology stack",
            "criticality": "high",
            "options": [
                {"id": "stack1", "name": "Stack 1"},
                {"id": "stack2", "name": "Stack 2"},
                {"id": "stack3", "name": "Stack 3"},
            ],
        }

        def mock_get_messages(agent=None, filters=None):
            if agent == "Agent1" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent1",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer Stack 1",
                            "rationale": "It's robust and reliable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            elif agent == "Agent2" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent2",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer Stack 2",
                            "rationale": "It's flexible and scalable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            elif agent == "Agent3" and filters.get("type") == "opinion":
                return [
                    {
                        "sender": "Agent3",
                        "type": "opinion",
                        "content": {
                            "opinion": "I prefer Stack 1",
                            "rationale": "It's secure and stable",
                        },
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"task_id": task["id"]},
                    }
                ]
            return []

        with patch.object(team, "get_messages", side_effect=mock_get_messages):
            with patch.object(team, "_identify_conflicts", return_value=[]):
                consensus_result = team.build_consensus(task)
                tracked_decision = {
                    "id": task["id"],
                    "metadata": {
                        "decision_date": datetime.now().isoformat(),
                        "decision_maker": "TrackingTeam",
                        "criticality": "high",
                        "implementation_status": "pending",
                        "verification_status": "pending",
                    },
                    "voting_results": {
                        "method": "majority_opinion",
                        "majority_opinion": "I prefer Stack 1",
                    },
                    "rationale": {
                        "expertise_references": ["python", "backend", "security"],
                        "considerations": ["robustness", "security", "stability"],
                    },
                    "stakeholder_explanation": "Stack 1 was chosen for its robustness, security, and stability.",
                    "readability_score": 75.0,
                }
                with patch.object(
                    team, "get_tracked_decision", return_value=tracked_decision
                ):
                    with patch.object(
                        team, "mark_decision_implemented", return_value=True
                    ):
                        team.mark_decision_implemented(task["id"])
                        with patch.object(
                            team,
                            "add_decision_implementation_details",
                            return_value=True,
                        ):
                            implementation_details = {
                                "implemented_by": "development_team",
                                "implementation_date": "2025-07-10",
                                "implementation_status": "completed",
                                "verification_status": "verified",
                            }
                            team.add_decision_implementation_details(
                                task["id"], implementation_details
                            )
                            tracked_decision["metadata"][
                                "implementation_status"
                            ] = "completed"
                            tracked_decision["metadata"][
                                "verification_status"
                            ] = "verified"
                            result = team.get_tracked_decision(task["id"])
                            assert "metadata" in result
                            assert "decision_date" in result["metadata"]
                            assert "decision_maker" in result["metadata"]
                            assert "criticality" in result["metadata"]
                            assert "implementation_status" in result["metadata"]
                            assert "verification_status" in result["metadata"]
                            assert "voting_results" in result
                            assert "rationale" in result
                            assert "expertise_references" in result["rationale"]
                            assert "considerations" in result["rationale"]
                            assert "stakeholder_explanation" in result
                            assert isinstance(result["readability_score"], (int, float))
                            high_criticality_decisions = [tracked_decision]
                            implemented_decisions = [tracked_decision]
                            with patch.object(
                                team,
                                "query_decisions",
                                side_effect=lambda **kwargs: (
                                    high_criticality_decisions
                                    if kwargs.get("criticality") == "high"
                                    else implemented_decisions
                                ),
                            ):
                                high_criticality_result = team.query_decisions(
                                    criticality="high"
                                )
                                assert len(high_criticality_result) > 0
                                assert task["id"] in [
                                    decision["id"]
                                    for decision in high_criticality_result
                                ]
                                implemented_result = team.query_decisions(
                                    implementation_status="completed"
                                )
                                assert len(implemented_result) > 0
                                assert task["id"] in [
                                    decision["id"] for decision in implemented_result
                                ]
