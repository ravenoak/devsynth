from unittest.mock import MagicMock, patch

import pytest

from devsynth.adapters.agents.agent_adapter import AgentAdapter
from devsynth.application.agents.unified_agent import UnifiedAgent


class TestMultiAgentAdapterWorkflow:
    """Tests for the MultiAgentAdapterWorkflow component.

    ReqID: N/A"""

    def setup_method(self):
        self.adapter = AgentAdapter()
        self.adapter.multi_agent_enabled = True
        self.team = self.adapter.create_team("team1")
        self.adapter.set_current_team("team1")
        self.agent1 = MagicMock(spec=UnifiedAgent)
        self.agent1.name = "PythonAgent"
        self.agent1.config = MagicMock()
        self.agent1.config.name = "PythonAgent"
        self.agent1.config.parameters = {"expertise": ["python", "backend"]}
        self.agent1.process.return_value = {"result": "py"}
        self.agent2 = MagicMock(spec=UnifiedAgent)
        self.agent2.name = "JSAgent"
        self.agent2.config = MagicMock()
        self.agent2.config.name = "JSAgent"
        self.agent2.config.parameters = {"expertise": ["javascript", "frontend"]}
        self.agent2.process.return_value = {"result": "js"}
        self.agent3 = MagicMock(spec=UnifiedAgent)
        self.agent3.name = "DocAgent"
        self.agent3.config = MagicMock()
        self.agent3.config.name = "DocAgent"
        self.agent3.config.parameters = {"expertise": ["documentation"]}
        self.agent3.process.return_value = {"result": "doc"}
        self.adapter.add_agents_to_team([self.agent1, self.agent2, self.agent3])

    def test_multi_agent_consensus_and_primus_selection_succeeds(self):
        """Test that multi agent consensus and primus selection succeeds.

        ReqID: N/A"""
        task = {"type": "coding", "language": "python"}
        with (
            patch.object(
                self.team,
                "build_consensus",
                return_value={
                    "consensus": "done",
                    "contributors": ["PythonAgent", "JSAgent", "DocAgent"],
                    "method": "consensus_synthesis",
                    "reasoning": "",
                },
            ) as mock_consensus,
            patch.object(
                self.team,
                "select_primus_by_expertise",
                wraps=self.team.select_primus_by_expertise,
            ) as mock_select,
        ):
            result = self.adapter.process_task(task)
            mock_consensus.assert_called_once_with(task)
            mock_select.assert_called_once_with(task)
        assert self.team.get_primus() == self.agent1
        assert result["method"] == "consensus_synthesis"
        assert set(result["contributors"]) == {"PythonAgent", "JSAgent", "DocAgent"}

    def test_bulk_add_agents_succeeds(self):
        """Test that bulk add agents succeeds.

        ReqID: N/A"""
        adapter = AgentAdapter()
        adapter.create_team("bulk")
        adapter.set_current_team("bulk")
        adapter.add_agents_to_team([self.agent1, self.agent2])
        team = adapter.get_team("bulk")
        assert len(team.agents) == 2
