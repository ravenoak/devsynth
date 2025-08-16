import pytest

from devsynth.application.collaboration.coordinator import AgentCoordinatorImpl
from devsynth.methodology.base import Phase


class DummyAgent:
    def __init__(self, name: str):
        self.name = name
        self.agent_type = "general"
        self.expertise = ["option_a"]

    def process(self, task):  # pragma: no cover - not used in voting
        return {}


@pytest.fixture
def coordinator():
    cfg = {"features": {"wsde_collaboration": True}}
    coord = AgentCoordinatorImpl(config=cfg)
    coord.add_agent(DummyAgent("a1"))
    coord.add_agent(DummyAgent("a2"))
    return coord


@pytest.mark.medium
@pytest.mark.parametrize(
    "phase",
    [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT],
)
def test_voting_summary_in_edrr_phases(coordinator, phase):
    task = {
        "type": "critical_decision",
        "is_critical": True,
        "options": ["option_a", "option_b"],
        "phase": phase.value,
        "team_task": True,
    }
    result = coordinator.delegate_task(task)
    assert result["phase"] == phase.value
    assert "Voting was completed" in result["summary"]
