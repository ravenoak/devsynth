"""Unit tests for SyncManager Protocol functionality."""

from typing import Any, Dict

import pytest

from devsynth.memory.sync_manager import MemoryStore, SyncManager, ValueT


class MockMemoryStore:
    """Mock implementation of MemoryStore for testing."""

    def __init__(self):
        self._data: dict[str, Any] = {}

    def write(self, key: str, value: Any) -> None:
        """Mock write implementation."""
        self._data[key] = value

    def read(self, key: str) -> Any:
        """Mock read implementation."""
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def snapshot(self) -> dict[str, Any]:
        """Mock snapshot implementation."""
        return self._data.copy()

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Mock restore implementation."""
        self._data = snapshot.copy()


class TestSyncManagerProtocol:
    """Test SyncManager with mock MemoryStore implementations."""

    def test_sync_manager_initialization(self):
        """Test SyncManager initializes correctly with required stores."""
        store1 = MockMemoryStore()
        store2 = MockMemoryStore()

        sync_manager = SyncManager(
            stores={"tinydb": store1, "store2": store2}, required_stores={"tinydb"}
        )

        assert "tinydb" in sync_manager.stores
        assert "store2" in sync_manager.stores

    def test_sync_manager_missing_required_store(self):
        """Test SyncManager raises error for missing required stores."""
        store1 = MockMemoryStore()

        with pytest.raises(ValueError, match="Missing stores: store2"):
            SyncManager(stores={"store1": store1}, required_stores={"store1", "store2"})

    def test_sync_manager_write_to_all_stores(self):
        """Test write operation propagates to all configured stores."""
        store1 = MockMemoryStore()
        store2 = MockMemoryStore()

        sync_manager = SyncManager(
            stores={"tinydb": store1, "store2": store2}, required_stores={"tinydb"}
        )

        sync_manager.write("test_key", "test_value")

        assert store1.read("test_key") == "test_value"
        assert store2.read("test_key") == "test_value"

    def test_sync_manager_read_from_first_store(self):
        """Test read operation returns from first store containing the key."""
        store1 = MockMemoryStore()
        store2 = MockMemoryStore()

        sync_manager = SyncManager(
            stores={"tinydb": store1, "store2": store2}, required_stores={"tinydb"}
        )

        store1.write("test_key", "value_from_store1")

        assert sync_manager.read("test_key") == "value_from_store1"

    def test_sync_manager_read_fallback_to_second_store(self):
        """Test read operation falls back to second store if first doesn't have key."""
        store1 = MockMemoryStore()
        store2 = MockMemoryStore()

        sync_manager = SyncManager(
            stores={"tinydb": store1, "store2": store2}, required_stores={"tinydb"}
        )

        store2.write("test_key", "value_from_store2")

        assert sync_manager.read("test_key") == "value_from_store2"

    def test_sync_manager_read_raises_keyerror_if_not_found(self):
        """Test read operation raises KeyError if key not found in any store."""
        store1 = MockMemoryStore()
        store2 = MockMemoryStore()

        sync_manager = SyncManager(
            stores={"tinydb": store1, "store2": store2}, required_stores={"tinydb"}
        )

        with pytest.raises(KeyError):
            sync_manager.read("nonexistent_key")

    def test_sync_manager_transaction_commit(self):
        """Test transaction commits changes to all stores."""
        store1 = MockMemoryStore()
        store2 = MockMemoryStore()

        sync_manager = SyncManager(
            stores={"tinydb": store1, "store2": store2}, required_stores={"tinydb"}
        )

        with sync_manager.transaction():
            sync_manager.write("key1", "value1")
            sync_manager.write("key2", "value2")

        # Changes should be visible after transaction
        assert store1.read("key1") == "value1"
        assert store2.read("key1") == "value1"
        assert store1.read("key2") == "value2"
        assert store2.read("key2") == "value2"

    def test_sync_manager_transaction_rollback_on_exception(self):
        """Test transaction rolls back changes if exception occurs."""
        store1 = MockMemoryStore()
        store2 = MockMemoryStore()

        sync_manager = SyncManager(stores={"store1": store1, "store2": store2})

        initial_state1 = store1.snapshot()
        initial_state2 = store2.snapshot()

        with pytest.raises(ValueError):
            with sync_manager.transaction():
                sync_manager.write("key1", "value1")
                raise ValueError("Test exception")

        # State should be rolled back
        assert store1.snapshot() == initial_state1
        assert store2.snapshot() == initial_state2

        # Key should not be present
        with pytest.raises(KeyError):
            store1.read("key1")
        with pytest.raises(KeyError):
            store2.read("key1")

    def test_memory_store_protocol_runtime_check(self):
        """Test that our mock store satisfies the MemoryStore protocol."""
        store = MockMemoryStore()

        # This should not raise an error since our mock implements the protocol
        assert isinstance(store, MemoryStore)

    def test_sync_manager_with_generic_type(self):
        """Test SyncManager works with different value types."""
        sync_manager = SyncManager[str](stores={"mock": MockMemoryStore()})

        sync_manager.write("string_key", "string_value")
        sync_manager.write("int_key", 42)  # Type: ignore - testing runtime behavior

        assert sync_manager.read("string_key") == "string_value"
        assert sync_manager.read("int_key") == 42
