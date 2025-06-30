import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.application.collaboration.exceptions import TeamConfigurationError
from devsynth.domain.interfaces.agent import Agent
from devsynth.exceptions import ValidationError


class TestDelegateTask:
    def setup_method(self) -> None:
        self.coordinator = AgentCoordinatorImpl(
            {"features": {"wsde_collaboration": True}}
        )

        self.designer = MagicMock(spec=Agent)
        self.designer.name = "designer"
        self.designer.agent_type = "planner"
        self.designer.expertise = ["design"]
        self.designer.current_role = None
        self.designer.process.return_value = {"solution": "design"}

        self.worker = MagicMock(spec=Agent)
        self.worker.name = "worker"
        self.worker.agent_type = "code"
        self.worker.expertise = ["python"]
        self.worker.current_role = None
        self.worker.process.return_value = {"solution": "code"}

        self.tester = MagicMock(spec=Agent)
        self.tester.name = "tester"
        self.tester.agent_type = "test"
        self.tester.expertise = ["testing"]
        self.tester.current_role = None
        self.tester.process.return_value = {"solution": "tests"}

        for agent in (self.designer, self.worker, self.tester):
            self.coordinator.add_agent(agent)

    def test_team_task_returns_consensus(self) -> None:
        consensus = {
            "consensus": "final",
            "contributors": ["designer", "worker", "tester"],
            "method": "consensus_synthesis",
        }
        task = {"team_task": True, "type": "coding"}
        with patch.object(
            self.coordinator.team, "build_consensus", return_value=consensus
        ) as bc:
            with patch.object(
                self.coordinator.team,
                "select_primus_by_expertise",
                wraps=self.coordinator.team.select_primus_by_expertise,
            ) as sp:
                result = self.coordinator.delegate_task(task)
                sp.assert_called_once_with(task)
        bc.assert_called_once_with(task)
        assert result["result"] == consensus["consensus"]
        assert result["contributors"] == consensus["contributors"]
        assert result["method"] == consensus["method"]

    def test_team_task_no_agents(self) -> None:
        coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
        with pytest.raises(TeamConfigurationError):
            coordinator.delegate_task({"team_task": True})

    def test_invalid_task_format(self) -> None:
        with pytest.raises(ValidationError):
            self.coordinator.delegate_task({})
