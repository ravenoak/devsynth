from types import SimpleNamespace

import pytest

from devsynth.application.collaboration.message_protocol import MessageProtocol
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.domain.wsde.workflow import progress_roles
from devsynth.methodology.base import Phase


class DummyMemoryManager:
    def __init__(self):
        self.adapters = {"tinydb": object()}
        self.sync_manager = SimpleNamespace(_queue=[])
        self.flush_updates_called = False

    def queue_update(self, store, item):
        self.sync_manager._queue.append((store, item))

    def flush_updates(self):
        self.flush_updates_called = True
        self.sync_manager._queue.clear()


@pytest.mark.medium
def test_progress_roles_flushes_memory_queue():
    """Progressing roles triggers queued memory flush."""
    mm = DummyMemoryManager()
    team = WSDETeam(name="IntegrationTeam")
    team.add_agent(SimpleNamespace(name="a1"))
    team.add_agent(SimpleNamespace(name="a2"))
    team.message_protocol = MessageProtocol(memory_manager=mm)
    team.send_message("a1", ["a2"], "status_update", "hi", {})
    assert len(mm.sync_manager._queue) == 1
    progress_roles(team, Phase.DIFFERENTIATE, mm)
    assert mm.flush_updates_called
    assert mm.sync_manager._queue == []
