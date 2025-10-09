from unittest.mock import MagicMock

import pytest

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
    restore_memory_queue,
)
from devsynth.application.collaboration.dto import MemorySyncPort
from devsynth.application.collaboration.structures import MemoryQueueEntry
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.mark.medium
def test_flush_memory_queue_handles_missing_manager() -> None:
    """Gracefully handles a missing memory manager."""

    assert flush_memory_queue(None) == []


@pytest.mark.medium
def test_flush_memory_queue_without_sync_manager() -> None:
    """Returns empty list when sync manager is absent."""

    class Dummy:
        def __init__(self) -> None:
            self.flush_updates = MagicMock()

    mm = Dummy()
    result = flush_memory_queue(mm)
    assert result == []
    mm.flush_updates.assert_not_called()


@pytest.mark.medium
def test_restore_memory_queue_requeues_items_in_order() -> None:
    """Items are requeued without raising errors."""

    mm = MagicMock()
    sync_port = MemorySyncPort(
        adapter="tinydb",
        channel="primary",
        priority="high",
        options={"z": 1, "a": 2},
    )
    first = MemoryItem(
        id="1",
        content={},
        memory_type=MemoryType.TEAM_STATE,
        metadata={"sync_port": sync_port},
    )
    second = MemoryItem(
        id="2",
        content={},
        memory_type=MemoryType.TEAM_STATE,
        metadata={"sync_port": sync_port.to_dict()},
    )
    restore_memory_queue(
        mm,
        [
            MemoryQueueEntry(store="default", item=first),
            MemoryQueueEntry(store="secondary", item=second),
        ],
    )
    assert [call.args[0] for call in mm.queue_update.call_args_list] == [
        "default",
        "secondary",
    ]
    serialized_port = sync_port.to_dict()
    first_item = mm.queue_update.call_args_list[0].args[1]
    second_item = mm.queue_update.call_args_list[1].args[1]
    assert first_item.metadata["sync_port"] == serialized_port
    assert second_item.metadata["sync_port"] == serialized_port
