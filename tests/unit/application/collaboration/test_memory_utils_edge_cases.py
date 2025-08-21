from unittest.mock import MagicMock

import pytest

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
    restore_memory_queue,
)
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
    item = MemoryItem(id="1", content={}, memory_type=MemoryType.TEAM_STATE)
    restore_memory_queue(mm, [("default", item)])
    mm.queue_update.assert_called_once_with("default", item)
