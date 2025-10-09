from datetime import datetime

import pytest

from devsynth.application.memory.dto import MemoryRecord
from devsynth.application.memory.transaction_context import TransactionContext
from devsynth.domain.models.memory import MemoryItem, MemoryType


class DummyStore:
    """Simple in-memory store with flush capability."""

    def __init__(self):
        self.items = {}
        self.flushed = 0

    def store(self, item: MemoryItem) -> str:
        self.items[item.id] = item
        return item.id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        return self.items.get(item_id)

    def get_all(self):
        return list(self.items.values())

    def delete(self, item_id: str) -> None:
        self.items.pop(item_id, None)

    def flush(self) -> None:
        self.flushed += 1

    def prepare_commit(self, transaction_id: str) -> bool:
        return True

    def commit_transaction(self, transaction_id: str) -> bool:
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        return True


class SnapshotOnlyStore:
    """Store without native transactions to test snapshot restoration."""

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


class TestMixedBackendTransactions:
    """Tests cross-store transactions across different backends."""

    @pytest.mark.medium
    def test_transaction_across_backends(self):
        store_a = DummyStore()
        store_b = DummyStore()
        item1 = MemoryItem(
            id="1",
            content="Store A",
            memory_type=MemoryType.SHORT_TERM,
            metadata={},
            created_at=datetime.now(),
        )
        item2 = MemoryItem(
            id="2",
            content="Store B",
            memory_type=MemoryType.SHORT_TERM,
            metadata={},
            created_at=datetime.now(),
        )
        with TransactionContext([store_a, store_b]):
            store_a.store(item1)
            store_b.store(item2)

        assert store_a.retrieve("1").content == "Store A"
        assert store_b.retrieve("2").content == "Store B"
        assert store_a.flushed > 0
        assert store_b.flushed > 0

    @pytest.mark.medium
    def test_snapshot_rollback_restores_memory_records(self):
        store = SnapshotOnlyStore()
        original = MemoryItem(
            id="snap-1",
            content="baseline",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"version": "initial"},
            created_at=datetime.now(),
        )
        store.store(original)
        context = TransactionContext([store])
        with pytest.raises(RuntimeError):
            with context:
                updated = MemoryItem(
                    id="snap-1",
                    content="mutated",
                    memory_type=MemoryType.SHORT_TERM,
                    metadata={"version": "updated"},
                    created_at=datetime.now(),
                )
                store.store(updated)
                raise RuntimeError("force rollback")

        restored = store.retrieve("snap-1")
        assert restored is not None
        assert restored.content == "baseline"
        assert restored.metadata["version"] == "initial"
        assert store.stored_payloads[-1].metadata["version"] == "initial"

        rollback_entries = [
            entry for entry in context.operations if entry["phase"] == "rollback"
        ]
        assert rollback_entries
        for entry in rollback_entries:
            assert all(isinstance(record, MemoryRecord) for record in entry["records"])
            assert all(record.source == entry["store"] for record in entry["records"])
