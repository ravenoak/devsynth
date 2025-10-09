from __future__ import annotations

from datetime import datetime
from typing import cast

import pytest

from devsynth.application.memory.dto import MemoryRecord
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.sync_manager import SyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryType


class RecordingStore:
    """Store that records stored payloads for verification."""

    def __init__(self) -> None:
        self.items: dict[str, MemoryItem] = {}
        self.stored_payloads: list[MemoryItem] = []

    def store(self, item: MemoryItem) -> str:
        self.stored_payloads.append(item)
        self.items[item.id] = item
        return item.id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        return self.items.get(item_id)

    def get_all_items(self) -> list[MemoryItem]:
        return list(self.items.values())

    def delete(self, item_id: str) -> None:
        self.items.pop(item_id, None)

    def flush(self) -> None:
        # SyncManager expects adapters to expose flush hooks during commits.
        return None


def _manager() -> MemoryManager:
    adapters = {"alpha": RecordingStore(), "beta": RecordingStore()}
    manager = MemoryManager(adapters=adapters)
    return manager


@pytest.mark.fast
def test_queue_update_enqueues_memory_record() -> None:
    manager = _manager()
    sync_manager: SyncManager = manager.sync_manager
    item = MemoryItem(
        id="queued-1",
        content="queue-test",
        memory_type=MemoryType.SHORT_TERM,
        metadata={"origin": "alpha"},
        created_at=datetime.now(),
    )

    sync_manager.queue_update("alpha", item)

    with sync_manager._queue_lock:  # noqa: SLF001 - internal verification for test
        queued_store, record = sync_manager._queue[-1]

    assert queued_store == "alpha"
    assert isinstance(record, MemoryRecord)
    assert record.item.metadata["origin"] == "alpha"

    sync_manager.flush_queue()
    beta_store = manager.adapters["beta"]
    assert beta_store.retrieve("queued-1") is not None


@pytest.mark.fast
def test_transaction_rollback_uses_normalized_snapshots() -> None:
    manager = _manager()
    sync_manager: SyncManager = manager.sync_manager
    alpha_store = cast(RecordingStore, manager.adapters["alpha"])

    original = MemoryItem(
        id="alpha-1",
        content="baseline",
        memory_type=MemoryType.SHORT_TERM,
        metadata={"revision": 1},
        created_at=datetime.now(),
    )
    alpha_store.store(original)

    with pytest.raises(RuntimeError):
        with sync_manager.transaction(["alpha"]):
            mutated = MemoryItem(
                id="alpha-1",
                content="mutated",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"revision": 2},
                created_at=datetime.now(),
            )
            alpha_store.store(mutated)
            raise RuntimeError("fail transaction")

    restored = alpha_store.retrieve("alpha-1")
    assert restored is not None
    assert restored.content == "baseline"
    assert restored.metadata == {"revision": 1}
    assert alpha_store.stored_payloads[-1].metadata == {"revision": 1}
    assert manager.sync_manager.get_cache_size() == 0
