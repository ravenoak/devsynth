"""
Unit Tests for WSDE Team Model

This file contains unit tests for the WSDETeam class, which implements
the Worker Self-Directed Enterprise model.
"""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.domain.models.wsde_facade import WSDE, WSDETeam


class TestWSDETeam:
    """Test suite for the WSDETeam class.

    ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.team = WSDETeam(name="test_wsde_team")
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

    @pytest.mark.fast
    def test_add_agent_succeeds(self):
        """Test adding an agent to the team.

        ReqID: N/A"""
        self.team.add_agent(self.agent1)
        assert len(self.team.agents) == 1
        assert self.team.agents[0] == self.agent1

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
    def test_analyze_trade_offs_detects_conflicts_succeeds(self):
        """Trade-off analysis should flag options with similar scores as conflicts.

        ReqID: N/A"""
        evaluated = [
            {"id": 1, "score": 0.8},
            {"id": 2, "score": 0.78},
            {"id": 3, "score": 0.2},
        ]
        trade_offs = self.team.analyze_trade_offs(
            evaluated, conflict_detection_threshold=0.7
        )
        opt1 = next(o for o in trade_offs if o["id"] == 1)
        assert any(
            t["type"] == "conflict" and t["other_id"] == 2 for t in opt1["trade_offs"]
        )
        assert not any(
            t["type"] == "conflict" and t["other_id"] == 3 for t in opt1["trade_offs"]
        )
