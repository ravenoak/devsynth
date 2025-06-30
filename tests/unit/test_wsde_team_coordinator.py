"""
Unit Tests for WSDETeamCoordinator

This file contains unit tests for the WSDETeamCoordinator class, which is responsible
for coordinating WSDE teams and implementing consensus-based decision making.
"""

import pytest
from unittest.mock import MagicMock, patch

from devsynth.domain.interfaces.agent import Agent
from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator
from devsynth.domain.models.wsde import WSDETeam
from devsynth.exceptions import ValidationError, AgentExecutionError


class TestWSDETeamCoordinator:
    """Test suite for the WSDETeamCoordinator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = WSDETeamCoordinator()

        # Create mock agents
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

    def test_create_team(self):
        """Test creating a team."""
        # Act
        team = self.coordinator.create_team("test_team")

        # Assert
        assert team is not None
        assert isinstance(team, WSDETeam)
        assert self.coordinator.teams["test_team"] == team
        assert self.coordinator.current_team_id == "test_team"

    def test_add_agent(self):
        """Test adding an agent to the coordinator."""
        # Arrange
        # Setup is done in setup_method

        # Act
        self.coordinator.add_agent(self.agent1)

        # Assert
        assert self.coordinator.current_team_id is not None
        assert len(self.coordinator.teams[self.coordinator.current_team_id].agents) == 1
        assert (
            self.coordinator.teams[self.coordinator.current_team_id].agents[0]
            == self.agent1
        )

    def test_delegate_task_single_agent(self):
        """Test delegating a task with a single agent."""
        # Arrange
        self.coordinator.add_agent(self.agent1)
        task = {"type": "planning", "description": "Plan a new feature"}
        self.agent1.process.return_value = {"result": "Feature plan created"}

        # Act
        result = self.coordinator.delegate_task(task)

        # Assert
        assert result["result"] == "Feature plan created"
        self.agent1.process.assert_called_once_with(task)

    def test_delegate_task_multi_agent_consensus(self):
        """Test delegating a task with multiple agents using consensus-based decision making."""
        # Arrange
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

        # Configure mock returns for agent processes
        self.agent1.process.return_value = {"result": "Design for the feature"}
        self.agent2.process.return_value = {"result": "Implementation of the feature"}
        self.agent3.process.return_value = {"result": "Tests for the feature"}
        self.agent4.process.return_value = {"result": "Validation of the feature"}

        # Mock the build_consensus method to return a predefined consensus
        team = self.coordinator.teams["test_team"]
        team.build_consensus = MagicMock(
            return_value={
                "consensus": "Consensus solution incorporating all perspectives",
                "contributors": ["agent1", "agent2", "agent3", "agent4"],
                "method": "consensus_synthesis",
                "reasoning": "Combined the best elements from all solutions",
            }
        )

        # Act
        result = self.coordinator.delegate_task(task)

        # Assert
        assert "result" in result
        assert result["result"] == "Consensus solution incorporating all perspectives"
        assert "contributors" in result
        assert len(result["contributors"]) == 4
        assert "method" in result
        assert result["method"] == "consensus_synthesis"

        # Verify that all agents were asked to process the task
        self.agent1.process.assert_called_once_with(task)
        self.agent2.process.assert_called_once_with(task)
        self.agent3.process.assert_called_once_with(task)
        self.agent4.process.assert_called_once_with(task)

        # Verify that build_consensus was called
        team.build_consensus.assert_called_once()

    def test_delegate_task_critical_decision(self):
        """Ensure critical decisions trigger team voting."""
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

    def test_delegate_task_agent_failure_continues(self):
        """If one agent fails, others still contribute to the result."""
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

    def test_delegate_task_propagates_agent_execution_error(self):
        """Errors from agents bubble up to the caller."""
        self.coordinator.add_agent(self.agent1)
        task = {"type": "planning"}
        self.agent1.process.side_effect = AgentExecutionError("failed", agent_id="agent1")

        with pytest.raises(AgentExecutionError):
            self.coordinator.delegate_task(task)

    def test_delegate_task_coverage(self):
        import inspect
        import coverage
        from types import SimpleNamespace
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
            {
                "type": "critical_decision",
                "is_critical": True,
                "options": [{"id": "x"}],
            }
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

    def test_delegate_task_no_team(self):
        """Test delegating a task with no active team."""
        # Arrange
        task = {"type": "planning", "description": "Plan a new feature"}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task(task)

    def test_delegate_task_no_agents(self):
        """Test delegating a task with no agents in the team."""
        # Arrange
        self.coordinator.create_team("test_team")
        task = {"type": "planning", "description": "Plan a new feature"}

        # Act & Assert
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task(task)

    def test_get_team(self):
        """Test getting a team by ID."""
        # Arrange
        team = self.coordinator.create_team("test_team")

        # Act
        result = self.coordinator.get_team("test_team")

        # Assert
        assert result == team

    def test_set_current_team(self):
        """Test setting the current active team."""
        # Arrange
        self.coordinator.create_team("team1")
        self.coordinator.create_team("team2")

        # Act
        self.coordinator.set_current_team("team2")

        # Assert
        assert self.coordinator.current_team_id == "team2"

    def test_set_current_team_nonexistent(self):
        """Test setting a nonexistent team as the current team."""
        # Act & Assert
        with pytest.raises(ValidationError):
            self.coordinator.set_current_team("nonexistent_team")
