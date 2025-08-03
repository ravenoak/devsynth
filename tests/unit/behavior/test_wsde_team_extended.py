import pytest
from devsynth.application.collaboration.wsde_team_extended import CollaborativeWSDETeam
from devsynth.domain.models.memory import MemoryType


class DummyMemoryManager:
    def __init__(self):
        self.calls = []

    def store_with_edrr_phase(self, content, memory_type, edrr_phase, metadata=None):
        self.calls.append((content, memory_type, edrr_phase, metadata))
        return "mem-ref"


@pytest.mark.medium
def test_summarize_and_store_consensus():
    team = CollaborativeWSDETeam()
    team.memory_manager = DummyMemoryManager()
    task = {"id": "t1"}
    consensus = {"method": "synthesis", "synthesis": {"text": "do x"}}

    result = team._summarize_and_store_consensus(task, consensus)

    assert "summary" in result
    assert "synthesis consensus" in result["summary"].lower()
    assert result["memory_reference"] == "mem-ref"
    assert team.memory_manager.calls[0][1] == MemoryType.TEAM_STATE
