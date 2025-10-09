import pytest

from devsynth.application.collaboration.structures import SubtaskSpec
from devsynth.application.collaboration.wsde_team_task_management import (
    TaskManagementMixin,
)


class DummyTeam(TaskManagementMixin):
    def __init__(self) -> None:
        class Agent:
            def __init__(self, name: str, expertise: list[str]) -> None:
                self.name = name
                self.expertise = expertise
                self.metadata = {"expertise": expertise}

        class Logger:
            def info(self, *args, **kwargs) -> None:  # pragma: no cover - stub
                pass

            def debug(self, *args, **kwargs) -> None:  # pragma: no cover - stub
                pass

        self.agents = [Agent("A", ["python"]), Agent("B", ["rust"])]
        self.logger = Logger()
        self.send_message = lambda **kwargs: None
        self.subtasks: dict[str, list[SubtaskSpec]] = {}
        self.subtask_progress: dict[str, float] = {}
        self.contribution_metrics: dict[str, dict[str, dict[str, float]]] = {}

    def get_messages(self, *_, **__) -> list[dict[str, object]]:  # pragma: no cover
        return []

    def _calculate_expertise_score(self, agent, subtask):  # type: ignore[override]
        return 3 if subtask.get("primary_expertise") in agent.expertise else 0


@pytest.mark.fast
def test_delegate_subtasks_assigns_best_agent() -> None:
    """ReqID: N/A"""

    team = DummyTeam()
    subtask = SubtaskSpec(
        id="s1",
        title="do thing",
        description="python task",
        parent_task_id="t1",
        metadata={"primary_expertise": "python"},
    )
    assignments = team.delegate_subtasks([subtask])
    assert assignments[0].assigned_to == "A"
    assert subtask.assigned_to == "A"
    assert subtask.status == "assigned"
