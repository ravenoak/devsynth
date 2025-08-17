import asyncio
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
    restore_memory_queue,
)
from devsynth.application.collaboration.WSDE import WSDE
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.methodology.base import Phase


@pytest.mark.medium
def test_progress_roles_triggers_memory_flush():
    """Progressing roles should flush pending memory updates."""

    mm = MemoryManager(adapters={"default": MagicMock(flush=MagicMock())})
    team = WSDE(name="RoleTeam")
    agent = MagicMock()
    agent.id = "agent-1"
    agent.name = "Agent One"
    team.add_agent(agent)

    def assign_roles_for_phase(self, phase, _context=None):
        self.roles = {"explorer": agent}

    team.assign_roles_for_phase = assign_roles_for_phase.__get__(team, WSDE)

    with patch("devsynth.domain.wsde.workflow.flush_memory_queue") as flush_mock:
        flush_mock.return_value = []
        assignments = team.progress_roles(Phase.EXPAND, memory_manager=mm)

    assert assignments == {"agent-1": "Explorer"}
    flush_mock.assert_called_once_with(mm)


@pytest.mark.medium
def test_flush_memory_queue_waits_for_sync():
    """Flushing memory queue should await async sync if available."""

    adapter = MagicMock(flush=MagicMock())
    mm = MemoryManager(adapters={"default": adapter})
    mm.wait_for_sync = MagicMock(return_value=asyncio.sleep(0))

    item = MemoryItem(id="m1", content={}, memory_type=MemoryType.TEAM_STATE)
    mm.queue_update("default", item)
    flushed = flush_memory_queue(mm)

    assert flushed == [("default", item)]
    mm.wait_for_sync.assert_called_once()
    assert mm.sync_manager._queue == []


@pytest.mark.medium
def test_flush_memory_queue_notifies_hooks_on_failure():
    """Even if flushing fails, hooks receive a final None event."""

    adapter = MagicMock(flush=MagicMock())
    mm = MemoryManager(adapters={"default": adapter})
    mm.flush_updates = MagicMock(side_effect=RuntimeError("boom"))
    events: list[object | None] = []
    mm.register_sync_hook(lambda item: events.append(item))

    flushed = flush_memory_queue(mm)

    assert flushed == []
    assert events == [None]


@pytest.mark.medium
def test_restore_memory_queue_preserves_order():
    """Items are requeued in their original order."""

    adapter = MagicMock(flush=MagicMock())
    mm = MemoryManager(adapters={"default": adapter})
    item1 = MemoryItem(id="m1", content={}, memory_type=MemoryType.TEAM_STATE)
    item2 = MemoryItem(id="m2", content={}, memory_type=MemoryType.TEAM_STATE)

    restore_memory_queue(mm, [("default", item1), ("default", item2)])

    assert mm.sync_manager._queue == [("default", item1), ("default", item2)]
