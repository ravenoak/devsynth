"""Unit tests for the fallback mechanisms for memory store failures."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from typing import Any

import pytest

from devsynth.application.memory.dto import MemoryRecord
from devsynth.application.memory.fallback import (
    FallbackError,
    FallbackStore,
    PendingOperation,
    StoreStatus,
    with_fallback,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType


class TypedMemoryStore:
    """Simple in-memory store implementing the MemoryStore protocol."""

    def __init__(self, name: str, *, items: list[MemoryItem] | None = None) -> None:
        self.name = name
        self.items: dict[str, MemoryItem] = {
            item.id: deepcopy(item) for item in items or []
        }
        self.calls: dict[str, int] = {
            "store": 0,
            "retrieve": 0,
            "search": 0,
            "delete": 0,
            "get_all_items": 0,
            "begin_transaction": 0,
            "commit_transaction": 0,
            "rollback_transaction": 0,
            "is_transaction_active": 0,
        }
        self._failures: dict[str, list[Exception | None]] = {}
        self._tx_counter = 0
        self._active_transactions: set[str] = set()

    def set_failure(self, method: str, exc: Exception) -> None:
        self._failures[method] = [exc]

    def set_failure_sequence(
        self, method: str, sequence: list[Exception | None]
    ) -> None:
        self._failures[method] = list(sequence)

    def clear_failures(self) -> None:
        self._failures.clear()

    def _consume_failure(self, method: str) -> None:
        queue = self._failures.get(method)
        if not queue:
            return
        exc = queue.pop(0)
        if not queue:
            self._failures.pop(method, None)
        if exc is not None:
            raise exc

    def store(self, item: MemoryItem) -> str:
        self.calls["store"] += 1
        self._consume_failure("store")
        stored = deepcopy(item)
        if not stored.id:
            stored.id = f"{self.name}-{len(self.items) + 1}"
        self.items[stored.id] = stored
        return stored.id

    def retrieve(self, item_id: str) -> MemoryItem:
        self.calls["retrieve"] += 1
        self._consume_failure("retrieve")
        if item_id not in self.items:
            raise KeyError(f"Item {item_id} not found")
        return deepcopy(self.items[item_id])

    def search(self, query: dict[str, Any]) -> list[MemoryItem]:
        self.calls["search"] += 1
        self._consume_failure("search")
        return [deepcopy(item) for item in self.items.values()]

    def delete(self, item_id: str) -> bool:
        self.calls["delete"] += 1
        self._consume_failure("delete")
        return self.items.pop(item_id, None) is not None

    def get_all_items(self) -> list[MemoryItem]:
        self.calls["get_all_items"] += 1
        self._consume_failure("get_all_items")
        return [deepcopy(item) for item in self.items.values()]

    def begin_transaction(self) -> str:
        self.calls["begin_transaction"] += 1
        self._consume_failure("begin_transaction")
        self._tx_counter += 1
        tx = f"{self.name}-tx-{self._tx_counter}"
        self._active_transactions.add(tx)
        return tx

    def commit_transaction(self, transaction_id: str) -> bool:
        self.calls["commit_transaction"] += 1
        self._consume_failure("commit_transaction")
        self._active_transactions.discard(transaction_id)
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        self.calls["rollback_transaction"] += 1
        self._consume_failure("rollback_transaction")
        self._active_transactions.discard(transaction_id)
        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        self.calls["is_transaction_active"] += 1
        self._consume_failure("is_transaction_active")
        return transaction_id in self._active_transactions


@pytest.fixture
def memory_item():
    """Create a memory item for testing."""
    return MemoryItem(
        id="test-item-1",
        content="This is a test item",
        memory_type=MemoryType.WORKING,
        metadata={"test": "value"},
        created_at=datetime.now(),
    )


@pytest.fixture
def primary_store():
    """Create a typed primary store."""

    base_item = MemoryItem(
        id="test-item-1",
        content="This is a test item",
        memory_type=MemoryType.WORKING,
        metadata={"test": "value"},
        created_at=datetime.now(),
    )
    return TypedMemoryStore("primary", items=[base_item])


@pytest.fixture
def fallback_store():
    """Create a typed fallback store."""

    fallback_item = MemoryItem(
        id="test-item-1",
        content="This is a test item from fallback",
        memory_type=MemoryType.WORKING,
        metadata={"test": "value", "source": "fallback"},
        created_at=datetime.now(),
    )
    return TypedMemoryStore("fallback", items=[fallback_item])


class TestFallbackStore:
    """Tests for the FallbackStore class."""

    @pytest.mark.medium
    def test_initialization(self, primary_store, fallback_store):
        """Test that FallbackStore initializes with expected values."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        assert store.primary_store is primary_store
        assert store.fallback_stores == [fallback_store]
        assert store.store_states[primary_store].status is StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status is StoreStatus.AVAILABLE
        assert store.last_errors == {}
        assert store.pending_operations == []

        status = store.get_store_status()
        assert status.primary is StoreStatus.AVAILABLE
        assert status.fallbacks == [StoreStatus.AVAILABLE]
        assert status.last_errors == {"primary": None, "fallback": None}

    @pytest.mark.medium
    def test_store_primary_success(self, primary_store, fallback_store, memory_item):
        """Test storing an item when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item_id = store.store(memory_item)
        assert item_id == "test-item-1"
        assert primary_store.calls["store"] == 1
        assert fallback_store.calls["store"] == 1
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_store_primary_failure(self, primary_store, fallback_store, memory_item):
        """Test storing an item when the primary store fails."""
        primary_store.set_failure("store", ValueError("Primary store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item_id = store.store(memory_item)
        assert item_id == "test-item-1"
        assert primary_store.calls["store"] == 1
        assert fallback_store.calls["store"] == 1
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert isinstance(store.last_errors[primary_store], ValueError)
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "store"
        assert store.pending_operations[0].item == memory_item

    @pytest.mark.medium
    def test_store_all_failures(self, primary_store, fallback_store, memory_item):
        """Test storing an item when all stores fail."""
        primary_store.set_failure("store", ValueError("Primary store failed"))
        fallback_store.set_failure("store", ValueError("Fallback store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.store(memory_item)
        assert "All stores failed to store item" in str(excinfo.value)
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_retrieve_primary_success(self, primary_store, fallback_store):
        """Test retrieving an item when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item = store.retrieve("test-item-1")
        assert isinstance(item, MemoryRecord)
        assert item.id == "test-item-1"
        assert item.content == "This is a test item"
        assert item.source == "primary"
        assert isinstance(item.metadata, dict)
        assert primary_store.calls["retrieve"] == 1
        assert fallback_store.calls["retrieve"] == 0
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_retrieve_primary_failure(self, primary_store, fallback_store):
        """Test retrieving an item when the primary store fails."""
        primary_store.set_failure("retrieve", ValueError("Primary store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item = store.retrieve("test-item-1")
        assert isinstance(item, MemoryRecord)
        assert item.id == "test-item-1"
        assert item.content == "This is a test item from fallback"
        assert item.source == "fallback"
        assert isinstance(item.metadata, dict)
        assert primary_store.calls["retrieve"] == 1
        assert fallback_store.calls["retrieve"] == 1
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_retrieve_primary_not_found(self, primary_store, fallback_store):
        """Test retrieving an item when the primary store doesn't find it."""
        primary_store.set_failure("retrieve", KeyError("Item not found"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item = store.retrieve("test-item-1")
        assert isinstance(item, MemoryRecord)
        assert item.id == "test-item-1"
        assert item.content == "This is a test item from fallback"
        assert item.source == "fallback"
        assert isinstance(item.metadata, dict)
        assert primary_store.calls["retrieve"] == 1
        assert fallback_store.calls["retrieve"] == 1
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_retrieve_all_failures(self, primary_store, fallback_store):
        """Test retrieving an item when all stores fail."""
        primary_store.set_failure("retrieve", ValueError("Primary store failed"))
        fallback_store.set_failure("retrieve", ValueError("Fallback store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(KeyError) as excinfo:
            store.retrieve("test-item-1")
        assert "Item test-item-1 not found in any store" in str(excinfo.value)
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_search_primary_success(self, primary_store, fallback_store):
        """Test searching for items when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        results = store.search({"query": "test"})
        assert results["store"] == "primary"
        assert len(results["records"]) == 1
        record = results["records"][0]
        assert isinstance(record, MemoryRecord)
        assert record.id == "test-item-1"
        assert record.content == "This is a test item"
        assert record.source == "primary"
        assert primary_store.calls["search"] == 1
        assert fallback_store.calls["search"] == 0
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_search_primary_failure(self, primary_store, fallback_store):
        """Test searching for items when the primary store fails."""
        primary_store.set_failure("search", ValueError("Primary store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        results = store.search({"query": "test"})
        assert results["store"] == "fallback"
        assert len(results["records"]) == 1
        record = results["records"][0]
        assert isinstance(record, MemoryRecord)
        assert record.id == "test-item-1"
        assert record.content == "This is a test item from fallback"
        assert record.source == "fallback"
        assert primary_store.calls["search"] == 1
        assert fallback_store.calls["search"] == 1
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_search_all_failures(self, primary_store, fallback_store):
        """Test searching for items when all stores fail."""
        primary_store.set_failure("search", ValueError("Primary store failed"))
        fallback_store.set_failure("search", ValueError("Fallback store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.search({"query": "test"})
        assert "All stores failed to search" in str(excinfo.value)
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_delete_primary_success(self, primary_store, fallback_store):
        """Test deleting an item when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.delete("test-item-1")
        assert result is True
        assert primary_store.calls["delete"] == 1
        assert fallback_store.calls["delete"] == 1
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_delete_primary_failure(self, primary_store, fallback_store):
        """Test deleting an item when the primary store fails."""
        primary_store.set_failure("delete", ValueError("Primary store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.delete("test-item-1")
        assert result is True
        assert primary_store.calls["delete"] == 1
        assert fallback_store.calls["delete"] == 1
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "delete"
        assert store.pending_operations[0].item_id == "test-item-1"

    @pytest.mark.medium
    def test_delete_all_failures(self, primary_store, fallback_store):
        """Test deleting an item when all stores fail."""
        primary_store.set_failure("delete", ValueError("Primary store failed"))
        fallback_store.set_failure("delete", ValueError("Fallback store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.delete("test-item-1")
        assert result is False
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_get_all_items_primary_success(self, primary_store, fallback_store):
        """Test getting all items when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        items = store.get_all_items()
        assert len(items) == 1
        assert items[0].id == "test-item-1"
        assert items[0].content == "This is a test item"
        assert primary_store.calls["get_all_items"] == 1
        assert fallback_store.calls["get_all_items"] == 0
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_get_all_items_primary_failure(self, primary_store, fallback_store):
        """Test getting all items when the primary store fails."""
        primary_store.set_failure("get_all_items", ValueError("Primary store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        items = store.get_all_items()
        assert len(items) == 1
        assert items[0].id == "test-item-1"
        assert items[0].content == "This is a test item from fallback"
        assert primary_store.calls["get_all_items"] == 1
        assert fallback_store.calls["get_all_items"] == 1
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_get_all_items_all_failures(self, primary_store, fallback_store):
        """Test getting all items when all stores fail."""
        primary_store.set_failure("get_all_items", ValueError("Primary store failed"))
        fallback_store.set_failure("get_all_items", ValueError("Fallback store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.get_all_items()
        assert "All stores failed to get all items" in str(excinfo.value)
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_begin_transaction_primary_success(self, primary_store, fallback_store):
        """Test beginning a transaction when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        transaction_id = store.begin_transaction()
        assert transaction_id == "primary-tx-1"
        assert primary_store.calls["begin_transaction"] == 1
        assert fallback_store.calls["begin_transaction"] == 1
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_begin_transaction_primary_failure(self, primary_store, fallback_store):
        """Test beginning a transaction when the primary store fails."""
        primary_store.set_failure(
            "begin_transaction", ValueError("Primary store failed")
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        transaction_id = store.begin_transaction()
        assert transaction_id == "fallback-tx-1"
        assert primary_store.calls["begin_transaction"] == 1
        assert fallback_store.calls["begin_transaction"] == 1
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "begin_transaction"
        assert store.pending_operations[0].transaction_id == "fallback-tx-1"

    @pytest.mark.medium
    def test_begin_transaction_all_failures(self, primary_store, fallback_store):
        """Test beginning a transaction when all stores fail."""
        primary_store.set_failure(
            "begin_transaction", ValueError("Primary store failed")
        )
        fallback_store.set_failure(
            "begin_transaction", ValueError("Fallback store failed")
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.begin_transaction()
        assert "All stores failed to begin transaction" in str(excinfo.value)
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_commit_transaction_primary_success(self, primary_store, fallback_store):
        """Test committing a transaction when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.commit_transaction("tx-1")
        assert result is True
        assert primary_store.calls["commit_transaction"] == 1
        assert fallback_store.calls["commit_transaction"] == 1
        assert store.store_states[primary_store].status == StoreStatus.AVAILABLE
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_commit_transaction_primary_failure(self, primary_store, fallback_store):
        """Test committing a transaction when the primary store fails."""
        primary_store.set_failure(
            "commit_transaction", ValueError("Primary store failed")
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.commit_transaction("tx-1")
        assert result is True
        assert primary_store.calls["commit_transaction"] == 1
        assert fallback_store.calls["commit_transaction"] == 1
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "commit_transaction"
        assert store.pending_operations[0].transaction_id == "tx-1"

    @pytest.mark.medium
    def test_commit_transaction_all_failures(self, primary_store, fallback_store):
        """Test committing a transaction when all stores fail."""
        primary_store.set_failure(
            "commit_transaction", ValueError("Primary store failed")
        )
        fallback_store.set_failure(
            "commit_transaction", ValueError("Fallback store failed")
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.commit_transaction("tx-1")
        assert result is False
        assert store.store_states[primary_store].status == StoreStatus.DEGRADED
        assert store.store_states[fallback_store].status == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_reconcile_pending_operations(
        self, primary_store, fallback_store, memory_item
    ):
        """Test reconciling pending operations when the primary store becomes available."""
        primary_store.set_failure_sequence(
            "store", [ValueError("Primary store failed"), None]
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        store.store(memory_item)
        assert len(store.pending_operations) == 1
        store._reconcile_pending_operations()
        assert primary_store.calls["store"] >= 2
        assert len(store.pending_operations) == 0

    @pytest.mark.medium
    def test_get_store_status(self, primary_store, fallback_store, memory_item):
        """Test getting the status of all stores."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        status = store.get_store_status()
        assert status.primary is StoreStatus.AVAILABLE
        assert status.fallbacks == [StoreStatus.AVAILABLE]
        assert status.last_errors == {"primary": None, "fallback": None}

        primary_store.set_failure("store", ValueError("Primary store failed"))
        store.store(memory_item)
        status = store.get_store_status()
        assert status.primary is StoreStatus.DEGRADED
        assert status.fallbacks == [StoreStatus.AVAILABLE]
        assert status.last_errors == {
            "primary": "Primary store failed",
            "fallback": None,
        }

    @pytest.mark.medium
    def test_get_pending_operations_count(
        self, primary_store, fallback_store, memory_item
    ):
        """Test getting the number of pending operations."""
        primary_store.set_failure("store", ValueError("Primary store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        store.store(memory_item)
        count = store.get_pending_operations_count()
        assert count == 1

    @pytest.mark.medium
    def test_pending_operation_serialization_round_trip(
        self, primary_store, fallback_store, memory_item
    ):
        """Pending operations serialize and hydrate with typed metadata payloads."""

        primary_store.set_failure("store", ValueError("Primary store failed"))
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        store.store(memory_item)

        pending = store.pending_operations[0]
        serialized_payload = asdict(pending)
        if pending.item is not None:
            serialized_payload["item"] = pending.item.to_dict()

        serialized = json.dumps(serialized_payload)
        decoded: dict[str, Any] = json.loads(serialized)

        item_payload = decoded.get("item")
        restored_item = (
            MemoryItem.from_dict(item_payload) if item_payload is not None else None
        )

        restored_operation = PendingOperation(
            operation=decoded["operation"],
            timestamp=float(decoded["timestamp"]),
            item=restored_item,
            item_id=decoded.get("item_id"),
            transaction_id=decoded.get("transaction_id"),
        )

        store.pending_operations = [restored_operation]
        primary_store.clear_failures()
        store._reconcile_pending_operations()

        assert not store.pending_operations
        assert isinstance(restored_operation.item, MemoryItem)
        assert isinstance(restored_operation.item.metadata, dict)
        for value in restored_operation.item.metadata.values():
            assert isinstance(value, (str, int, float, bool, type(None), dict, list))


@pytest.mark.medium
def test_with_fallback(primary_store, fallback_store):
    """Test the with_fallback function."""
    store = with_fallback(primary_store, [fallback_store])
    assert isinstance(store, FallbackStore)
    assert store.primary_store is primary_store
    assert store.fallback_stores == [fallback_store]
