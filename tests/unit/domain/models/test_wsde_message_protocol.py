from types import SimpleNamespace

import pytest

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
    restore_memory_queue,
)
from devsynth.application.collaboration.message_protocol import (
    MessageProtocol,
    MessageType,
)


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
def test_message_queue_flush_and_restore_has_expected():
    """Messages queue memory updates and can be restored."""
    mm = DummyMemoryManager()
    proto = MessageProtocol(memory_manager=mm)
    proto.send_message(
        sender="alice",
        recipients=["bob"],
        message_type=MessageType.STATUS_UPDATE,
        subject="s",
        content="c",
        metadata={},
    )
    assert len(mm.sync_manager._queue) == 1
    flushed = flush_memory_queue(mm)
    assert len(flushed) == 1
    assert mm.flush_updates_called
    assert mm.sync_manager._queue == []
    restore_memory_queue(mm, flushed)
    assert len(mm.sync_manager._queue) == 1
    assert mm.sync_manager._queue[0][1].id == flushed[0][1].id
