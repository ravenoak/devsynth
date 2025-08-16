"""Verify WSDE messaging integrates with EDRR-tagged memory storage."""

import pytest

from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.mark.medium
def test_message_persisted_with_edrr_phase(tmp_path):
    """Messages should be stored with their EDRR phase metadata."""
    mem_file = tmp_path / "mem.json"
    adapter = TinyDBMemoryAdapter(str(mem_file))
    memory = MemoryManager(adapters={"tinydb": adapter})
    team = WSDETeam(name="EDRRTeam")
    team.memory_manager = memory

    team.send_message(
        sender="alice",
        recipients=["bob"],
        message_type="status_update",
        subject="s",
        content="c",
        metadata={"edrr_phase": Phase.EXPAND.value},
    )

    results = memory.query_by_edrr_phase(Phase.EXPAND.value)
    assert any(r.metadata.get("edrr_phase") == Phase.EXPAND.value for r in results)
