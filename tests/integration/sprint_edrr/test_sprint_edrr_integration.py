"""Integration tests for sprint planning CLI and WSDE coordinator."""

import json

import pytest

from devsynth.agents.wsde_team_coordinator import WSDETeamCoordinatorAgent
from devsynth.application.cli.sprint_cmd import sprint_planning_cmd


class DummyTeam:
    """Simple team that records retrospectives."""

    def __init__(self) -> None:
        self.recorded = None

    def record_retrospective(self, summary):
        self.recorded = summary


@pytest.mark.slow
def test_sprint_planning_cmd_maps_requirements(tmp_path):
    """Sprint planning command maps requirement results to a plan."""
    data = {
        "recommended_scope": ["task1"],
        "objectives": ["obj1"],
        "success_criteria": ["crit1"],
    }
    path = tmp_path / "req.json"
    path.write_text(json.dumps(data))

    plan = sprint_planning_cmd(str(path))

    assert plan["planned_scope"] == ["task1"]
    assert plan["objectives"] == ["obj1"]
    assert plan["success_criteria"] == ["crit1"]


@pytest.mark.slow
def test_wsde_team_coordinator_aggregates_retrospective():
    """Coordinator aggregates notes and records summary."""
    team = DummyTeam()
    agent = WSDETeamCoordinatorAgent(team)
    notes = [
        {"positives": ["good"], "improvements": ["better"], "action_items": ["do"]},
        {"positives": ["great"], "improvements": [], "action_items": []},
    ]

    summary = agent.run_retrospective(notes, sprint=1)

    assert summary["positives"] == ["good", "great"]
    assert summary["improvements"] == ["better"]
    assert summary["action_items"] == ["do"]
    assert summary["sprint"] == 1
    assert team.recorded == summary
