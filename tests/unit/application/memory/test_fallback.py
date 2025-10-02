"""
Unit tests for the fallback mechanisms for memory store failures.
"""

from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from devsynth.application.memory.fallback import (
    FallbackError,
    FallbackStore,
    StoreStatus,
    with_fallback,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType


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
    """Create a mock primary store."""
    store = MagicMock()
    store.store.return_value = "test-item-1"
    store.retrieve.return_value = MemoryItem(
        id="test-item-1", content="This is a test item", memory_type=MemoryType.WORKING
    )
    store.search.return_value = [
        MemoryItem(
            id="test-item-1",
            content="This is a test item",
            memory_type=MemoryType.WORKING,
        )
    ]
    store.delete.return_value = True
    store.get_all_items.return_value = [
        MemoryItem(
            id="test-item-1",
            content="This is a test item",
            memory_type=MemoryType.WORKING,
        )
    ]
    store.begin_transaction.return_value = "tx-1"
    store.commit_transaction.return_value = True
    store.rollback_transaction.return_value = True
    store.is_transaction_active.return_value = True
    return store


@pytest.fixture
def fallback_store():
    """Create a mock fallback store."""
    store = MagicMock()
    store.store.return_value = "test-item-1"
    store.retrieve.return_value = MemoryItem(
        id="test-item-1",
        content="This is a test item from fallback",
        memory_type=MemoryType.WORKING,
    )
    store.search.return_value = [
        MemoryItem(
            id="test-item-1",
            content="This is a test item from fallback",
            memory_type=MemoryType.WORKING,
        )
    ]
    store.delete.return_value = True
    store.get_all_items.return_value = [
        MemoryItem(
            id="test-item-1",
            content="This is a test item from fallback",
            memory_type=MemoryType.WORKING,
        )
    ]
    store.begin_transaction.return_value = "tx-1"
    store.commit_transaction.return_value = True
    store.rollback_transaction.return_value = True
    store.is_transaction_active.return_value = True
    return store


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
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE
        assert store.last_errors == {}
        assert store.pending_operations == []

    @pytest.mark.medium
    def test_store_primary_success(self, primary_store, fallback_store, memory_item):
        """Test storing an item when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item_id = store.store(memory_item)
        assert item_id == "test-item-1"
        primary_store.store.assert_called_once()
        fallback_store.store.assert_called_once()
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_store_primary_failure(self, primary_store, fallback_store, memory_item):
        """Test storing an item when the primary store fails."""
        primary_store.store.side_effect = ValueError("Primary store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item_id = store.store(memory_item)
        assert item_id == "test-item-1"
        primary_store.store.assert_called_once()
        fallback_store.store.assert_called_once()
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "store"
        assert store.pending_operations[0].item == memory_item

    @pytest.mark.medium
    def test_store_all_failures(self, primary_store, fallback_store, memory_item):
        """Test storing an item when all stores fail."""
        primary_store.store.side_effect = ValueError("Primary store failed")
        fallback_store.store.side_effect = ValueError("Fallback store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.store(memory_item)
        assert "All stores failed to store item" in str(excinfo.value)
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_retrieve_primary_success(self, primary_store, fallback_store):
        """Test retrieving an item when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item = store.retrieve("test-item-1")
        assert item.id == "test-item-1"
        assert item.content == "This is a test item"
        primary_store.retrieve.assert_called_once_with("test-item-1")
        fallback_store.retrieve.assert_not_called()
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_retrieve_primary_failure(self, primary_store, fallback_store):
        """Test retrieving an item when the primary store fails."""
        primary_store.retrieve.side_effect = ValueError("Primary store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item = store.retrieve("test-item-1")
        assert item.id == "test-item-1"
        assert item.content == "This is a test item from fallback"
        primary_store.retrieve.assert_called_once_with("test-item-1")
        fallback_store.retrieve.assert_called_once_with("test-item-1")
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_retrieve_primary_not_found(self, primary_store, fallback_store):
        """Test retrieving an item when the primary store doesn't find it."""
        primary_store.retrieve.side_effect = KeyError("Item not found")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        item = store.retrieve("test-item-1")
        assert item.id == "test-item-1"
        assert item.content == "This is a test item from fallback"
        primary_store.retrieve.assert_called_once_with("test-item-1")
        fallback_store.retrieve.assert_called_once_with("test-item-1")
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_retrieve_all_failures(self, primary_store, fallback_store):
        """Test retrieving an item when all stores fail."""
        primary_store.retrieve.side_effect = ValueError("Primary store failed")
        fallback_store.retrieve.side_effect = ValueError("Fallback store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(KeyError) as excinfo:
            store.retrieve("test-item-1")
        assert "Item test-item-1 not found in any store" in str(excinfo.value)
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_search_primary_success(self, primary_store, fallback_store):
        """Test searching for items when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        items = store.search({"query": "test"})
        assert len(items) == 1
        assert items[0].id == "test-item-1"
        assert items[0].content == "This is a test item"
        primary_store.search.assert_called_once_with({"query": "test"})
        fallback_store.search.assert_not_called()
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_search_primary_failure(self, primary_store, fallback_store):
        """Test searching for items when the primary store fails."""
        primary_store.search.side_effect = ValueError("Primary store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        items = store.search({"query": "test"})
        assert len(items) == 1
        assert items[0].id == "test-item-1"
        assert items[0].content == "This is a test item from fallback"
        primary_store.search.assert_called_once_with({"query": "test"})
        fallback_store.search.assert_called_once_with({"query": "test"})
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_search_all_failures(self, primary_store, fallback_store):
        """Test searching for items when all stores fail."""
        primary_store.search.side_effect = ValueError("Primary store failed")
        fallback_store.search.side_effect = ValueError("Fallback store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.search({"query": "test"})
        assert "All stores failed to search" in str(excinfo.value)
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_delete_primary_success(self, primary_store, fallback_store):
        """Test deleting an item when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.delete("test-item-1")
        assert result is True
        primary_store.delete.assert_called_once_with("test-item-1")
        fallback_store.delete.assert_called_once_with("test-item-1")
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_delete_primary_failure(self, primary_store, fallback_store):
        """Test deleting an item when the primary store fails."""
        primary_store.delete.side_effect = ValueError("Primary store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.delete("test-item-1")
        assert result is True
        primary_store.delete.assert_called_once_with("test-item-1")
        fallback_store.delete.assert_called_once_with("test-item-1")
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "delete"
        assert store.pending_operations[0].item_id == "test-item-1"

    @pytest.mark.medium
    def test_delete_all_failures(self, primary_store, fallback_store):
        """Test deleting an item when all stores fail."""
        primary_store.delete.side_effect = ValueError("Primary store failed")
        fallback_store.delete.side_effect = ValueError("Fallback store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.delete("test-item-1")
        assert result is False
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.DEGRADED

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
        primary_store.get_all_items.assert_called_once()
        fallback_store.get_all_items.assert_not_called()
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_get_all_items_primary_failure(self, primary_store, fallback_store):
        """Test getting all items when the primary store fails."""
        primary_store.get_all_items.side_effect = ValueError("Primary store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        items = store.get_all_items()
        assert len(items) == 1
        assert items[0].id == "test-item-1"
        assert items[0].content == "This is a test item from fallback"
        primary_store.get_all_items.assert_called_once()
        fallback_store.get_all_items.assert_called_once()
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_get_all_items_all_failures(self, primary_store, fallback_store):
        """Test getting all items when all stores fail."""
        primary_store.get_all_items.side_effect = ValueError("Primary store failed")
        fallback_store.get_all_items.side_effect = ValueError("Fallback store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.get_all_items()
        assert "All stores failed to get all items" in str(excinfo.value)
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_begin_transaction_primary_success(self, primary_store, fallback_store):
        """Test beginning a transaction when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        transaction_id = store.begin_transaction()
        assert transaction_id == "tx-1"
        primary_store.begin_transaction.assert_called_once()
        fallback_store.begin_transaction.assert_called_once()
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_begin_transaction_primary_failure(self, primary_store, fallback_store):
        """Test beginning a transaction when the primary store fails."""
        primary_store.begin_transaction.side_effect = ValueError("Primary store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        transaction_id = store.begin_transaction()
        assert transaction_id == "tx-1"
        primary_store.begin_transaction.assert_called_once()
        fallback_store.begin_transaction.assert_called_once()
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "begin_transaction"
        assert store.pending_operations[0].transaction_id == "tx-1"

    @pytest.mark.medium
    def test_begin_transaction_all_failures(self, primary_store, fallback_store):
        """Test beginning a transaction when all stores fail."""
        primary_store.begin_transaction.side_effect = ValueError("Primary store failed")
        fallback_store.begin_transaction.side_effect = ValueError(
            "Fallback store failed"
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        with pytest.raises(FallbackError) as excinfo:
            store.begin_transaction()
        assert "All stores failed to begin transaction" in str(excinfo.value)
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_commit_transaction_primary_success(self, primary_store, fallback_store):
        """Test committing a transaction when the primary store succeeds."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.commit_transaction("tx-1")
        assert result is True
        primary_store.commit_transaction.assert_called_once_with("tx-1")
        fallback_store.commit_transaction.assert_called_once_with("tx-1")
        assert store.store_status[primary_store] == StoreStatus.AVAILABLE
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE

    @pytest.mark.medium
    def test_commit_transaction_primary_failure(self, primary_store, fallback_store):
        """Test committing a transaction when the primary store fails."""
        primary_store.commit_transaction.side_effect = ValueError(
            "Primary store failed"
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.commit_transaction("tx-1")
        assert result is True
        primary_store.commit_transaction.assert_called_once_with("tx-1")
        fallback_store.commit_transaction.assert_called_once_with("tx-1")
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.AVAILABLE
        assert len(store.pending_operations) == 1
        assert store.pending_operations[0].operation == "commit_transaction"
        assert store.pending_operations[0].transaction_id == "tx-1"

    @pytest.mark.medium
    def test_commit_transaction_all_failures(self, primary_store, fallback_store):
        """Test committing a transaction when all stores fail."""
        primary_store.commit_transaction.side_effect = ValueError(
            "Primary store failed"
        )
        fallback_store.commit_transaction.side_effect = ValueError(
            "Fallback store failed"
        )
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        result = store.commit_transaction("tx-1")
        assert result is False
        assert store.store_status[primary_store] == StoreStatus.DEGRADED
        assert store.store_status[fallback_store] == StoreStatus.DEGRADED

    @pytest.mark.medium
    def test_reconcile_pending_operations(
        self, primary_store, fallback_store, memory_item
    ):
        """Test reconciling pending operations when the primary store becomes available."""
        primary_store.store.side_effect = [ValueError("Primary store failed"), None]
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        store.store(memory_item)
        assert len(store.pending_operations) == 1
        primary_store.reset_mock()
        primary_store.store.side_effect = None
        store._reconcile_pending_operations()
        primary_store.store.assert_called_once()
        assert len(store.pending_operations) == 0

    @pytest.mark.medium
    def test_get_store_status(self, primary_store, fallback_store):
        """Test getting the status of all stores."""
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        status = store.get_store_status()
        assert status["primary"] == "AVAILABLE"
        assert status["fallbacks"] == ["AVAILABLE"]

    @pytest.mark.medium
    def test_get_pending_operations_count(
        self, primary_store, fallback_store, memory_item
    ):
        """Test getting the number of pending operations."""
        primary_store.store.side_effect = ValueError("Primary store failed")
        store = FallbackStore(
            primary_store=primary_store, fallback_stores=[fallback_store]
        )
        store.store(memory_item)
        count = store.get_pending_operations_count()
        assert count == 1


@pytest.mark.medium
def test_with_fallback(primary_store, fallback_store):
    """Test the with_fallback function."""
    store = with_fallback(primary_store, [fallback_store])
    assert isinstance(store, FallbackStore)
    assert store.primary_store is primary_store
    assert store.fallback_stores == [fallback_store]
