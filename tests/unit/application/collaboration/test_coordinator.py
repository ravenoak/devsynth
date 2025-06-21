import pytest
from unittest.mock import MagicMock, patch

from devsynth.domain.interfaces.agent import Agent
from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.exceptions import ValidationError


class TestAgentCoordinatorPrimusSelection:
    def setup_method(self):
        self.coordinator = AgentCoordinatorImpl(
            {"features": {"wsde_collaboration": True}}
        )

        self.python_agent = MagicMock(spec=Agent)
        self.python_agent.name = "python"
        self.python_agent.agent_type = "code"
        self.python_agent.expertise = ["python", "backend"]
        self.python_agent.current_role = None
        self.python_agent.process.return_value = {"solution": "python-solution"}

        self.js_agent = MagicMock(spec=Agent)
        self.js_agent.name = "javascript"
        self.js_agent.agent_type = "code"
        self.js_agent.expertise = ["javascript"]
        self.js_agent.current_role = None
        self.js_agent.process.return_value = {"solution": "js-solution"}

        self.doc_agent = MagicMock(spec=Agent)
        self.doc_agent.name = "docs"
        self.doc_agent.agent_type = "documentation"
        self.doc_agent.expertise = ["documentation"]
        self.doc_agent.current_role = None
        self.doc_agent.process.return_value = {"solution": "doc-solution"}

        for agent in [self.python_agent, self.js_agent, self.doc_agent]:
            self.coordinator.add_agent(agent)

    def test_primus_selection_and_consensus_fields(self):
        consensus = {
            "consensus": "final",
            "contributors": ["python", "javascript", "docs"],
            "method": "consensus_synthesis",
        }
        with patch.object(
            self.coordinator.team, "build_consensus", return_value=consensus
        ):
            with patch.object(
                self.coordinator.team,
                "select_primus_by_expertise",
                wraps=self.coordinator.team.select_primus_by_expertise,
            ) as spy:
                task = {"team_task": True, "language": "python", "type": "coding"}
                result = self.coordinator.delegate_task(task)
                spy.assert_called_once_with(task)

        assert self.coordinator.team.get_primus() == self.python_agent
        assert result["contributors"] == consensus["contributors"]
        assert result["method"] == consensus["method"]


class TestAgentCoordinatorErrorPaths:
    def test_missing_agent_type(self):
        coordinator = AgentCoordinatorImpl({"features": {"wsde_collaboration": True}})
        agent = MagicMock(spec=Agent)
        agent.name = "planner"
        agent.agent_type = "planner"
        agent.current_role = None
        coordinator.add_agent(agent)

        with pytest.raises(ValidationError):
            coordinator.delegate_task({"agent_type": "nonexistent"})
