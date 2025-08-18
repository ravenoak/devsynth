from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
)
from devsynth.application.collaboration.WSDE import WSDE
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.methodology.base import Phase
from devsynth.methodology.wsde_edrr_coordinator import WSDEEDRRCoordinator


@pytest.mark.medium
def test_phase_progress_flushes_pending_memory_before_and_after() -> None:
    """Coordinator flushes memory queue to avoid hangs."""

    mm = MemoryManager(adapters={"default": MagicMock(flush=MagicMock())})
    team = WSDE(name="RoleTeam")
    agent = MagicMock()
    agent.id = "agent-1"
    agent.name = "Agent One"
    team.add_agent(agent)

    def assign_roles_for_phase(self, phase, _context=None):
        self.roles = {"explorer": agent}

    team.assign_roles_for_phase = assign_roles_for_phase.__get__(team, WSDE)
    coordinator = WSDEEDRRCoordinator(team, memory_manager=mm)

    mm.queue_update(
        "default",
        MemoryItem(id="m1", content={}, memory_type=MemoryType.TEAM_STATE),
    )
    assert mm.sync_manager._queue  # ensure queue populated

    with (
        patch(
            "devsynth.methodology.wsde_edrr_coordinator.flush_memory_queue",
            wraps=flush_memory_queue,
        ) as pre_flush,
        patch(
            "devsynth.domain.wsde.workflow.flush_memory_queue",
            wraps=flush_memory_queue,
        ) as post_flush,
    ):
        assignments = coordinator.progress_to_phase(Phase.EXPAND)

    assert assignments == {"agent-1": "Explorer"}
    assert pre_flush.call_count == 1
    assert post_flush.call_count == 1
    assert mm.sync_manager._queue == []
