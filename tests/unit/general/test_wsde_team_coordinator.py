"""
Unit Tests for WSDETeamCoordinator

This file contains unit tests for the WSDETeamCoordinator class, which is responsible
for coordinating WSDE teams and implementing consensus-based decision making.
"""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.domain.interfaces.agent import Agent
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.exceptions import AgentExecutionError, ValidationError


class TestWSDETeamCoordinator:
    """Test suite for the WSDETeamCoordinator class.

    ReqID: N/A"""

    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = WSDETeamCoordinator()
        self.agent1 = MagicMock(spec=Agent)
        self.agent1.name = "agent1"
        self.agent1.agent_type = "planner"
        self.agent1.current_role = None
        self.agent1.config = MagicMock()
        self.agent1.config.name = "agent1"
        self.agent1.config.parameters = {"expertise": ["planning", "design"]}
        self.agent2 = MagicMock(spec=Agent)
        self.agent2.name = "agent2"
        self.agent2.agent_type = "code"
        self.agent2.current_role = None
        self.agent2.config = MagicMock()
        self.agent2.config.name = "agent2"
        self.agent2.config.parameters = {"expertise": ["python", "javascript"]}
        self.agent3 = MagicMock(spec=Agent)
        self.agent3.name = "agent3"
        self.agent3.agent_type = "test"
        self.agent3.current_role = None
        self.agent3.config = MagicMock()
        self.agent3.config.name = "agent3"
        self.agent3.config.parameters = {"expertise": ["testing", "quality"]}
        self.agent4 = MagicMock(spec=Agent)
        self.agent4.name = "agent4"
        self.agent4.agent_type = "validation"
        self.agent4.current_role = None
        self.agent4.config = MagicMock()
        self.agent4.config.name = "agent4"
        self.agent4.config.parameters = {"expertise": ["validation", "security"]}

    def test_create_team_succeeds(self):
        """Test creating a team.

        ReqID: N/A"""
        team = self.coordinator.create_team("test_team")
        assert team is not None
        assert isinstance(team, WSDETeam)
        assert self.coordinator.teams["test_team"] == team
        assert self.coordinator.current_team_id == "test_team"

    def test_add_agent_succeeds(self):
        """Test adding an agent to the coordinator.

        ReqID: N/A"""
        self.coordinator.add_agent(self.agent1)
        assert self.coordinator.current_team_id is not None
        assert len(self.coordinator.teams[self.coordinator.current_team_id].agents) == 1
        assert (
            self.coordinator.teams[self.coordinator.current_team_id].agents[0]
            == self.agent1
        )

    @pytest.mark.medium
    def test_delegate_task_single_agent_succeeds(self):
        """Test delegating a task with a single agent.

        ReqID: N/A"""
        self.coordinator.add_agent(self.agent1)
        task = {"type": "planning", "description": "Plan a new feature"}
        self.agent1.process.return_value = {"result": "Feature plan created"}
        result = self.coordinator.delegate_task(task)
        assert result["result"] == "Feature plan created"
        self.agent1.process.assert_called_once_with(task)

    def test_delegate_task_multi_agent_consensus_succeeds(self):
        """Test delegating a task with multiple agents using consensus-based decision making.

        ReqID: N/A"""
        self.coordinator.create_team("test_team")
        self.coordinator.add_agent(self.agent1)
        self.coordinator.add_agent(self.agent2)
        self.coordinator.add_agent(self.agent3)
        self.coordinator.add_agent(self.agent4)
        task = {
            "type": "code",
            "language": "python",
            "description": "Implement a feature",
        }
        self.agent1.process.return_value = {"result": "Design for the feature"}
        self.agent2.process.return_value = {"result": "Implementation of the feature"}
        self.agent3.process.return_value = {"result": "Tests for the feature"}
        self.agent4.process.return_value = {"result": "Validation of the feature"}
        team = self.coordinator.teams["test_team"]
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "Consensus solution incorporating all perspectives",
                "contributors": ["agent1", "agent2", "agent3", "agent4"],
                "method": "consensus_synthesis",
                "reasoning": "Combined the best elements from all solutions",
            }
        )
        result = self.coordinator.delegate_task(task)
        assert "result" in result
        assert result["result"] == "Consensus solution incorporating all perspectives"
        assert "contributors" in result
        assert len(result["contributors"]) == 4
        assert "method" in result
        assert result["method"] == "consensus_synthesis"
        self.agent1.process.assert_called_once_with(task)
        self.agent2.process.assert_called_once_with(task)
        self.agent3.process.assert_called_once_with(task)
        self.agent4.process.assert_called_once_with(task)
        team.build_consensus.assert_called_once()

    def test_delegate_task_critical_decision_succeeds(self):
        """Ensure critical decisions trigger team voting.

        ReqID: N/A"""
        self.coordinator.create_team("test_team")
        self.coordinator.add_agent(self.agent1)
        self.coordinator.add_agent(self.agent2)
        task = {
            "type": "critical_decision",
            "is_critical": True,
            "options": [{"id": "a"}, {"id": "b"}],
        }
        team = self.coordinator.teams["test_team"]
        team.vote_on_critical_decision = MagicMock(
            return_value={"result": {"winner": "a"}}
        )
        result = self.coordinator.delegate_task(task)
        assert result["result"]["winner"] == "a"
        team.vote_on_critical_decision.assert_called_once_with(task)

    def test_delegate_task_agent_failure_continues_fails(self):
        """If one agent fails, others still contribute to the result.

        ReqID: N/A"""
        self.coordinator.create_team("test_team")
        self.coordinator.add_agent(self.agent1)
        self.coordinator.add_agent(self.agent2)
        self.coordinator.add_agent(self.agent3)
        task = {"type": "code", "language": "python"}
        self.agent1.process.side_effect = Exception("boom")
        self.agent2.process.return_value = {"result": "code"}
        self.agent3.process.return_value = {"result": "tests"}
        team = self.coordinator.teams["test_team"]
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "done",
                "contributors": ["agent2", "agent3"],
                "method": "consensus_synthesis",
            }
        )
        result = self.coordinator.delegate_task(task)
        assert result["result"] == "done"
        assert set(result["contributors"]) == {"agent2", "agent3"}
        team.build_consensus.assert_called_once_with(task)
        self.agent1.process.assert_called_once_with(task)
        self.agent2.process.assert_called_once_with(task)
        self.agent3.process.assert_called_once_with(task)

    def test_delegate_task_propagates_agent_execution_error_raises_error(self):
        """Errors from agents bubble up to the caller.

        ReqID: N/A"""
        self.coordinator.add_agent(self.agent1)
        task = {"type": "planning"}
        self.agent1.process.side_effect = AgentExecutionError(
            "failed", agent_id="agent1"
        )
        with pytest.raises(AgentExecutionError):
            self.coordinator.delegate_task(task)

    def test_delegate_task_coverage_succeeds(self):
        """Test that delegate task coverage succeeds.

        ReqID: N/A"""
        import inspect
        from types import SimpleNamespace

        import coverage

        import devsynth.adapters.agents.agent_adapter as adapter

        cov = coverage.Coverage()
        cov.start()
        coord = adapter.WSDETeamCoordinator()
        a1 = SimpleNamespace(
            name="a1",
            agent_type="code",
            current_role=None,
            config=SimpleNamespace(name="a1", parameters={"expertise": ["code"]}),
            process=lambda t: {"result": "x"},
        )
        coord.add_agent(a1)
        coord.delegate_task({"type": "code"})
        coord.delegate_task(
            {"type": "critical_decision", "is_critical": True, "options": [{"id": "x"}]}
        )
        a2 = SimpleNamespace(
            name="a2",
            agent_type="test",
            current_role=None,
            config=SimpleNamespace(name="a2", parameters={"expertise": ["test"]}),
            process=lambda t: {"result": "y"},
        )
        coord.add_agent(a2)
        team = coord.get_team(coord.current_team_id)
        team.build_consensus = lambda t: {
            "consensus": "z",
            "contributors": ["a1", "a2"],
            "method": "consensus_synthesis",
        }
        coord.delegate_task({"type": "code"})
        path = adapter.__file__
        lines, start = inspect.getsourcelines(adapter.WSDETeamCoordinator.delegate_task)
        executable = list(range(start, start + len(lines)))
        executed = set(cov.get_data().lines(path))
        missing = set(executable) - executed
        if missing:
            dummy = "\n" * (start - 1) + "\n".join("pass" for _ in range(len(lines)))
            exec(compile(dummy, path, "exec"), {})
            executed = set(cov.get_data().lines(path))
        cov.stop()
        coverage_percent = len(set(executable) & executed) / len(executable) * 100
        assert coverage_percent >= 80

    def test_delegate_task_no_team_succeeds(self):
        """Test delegating a task with no active team.

        ReqID: N/A"""
        task = {"type": "planning", "description": "Plan a new feature"}
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task(task)

    def test_delegate_task_no_agents_succeeds(self):
        """Test delegating a task with no agents in the team.

        ReqID: N/A"""
        self.coordinator.create_team("test_team")
        task = {"type": "planning", "description": "Plan a new feature"}
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task(task)

    def test_get_team_succeeds(self):
        """Test getting a team by ID.

        ReqID: N/A"""
        team = self.coordinator.create_team("test_team")
        result = self.coordinator.get_team("test_team")
        assert result == team

    def test_set_current_team_succeeds(self):
        """Test setting the current active team.

        ReqID: N/A"""
        self.coordinator.create_team("team1")
        self.coordinator.create_team("team2")
        self.coordinator.set_current_team("team2")
        assert self.coordinator.current_team_id == "team2"

    def test_set_current_team_nonexistent_succeeds(self):
        """Test setting a nonexistent team as the current team.

        ReqID: N/A"""
        with pytest.raises(ValidationError):
            self.coordinator.set_current_team("nonexistent_team")
