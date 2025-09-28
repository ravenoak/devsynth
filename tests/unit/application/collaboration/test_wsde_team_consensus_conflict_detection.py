from types import SimpleNamespace

import pytest

from devsynth.application.collaboration.dto import ConflictRecord
from devsynth.application.collaboration.wsde_team_consensus import (
    ConsensusBuildingMixin,
)


class DummyTeam(ConsensusBuildingMixin):
    def __init__(self) -> None:
        self.agents = [SimpleNamespace(name="A"), SimpleNamespace(name="B")]

    def get_messages(self, agent: str, filters):  # type: ignore[override]
        opinion_map = {
            "A": {"opinion": "yes", "rationale": ""},
            "B": {"opinion": "no", "rationale": ""},
        }
        return [
            {
                "content": opinion_map[agent],
                "timestamp": 1,
            }
        ]


@pytest.mark.fast
def test_identify_conflicts_detects_opposing_opinions() -> None:
    """ReqID: N/A"""

    team = DummyTeam()
    conflicts = team._identify_conflicts({"id": "t1"})
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert isinstance(conflict, ConflictRecord)
    assert conflict.agent_a == "A"
    assert conflict.agent_b == "B"
