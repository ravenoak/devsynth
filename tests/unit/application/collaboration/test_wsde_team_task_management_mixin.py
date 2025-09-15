from types import SimpleNamespace

import pytest

from devsynth.application.collaboration.wsde_team_task_management import (
    TaskManagementMixin,
)


class DummyTeam(TaskManagementMixin):
    def __init__(self) -> None:
        self.agents = [
            SimpleNamespace(name="A", expertise=["python"]),
            SimpleNamespace(name="B", expertise=["rust"]),
        ]
        self.logger = SimpleNamespace(
            info=lambda *a, **k: None, debug=lambda *a, **k: None
        )
        self.send_message = lambda **kwargs: None

    def _calculate_expertise_score(self, agent, subtask):  # type: ignore[override]
        return 3 if subtask.get("primary_expertise") in agent.expertise else 0


@pytest.mark.fast
def test_delegate_subtasks_assigns_best_agent() -> None:
    """ReqID: N/A"""

    team = DummyTeam()
    subtask = {
        "id": "s1",
        "title": "do thing",
        "primary_expertise": "python",
        "status": "pending",
    }
    assignments = team.delegate_subtasks([subtask])
    assert assignments[0]["assigned_to"] == "A"
    assert subtask["assigned_to"] == "A"
    assert subtask["status"] == "assigned"
