"""
Unit tests for the recovery mechanisms for memory operations.
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from devsynth.application.memory.recovery import (
    MemorySnapshot,
    OperationLog,
    RecoveryError,
    RecoveryManager,
    get_recovery_manager,
    with_recovery,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    for root, dirs, files in os.walk(temp_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(temp_dir)


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


class TestMemorySnapshot:
    """Tests for the MemorySnapshot class."""

    @pytest.mark.medium
    @pytest.mark.medium
    def test_snapshot_initialization(self, memory_item):
        """Test that MemorySnapshot initializes with expected values."""
        snapshot = MemorySnapshot(
            store_id="test-store", items=[memory_item], metadata={"version": "1.0"}
        )
        assert snapshot.store_id == "test-store"
        assert len(snapshot.items) == 1
        assert snapshot.items[0].id == "test-item-1"
        assert snapshot.metadata == {"version": "1.0"}
        assert isinstance(snapshot.created_at, datetime)
        assert snapshot.snapshot_id.startswith("test-store_")

    @pytest.mark.medium
    def test_add_item(self, memory_item):
        """Test adding an item to a snapshot."""
        snapshot = MemorySnapshot(store_id="test-store")
        assert len(snapshot.items) == 0
        snapshot.add_item(memory_item)
        assert len(snapshot.items) == 1
        assert snapshot.items[0].id == "test-item-1"

    @pytest.mark.medium
    def test_remove_item(self, memory_item):
        """Test removing an item from a snapshot."""
        snapshot = MemorySnapshot(store_id="test-store", items=[memory_item])
        assert len(snapshot.items) == 1
        result = snapshot.remove_item("test-item-1")
        assert result is True
        assert len(snapshot.items) == 0
        result = snapshot.remove_item("non-existent")
        assert result is False

    @pytest.mark.medium
    def test_get_item(self, memory_item):
        """Test getting an item from a snapshot."""
        snapshot = MemorySnapshot(store_id="test-store", items=[memory_item])
        item = snapshot.get_item("test-item-1")
        assert item is not None
        assert item.id == "test-item-1"
        item = snapshot.get_item("non-existent")
        assert item is None

    @pytest.mark.medium
    def test_snapshot_save_and_load(self, temp_dir, memory_item):
        """Test saving and loading a snapshot."""
        snapshot = MemorySnapshot(
            store_id="test-store", items=[memory_item], metadata={"version": "1.0"}
        )
        filepath = snapshot.save(temp_dir)
        assert os.path.exists(filepath)
        loaded_snapshot = MemorySnapshot.load(filepath)
        assert loaded_snapshot.store_id == "test-store"
        assert loaded_snapshot.snapshot_id == snapshot.snapshot_id
        assert loaded_snapshot.metadata == {"version": "1.0"}
        assert len(loaded_snapshot.items) == 1
        assert loaded_snapshot.items[0].id == "test-item-1"
        assert loaded_snapshot.items[0].content == "This is a test item"
        assert loaded_snapshot.items[0].memory_type == MemoryType.WORKING

    @pytest.mark.medium
    def test_snapshot_load_invalid_file(self, temp_dir):
        """Test loading an invalid snapshot file."""
        filepath = os.path.join(temp_dir, "invalid_snapshot.json")
        with open(filepath, "w") as f:
            f.write("invalid json")
        with pytest.raises(RecoveryError):
            MemorySnapshot.load(filepath)


class TestOperationLog:
    """Tests for the OperationLog class."""

    @pytest.mark.medium
    @pytest.mark.medium
    def test_operationlog_initialization(self):
        """Test that OperationLog initializes with expected values."""
        log = OperationLog(store_id="test-store")
        assert log.store_id == "test-store"
        assert log.operations == []

    @pytest.mark.medium
    def test_operationlog_log_operation(self):
        """Test logging an operation."""
        log = OperationLog(store_id="test-store")
        log.log_operation(
            operation_type="store", operation_data={"item_id": "test-item-1"}
        )
        assert len(log.operations) == 1
        assert log.operations[0]["type"] == "store"
        assert log.operations[0]["data"] == {"item_id": "test-item-1"}
        assert "timestamp" in log.operations[0]
        timestamp = datetime.now()
        log.log_operation(
            operation_type="delete",
            operation_data={"item_id": "test-item-2"},
            timestamp=timestamp,
        )
        assert len(log.operations) == 2
        assert log.operations[1]["type"] == "delete"
        assert log.operations[1]["data"] == {"item_id": "test-item-2"}
        assert log.operations[1]["timestamp"] == timestamp.isoformat()

    @pytest.mark.medium
    def test_operationlog_save_and_load(self, temp_dir):
        """Test saving and loading an operation log."""
        log = OperationLog(store_id="test-store")
        log.log_operation(
            operation_type="store", operation_data={"item_id": "test-item-1"}
        )
        log.log_operation(
            operation_type="delete", operation_data={"item_id": "test-item-2"}
        )
        filepath = log.save(temp_dir)
        assert os.path.exists(filepath)
        loaded_log = OperationLog.load(filepath)
        assert loaded_log.store_id == "test-store"
        assert len(loaded_log.operations) == 2
        assert loaded_log.operations[0]["type"] == "store"
        assert loaded_log.operations[0]["data"] == {"item_id": "test-item-1"}
        assert loaded_log.operations[1]["type"] == "delete"
        assert loaded_log.operations[1]["data"] == {"item_id": "test-item-2"}

    @pytest.mark.medium
    def test_operationlog_load_invalid_file(self, temp_dir):
        """Test loading an invalid operation log file."""
        filepath = os.path.join(temp_dir, "invalid_log.json")
        with open(filepath, "w") as f:
            f.write("invalid json")
        with pytest.raises(RecoveryError):
            OperationLog.load(filepath)

    @pytest.mark.medium
    def test_replay(self, memory_item):
        """Test replaying operations on a memory store."""
        log = OperationLog(store_id="test-store")
        log.log_operation(
            operation_type="store", operation_data={"item": memory_item.to_dict()}
        )
        log.log_operation(
            operation_type="delete", operation_data={"item_id": "test-item-2"}
        )
        mock_store = MagicMock()
        replayed_count = log.replay(mock_store)
        assert replayed_count == 2
        mock_store.store.assert_called_once()
        mock_store.delete.assert_called_once_with("test-item-2")

    @pytest.mark.medium
    def test_replay_with_time_range(self):
        """Test replaying operations within a time range."""
        log = OperationLog(store_id="test-store")
        timestamp1 = datetime(2025, 1, 1, 12, 0, 0)
        timestamp2 = datetime(2025, 1, 2, 12, 0, 0)
        timestamp3 = datetime(2025, 1, 3, 12, 0, 0)
        log.log_operation(
            operation_type="store",
            operation_data={"item_id": "test-item-1"},
            timestamp=timestamp1,
        )
        log.log_operation(
            operation_type="store",
            operation_data={"item_id": "test-item-2"},
            timestamp=timestamp2,
        )
        log.log_operation(
            operation_type="store",
            operation_data={"item_id": "test-item-3"},
            timestamp=timestamp3,
        )
        mock_store = MagicMock()
        start_time = datetime(2025, 1, 1, 18, 0, 0)
        end_time = datetime(2025, 1, 2, 18, 0, 0)
        replayed_count = log.replay(
            mock_store, start_time=start_time, end_time=end_time
        )
        assert replayed_count == 1
        mock_store.store.assert_called_once()

    @pytest.mark.medium
    def test_replay_failure(self):
        """Test handling of failures during replay."""
        log = OperationLog(store_id="test-store")
        log.log_operation(
            operation_type="store", operation_data={"item_id": "test-item-1"}
        )
        mock_store = MagicMock()
        mock_store.store.side_effect = ValueError("test error")
        with pytest.raises(RecoveryError):
            log.replay(mock_store)


class TestRecoveryManager:
    """Tests for the RecoveryManager class."""

    @pytest.mark.medium
    @pytest.mark.medium
    def test_recovery_manager_initialization(self, temp_dir):
        """Test that RecoveryManager initializes with expected values."""
        manager = RecoveryManager(recovery_dir=temp_dir)
        assert manager.recovery_dir == temp_dir
        assert manager.snapshots == {}
        assert manager.operation_logs == {}
        assert os.path.exists(temp_dir)

    @pytest.mark.medium
    def test_create_snapshot(self, memory_item):
        """Test creating a snapshot of a memory store."""
        manager = RecoveryManager()
        mock_store = MagicMock()
        mock_store.get_all_items.return_value = [memory_item]
        snapshot = manager.create_snapshot(
            store_id="test-store", store=mock_store, metadata={"version": "1.0"}
        )
        assert snapshot.store_id == "test-store"
        assert len(snapshot.items) == 1
        assert snapshot.items[0].id == "test-item-1"
        assert snapshot.metadata == {"version": "1.0"}
        assert "test-store" in manager.snapshots
        assert manager.snapshots["test-store"] is snapshot

    @pytest.mark.medium
    def test_get_operation_log(self):
        """Test getting or creating an operation log."""
        manager = RecoveryManager()
        log = manager.get_operation_log("test-store")
        assert log.store_id == "test-store"
        assert log.operations == []
        same_log = manager.get_operation_log("test-store")
        assert same_log is log

    @pytest.mark.medium
    def test_recovery_manager_log_operation(self):
        """Test logging an operation."""
        manager = RecoveryManager()
        manager.log_operation(
            store_id="test-store",
            operation_type="store",
            operation_data={"item_id": "test-item-1"},
        )
        assert "test-store" in manager.operation_logs
        log = manager.operation_logs["test-store"]
        assert len(log.operations) == 1
        assert log.operations[0]["type"] == "store"
        assert log.operations[0]["data"] == {"item_id": "test-item-1"}

    @pytest.mark.medium
    def test_restore_from_snapshot(self, memory_item):
        """Test restoring a memory store from a snapshot."""
        manager = RecoveryManager()
        snapshot = MemorySnapshot(store_id="test-store", items=[memory_item])
        manager.snapshots["test-store"] = snapshot
        mock_store = MagicMock()
        result = manager.restore_from_snapshot(store_id="test-store", store=mock_store)
        assert result is True
        mock_store.store.assert_called_once()

    @pytest.mark.medium
    def test_restore_from_snapshot_no_snapshot(self):
        """Test restoring a memory store when no snapshot exists."""
        manager = RecoveryManager()
        mock_store = MagicMock()
        result = manager.restore_from_snapshot(
            store_id="non-existent", store=mock_store
        )
        assert result is False
        mock_store.store.assert_not_called()

    @pytest.mark.medium
    def test_restore_from_snapshot_failure(self, memory_item):
        """Test handling of failures during snapshot restoration."""
        manager = RecoveryManager()
        snapshot = MemorySnapshot(store_id="test-store", items=[memory_item])
        manager.snapshots["test-store"] = snapshot
        mock_store = MagicMock()
        mock_store.store.side_effect = ValueError("test error")
        result = manager.restore_from_snapshot(store_id="test-store", store=mock_store)
        assert result is False

    @pytest.mark.medium
    def test_recover_store(self, memory_item):
        """Test recovering a memory store using snapshot and operation log."""
        manager = RecoveryManager()
        snapshot = MemorySnapshot(
            store_id="test-store",
            items=[memory_item],
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        manager.snapshots["test-store"] = snapshot
        log = OperationLog(store_id="test-store")
        log.log_operation(
            operation_type="delete",
            operation_data={"item_id": "test-item-1"},
            timestamp=datetime(2025, 1, 2, 12, 0, 0),
        )
        manager.operation_logs["test-store"] = log
        mock_store = MagicMock()
        result = manager.recover_store(store_id="test-store", store=mock_store)
        assert result is True
        mock_store.store.assert_called_once()
        mock_store.delete.assert_called_once_with("test-item-1")

    @pytest.mark.medium
    def test_recover_store_no_snapshot(self):
        """Test recovering a memory store when no snapshot exists."""
        manager = RecoveryManager()
        mock_store = MagicMock()
        result = manager.recover_store(store_id="non-existent", store=mock_store)
        assert result is False
        mock_store.store.assert_not_called()


class TestWithRecovery:
    """Tests for the with_recovery decorator."""

    @pytest.mark.medium
    @pytest.mark.medium
    def test_successful_execution(self, memory_item):
        """Test that the decorator returns the result when the function succeeds."""
        mock_store = MagicMock()
        mock_store.get_all_items.return_value = [memory_item]

        @with_recovery("test-store")
        def decorated_func(self, store):
            return "success"

        result = decorated_func(mock_store)
        assert result == "success"
        mock_store.get_all_items.assert_called_once()

    @pytest.mark.medium
    def test_execution_failure_with_recovery(self, memory_item):
        """Test that the decorator attempts recovery when the function fails."""
        mock_store = MagicMock()
        mock_store.get_all_items.return_value = [memory_item]

        @with_recovery("test-store")
        def failing_func(store):
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_func(mock_store)
        mock_store.get_all_items.assert_called_once()
        mock_store.store.assert_called()

    @pytest.mark.medium
    def test_no_snapshot_creation(self):
        """Test that the decorator doesn't create a snapshot when requested."""
        mock_store = MagicMock()

        @with_recovery("test-store", create_snapshot=False)
        def decorated_func(self, store):
            return "success"

        result = decorated_func(mock_store)
        assert result == "success"
        mock_store.get_all_items.assert_not_called()


@pytest.mark.medium
def test_global_recovery_manager():
    """Test that the global recovery manager is a singleton."""
    manager1 = get_recovery_manager()
    manager2 = get_recovery_manager()
    assert manager1 is manager2
