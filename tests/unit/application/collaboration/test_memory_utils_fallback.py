import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from devsynth.application.collaboration.collaboration_memory_utils import (
    flush_memory_queue,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.mark.medium
def test_flush_memory_queue_falls_back_to_sync_manager() -> None:
    """Uses sync manager flush when memory manager lacks flush_updates."""

    item = MemoryItem(id="x", content={}, memory_type=MemoryType.TEAM_STATE)
    sync_manager = SimpleNamespace(
        _queue=[("default", item)],
        flush_queue=MagicMock(),
        wait_for_async=MagicMock(return_value=asyncio.sleep(0)),
    )
    mm = SimpleNamespace(sync_manager=sync_manager)

    flushed = flush_memory_queue(mm)

    sync_manager.flush_queue.assert_called_once()
    sync_manager.wait_for_async.assert_called_once()
    assert flushed == [("default", item)]
