"""
Unit Tests for WSDE Models

This file contains unit tests for the WSDE (Worker Self-Directed Enterprise) models,
focusing on the WSDETeam class and its functionality.
"""

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from devsynth.domain.models.wsde_facade import WSDE, WSDETeam


class TestWSDETeam:
    """Test suite for the WSDETeam class.

    ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name="test_team")
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
        self.critic_agent = MagicMock()
        self.critic_agent.name = "critic"
        self.critic_agent.current_role = None
        self.critic_agent.parameters = {
            "expertise": ["critique", "dialectical_reasoning"]
        }

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up the team and all mock agents
        self.team = None
        self.agent1 = None
        self.agent2 = None
        self.agent3 = None
        self.agent4 = None
        self.critic_agent = None

    @pytest.mark.fast
    def test_add_agent_succeeds(self):
        """Test adding an agent to the team.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        assert len(self.team.agents) == 1
        assert self.team.agents[0] == self.agent1

    @pytest.mark.fast
    def test_dialectical_hook_invoked_on_add_solution_succeeds(self):
        """Registered dialectical hooks should run when a solution is added.

        ReqID: N/A"""
        called: dict[str, Any] = {}

        def hook(task: dict[str, Any], solutions: list[dict[str, Any]]):
            called["task"] = task
            called["solutions"] = list(solutions)

        self.team.register_dialectical_hook(hook)
        task = {"id": "task1"}
        solution = {"agent": "a1", "content": "foo"}
        self.team.add_solution(task, solution)
        assert called["task"] == task
        assert called["solutions"][0] == solution

    @pytest.mark.fast
    def test_rotate_primus_succeeds(self):
        """Test rotating the Primus role.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        initial_primus_index = self.team.primus_index
        self.team.rotate_primus()
        assert self.team.primus_index != initial_primus_index
        assert self.team.primus_index == (initial_primus_index + 1) % len(
            self.team.agents
        )

    @pytest.mark.fast
    def test_get_primus_succeeds(self):
        """Test getting the current Primus agent.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.primus_index = 1
        primus = self.team.get_primus()
        assert primus == self.agent2

    @pytest.mark.fast
    def test_get_primus_empty_team_succeeds(self):
        """Test getting the Primus agent from an empty team.

        ReqID: N/A"""
        primus = self.team.get_primus()
        assert primus is None

    @pytest.mark.fast
    def test_assign_roles_succeeds(self):
        """Test assigning WSDE roles to agents.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)
        self.team.primus_index = 0
        self.team.assign_roles()
        assert self.agent1.current_role == "Primus"
        assert self.agent2.current_role in [
            "Worker",
            "Supervisor",
            "Designer",
            "Evaluator",
        ]
        assert self.agent3.current_role in [
            "Worker",
            "Supervisor",
            "Designer",
            "Evaluator",
        ]
        assert self.agent4.current_role in [
            "Worker",
            "Supervisor",
            "Designer",
            "Evaluator",
        ]
        roles = [
            self.agent2.current_role,
            self.agent3.current_role,
            self.agent4.current_role,
        ]
        assert "Worker" in roles
        assert "Supervisor" in roles
        assert "Designer" in roles or "Evaluator" in roles

    @pytest.mark.fast
    def test_get_agent_by_role_succeeds(self):
        """Test getting agents by their role.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)
        self.team.primus_index = 0
        self.team.assign_roles()
        assert self.team.get_primus() == self.agent1
        worker_agent = None
        for agent in [self.agent2, self.agent3, self.agent4]:
            if agent.current_role == "Worker":
                worker_agent = agent
                break
        assert self.team.get_worker() == worker_agent
        for role, method in [
            ("Supervisor", self.team.get_supervisor),
            ("Designer", self.team.get_designer),
            ("Evaluator", self.team.get_evaluator),
        ]:
            role_agent = None
            for agent in [self.agent2, self.agent3, self.agent4]:
                if agent.current_role == role:
                    role_agent = agent
                    break
            assert method() == role_agent

    @pytest.mark.fast
    def test_assign_roles_with_rotation_succeeds(self):
        """Test that role assignments change when the Primus rotates.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        self.team.add_agent(self.agent3)
        self.team.add_agent(self.agent4)
        self.team.primus_index = 0
        self.team.assign_roles()
        initial_roles = {
            self.agent1.name: self.agent1.current_role,
            self.agent2.name: self.agent2.current_role,
            self.agent3.name: self.agent3.current_role,
            self.agent4.name: self.agent4.current_role,
        }
        self.team.rotate_primus()
        self.team.assign_roles()
        assert self.agent1.current_role != initial_roles[self.agent1.name]
        assert self.agent2.current_role == "Primus"
        roles = [
            self.agent1.current_role,
            self.agent3.current_role,
            self.agent4.current_role,
        ]
        assert "Worker" in roles
        assert "Supervisor" in roles
        assert "Designer" in roles or "Evaluator" in roles

    @pytest.mark.fast
    def test_apply_dialectical_reasoning_with_knowledge_graph_succeeds(self):
        """Test applying dialectical reasoning with knowledge graph integration.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        self.team.add_agent(self.agent2)
        task = {
            "id": "task1",
            "type": "code_generation",
            "description": "Implement a secure authentication system",
            "requirements": ["user authentication", "password security"],
        }
        solution = {
            "id": "solution1",
            "agent": "agent1",
            "content": """def authenticate(username, password):
    return username == 'admin' and password == 'password'""",
            "description": "Simple authentication function",
        }
        self.team.solutions = {task["id"]: [solution]}
        mock_wsde_memory = MagicMock()
        mock_wsde_memory.query_knowledge_for_task.return_value = [
            {"concept": "authentication", "relevance": 0.9},
            {"concept": "password", "relevance": 0.8},
            {"concept": "security", "relevance": 0.7},
        ]
        mock_wsde_memory.query_concept_relationships.return_value = [
            {"relationship": "requires", "direction": "outgoing"}
        ]
        result = self.team.apply_dialectical_reasoning_with_knowledge_graph(
            task, self.critic_agent, mock_wsde_memory
        )
        assert "thesis" in result
        assert "antithesis" in result
        assert "synthesis" in result
        assert "evaluation" in result
        assert "knowledge_graph_insights" in result
        assert "relevant_concepts" in result["knowledge_graph_insights"]
        assert "concept_relationships" in result["knowledge_graph_insights"]
        assert "task_relevant_knowledge" in result["knowledge_graph_insights"]
        mock_wsde_memory.query_knowledge_for_task.assert_called_once_with(task)
        assert mock_wsde_memory.query_concept_relationships.called
        assert "critique_categories" in result["antithesis"]
        assert "security" in result["antithesis"]["critique_categories"]
        assert "addressed_critiques" in result["synthesis"]
        assert "knowledge_alignment" in result["evaluation"]
        assert "alignment_score" in result["evaluation"]
        assert "alignment_level" in result["evaluation"]


class TestWSDE:
    """Test suite for the WSDE class.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_initialization_succeeds(self):
        """Test that a WSDE is initialized correctly.

        ReqID: N/A"""
        wsde = WSDE(name="Test WSDE")
        assert wsde.name == "Test WSDE"
        assert wsde.description is None
        assert wsde.metadata is None
        assert isinstance(wsde.created_at, datetime)
        assert wsde.updated_at == wsde.created_at

    @pytest.mark.fast
    def test_initialization_with_metadata_succeeds(self):
        """Test that a WSDE is initialized correctly with metadata.

        ReqID: N/A"""
        metadata = {"key": "value", "another_key": 123}
        wsde = WSDE(name="Test WSDE", metadata=metadata)
        assert wsde.name == "Test WSDE"
        assert wsde.metadata == metadata
        assert wsde.metadata["key"] == "value"
        assert wsde.metadata["another_key"] == 123
