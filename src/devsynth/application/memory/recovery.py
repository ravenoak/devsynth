"""
Recovery mechanisms for memory operations.

This module provides recovery mechanisms for memory operations to handle failures
and maintain data integrity during cross-store operations.
"""

import json
import os
import time
import logging
import tempfile
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from devsynth.logging_setup import DevSynthLogger
from devsynth.domain.models.memory import MemoryItem

T = TypeVar('T')


class RecoveryError(Exception):
    """Exception raised when recovery fails."""
    pass


class MemorySnapshot:
    """
    Snapshot of memory store state for recovery.
    
    This class provides functionality to create, save, and restore snapshots
    of memory store state for recovery purposes.
    """
    
    def __init__(
        self,
        store_id: str,
        items: Optional[List[MemoryItem]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize a memory snapshot.
        
        Args:
            store_id: Identifier for the memory store
            items: List of memory items in the snapshot
            metadata: Additional metadata for the snapshot
            logger: Optional logger instance
        """
        self.store_id = store_id
        self.items = items or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.snapshot_id = f"{store_id}_{int(time.time())}_{id(self)}"
        self.logger = logger or DevSynthLogger(__name__)
        
    def add_item(self, item: MemoryItem) -> None:
        """
        Add an item to the snapshot.
        
        Args:
            item: Memory item to add
        """
        self.items.append(item)
        
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from the snapshot.
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            True if the item was removed, False if not found
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                return True
        return False
        
    def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get an item from the snapshot.
        
        Args:
            item_id: ID of the item to get
            
        Returns:
            The memory item if found, None otherwise
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None
        
    def save(self, directory: Optional[str] = None) -> str:
        """
        Save the snapshot to a file.
        
        Args:
            directory: Directory to save the snapshot in (defaults to temp directory)
            
        Returns:
            Path to the saved snapshot file
        """
        if directory is None:
            directory = tempfile.gettempdir()
            
        os.makedirs(directory, exist_ok=True)
        
        # Create a serializable representation of the snapshot
        snapshot_data = {
            "snapshot_id": self.snapshot_id,
            "store_id": self.store_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "items": [item.to_dict() for item in self.items]
        }
        
        # Save to file
        filename = f"memory_snapshot_{self.snapshot_id}.json"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
            
        self.logger.info(f"Saved memory snapshot to {filepath}")
        return filepath
        
    @classmethod
    def load(
        cls,
        filepath: str,
        logger: Optional[logging.Logger] = None
    ) -> 'MemorySnapshot':
        """
        Load a snapshot from a file.
        
        Args:
            filepath: Path to the snapshot file
            logger: Optional logger instance
            
        Returns:
            Loaded memory snapshot
            
        Raises:
            RecoveryError: If the snapshot file cannot be loaded
        """
        logger = logger or DevSynthLogger(__name__)
        
        try:
            with open(filepath, 'r') as f:
                snapshot_data = json.load(f)
                
            # Create a new snapshot
            snapshot = cls(
                store_id=snapshot_data["store_id"],
                metadata=snapshot_data.get("metadata", {}),
                logger=logger
            )
            
            # Set snapshot attributes
            snapshot.snapshot_id = snapshot_data["snapshot_id"]
            snapshot.created_at = datetime.fromisoformat(snapshot_data["created_at"])
            
            # Load items
            from devsynth.domain.models.memory import MemoryItem
            snapshot.items = [
                MemoryItem.from_dict(item_data)
                for item_data in snapshot_data.get("items", [])
            ]
            
            logger.info(f"Loaded memory snapshot from {filepath}")
            return snapshot
        except Exception as e:
            error_message = f"Failed to load memory snapshot from {filepath}: {e}"
            logger.error(error_message)
            raise RecoveryError(error_message) from e


class OperationLog:
    """
    Log of memory operations for recovery.
    
    This class provides functionality to log memory operations and replay them
    for recovery purposes.
    """
    
    def __init__(
        self,
        store_id: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize an operation log.
        
        Args:
            store_id: Identifier for the memory store
            logger: Optional logger instance
        """
        self.store_id = store_id
        self.operations: List[Dict[str, Any]] = []
        self.logger = logger or DevSynthLogger(__name__)
        
    def log_operation(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Log an operation.
        
        Args:
            operation_type: Type of operation (e.g., "store", "delete")
            operation_data: Data for the operation
            timestamp: Optional timestamp for the operation
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        operation = {
            "type": operation_type,
            "data": operation_data,
            "timestamp": timestamp.isoformat()
        }
        
        self.operations.append(operation)
        self.logger.debug(
            f"Logged {operation_type} operation for store {self.store_id}"
        )
        
    def save(self, directory: Optional[str] = None) -> str:
        """
        Save the operation log to a file.
        
        Args:
            directory: Directory to save the log in (defaults to temp directory)
            
        Returns:
            Path to the saved log file
        """
        if directory is None:
            directory = tempfile.gettempdir()
            
        os.makedirs(directory, exist_ok=True)
        
        # Create a serializable representation of the log
        log_data = {
            "store_id": self.store_id,
            "operations": self.operations
        }
        
        # Save to file
        timestamp = int(time.time())
        filename = f"memory_operations_{self.store_id}_{timestamp}.json"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
            
        self.logger.info(f"Saved operation log to {filepath}")
        return filepath
        
    @classmethod
    def load(
        cls,
        filepath: str,
        logger: Optional[logging.Logger] = None
    ) -> 'OperationLog':
        """
        Load an operation log from a file.
        
        Args:
            filepath: Path to the log file
            logger: Optional logger instance
            
        Returns:
            Loaded operation log
            
        Raises:
            RecoveryError: If the log file cannot be loaded
        """
        logger = logger or DevSynthLogger(__name__)
        
        try:
            with open(filepath, 'r') as f:
                log_data = json.load(f)
                
            # Create a new log
            log = cls(
                store_id=log_data["store_id"],
                logger=logger
            )
            
            # Load operations
            log.operations = log_data.get("operations", [])
            
            logger.info(f"Loaded operation log from {filepath}")
            return log
        except Exception as e:
            error_message = f"Failed to load operation log from {filepath}: {e}"
            logger.error(error_message)
            raise RecoveryError(error_message) from e
            
    def replay(
        self,
        store: Any,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Replay operations on a memory store.
        
        Args:
            store: Memory store to replay operations on
            start_time: Optional start time for replay
            end_time: Optional end time for replay
            
        Returns:
            Number of operations replayed
            
        Raises:
            RecoveryError: If replay fails
        """
        # Filter operations by time range
        filtered_operations = self.operations
        
        if start_time is not None:
            start_time_str = start_time.isoformat()
            filtered_operations = [
                op for op in filtered_operations
                if op["timestamp"] >= start_time_str
            ]
            
        if end_time is not None:
            end_time_str = end_time.isoformat()
            filtered_operations = [
                op for op in filtered_operations
                if op["timestamp"] <= end_time_str
            ]
            
        # Replay operations
        replayed_count = 0
        
        for operation in filtered_operations:
            try:
                operation_type = operation["type"]
                operation_data = operation["data"]
                
                if operation_type == "store":
                    # Create MemoryItem from operation data
                    from devsynth.domain.models.memory import MemoryItem
                    item = MemoryItem.from_dict(operation_data["item"])
                    store.store(item)
                    
                elif operation_type == "delete":
                    item_id = operation_data["item_id"]
                    store.delete(item_id)
                    
                # Add more operation types as needed
                
                replayed_count += 1
                
            except Exception as e:
                error_message = (
                    f"Failed to replay {operation_type} operation: {e}"
                )
                self.logger.error(error_message)
                raise RecoveryError(error_message) from e
                
        self.logger.info(
            f"Replayed {replayed_count} operations on store {self.store_id}"
        )
        return replayed_count


class RecoveryManager:
    """
    Manager for memory store recovery.
    
    This class provides functionality to manage recovery for memory stores,
    including creating snapshots, logging operations, and performing recovery.
    """
    
    def __init__(
        self,
        recovery_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize a recovery manager.
        
        Args:
            recovery_dir: Directory for recovery files
            logger: Optional logger instance
        """
        self.recovery_dir = recovery_dir or os.path.join(
            tempfile.gettempdir(), "devsynth_recovery"
        )
        os.makedirs(self.recovery_dir, exist_ok=True)
        
        self.snapshots: Dict[str, MemorySnapshot] = {}
        self.operation_logs: Dict[str, OperationLog] = {}
        self.logger = logger or DevSynthLogger(__name__)
        
    def create_snapshot(
        self,
        store_id: str,
        store: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemorySnapshot:
        """
        Create a snapshot of a memory store.
        
        Args:
            store_id: Identifier for the memory store
            store: Memory store to snapshot
            metadata: Additional metadata for the snapshot
            
        Returns:
            Created memory snapshot
        """
        # Get all items from the store
        items = store.get_all_items()
        
        # Create snapshot
        snapshot = MemorySnapshot(
            store_id=store_id,
            items=items,
            metadata=metadata,
            logger=self.logger
        )
        
        # Save snapshot
        self.snapshots[store_id] = snapshot
        snapshot.save(self.recovery_dir)
        
        self.logger.info(f"Created snapshot for store {store_id}")
        return snapshot
        
    def get_operation_log(self, store_id: str) -> OperationLog:
        """
        Get or create an operation log for a memory store.
        
        Args:
            store_id: Identifier for the memory store
            
        Returns:
            Operation log for the store
        """
        if store_id not in self.operation_logs:
            self.operation_logs[store_id] = OperationLog(
                store_id=store_id,
                logger=self.logger
            )
            
        return self.operation_logs[store_id]
        
    def log_operation(
        self,
        store_id: str,
        operation_type: str,
        operation_data: Dict[str, Any]
    ) -> None:
        """
        Log an operation for a memory store.
        
        Args:
            store_id: Identifier for the memory store
            operation_type: Type of operation
            operation_data: Data for the operation
        """
        log = self.get_operation_log(store_id)
        log.log_operation(operation_type, operation_data)
        
    def restore_from_snapshot(
        self,
        store_id: str,
        store: Any,
        snapshot: Optional[MemorySnapshot] = None
    ) -> bool:
        """
        Restore a memory store from a snapshot.
        
        Args:
            store_id: Identifier for the memory store
            store: Memory store to restore
            snapshot: Optional snapshot to restore from (uses latest if None)
            
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            # Use provided snapshot or get the latest
            if snapshot is None:
                snapshot = self.snapshots.get(store_id)
                
                if snapshot is None:
                    self.logger.warning(
                        f"No snapshot found for store {store_id}"
                    )
                    return False
                    
            # Clear the store (if supported)
            if hasattr(store, "clear"):
                store.clear()
                
            # Restore items from snapshot
            for item in snapshot.items:
                store.store(item)
                
            self.logger.info(
                f"Restored store {store_id} from snapshot {snapshot.snapshot_id}"
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to restore store {store_id} from snapshot: {e}"
            )
            return False
            
    def recover_store(
        self,
        store_id: str,
        store: Any,
        snapshot: Optional[MemorySnapshot] = None,
        operation_log: Optional[OperationLog] = None
    ) -> bool:
        """
        Recover a memory store using snapshot and operation log.
        
        Args:
            store_id: Identifier for the memory store
            store: Memory store to recover
            snapshot: Optional snapshot to recover from
            operation_log: Optional operation log to replay
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            # Restore from snapshot
            if not self.restore_from_snapshot(store_id, store, snapshot):
                return False
                
            # Replay operations from log
            if operation_log is None:
                operation_log = self.operation_logs.get(store_id)
                
            if operation_log is not None:
                # If we have a snapshot, only replay operations after the snapshot
                start_time = None
                if snapshot is not None:
                    start_time = snapshot.created_at
                    
                operation_log.replay(store, start_time=start_time)
                
            self.logger.info(f"Recovered store {store_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to recover store {store_id}: {e}")
            return False


# Global recovery manager
_recovery_manager = RecoveryManager()


def get_recovery_manager() -> RecoveryManager:
    """
    Get the global recovery manager.
    
    Returns:
        The global recovery manager
    """
    return _recovery_manager


def with_recovery(
    store_id: str,
    create_snapshot: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for adding recovery to a function.
    
    Args:
        store_id: Identifier for the memory store
        create_snapshot: Whether to create a snapshot before execution
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Get the recovery manager
            recovery_manager = get_recovery_manager()
            
            # Get the store from args or kwargs
            store = None
            if args and hasattr(args[0], "get_all_items"):
                store = args[0]
            elif "store" in kwargs and hasattr(kwargs["store"], "get_all_items"):
                store = kwargs["store"]
                
            # Create snapshot if requested and store is available
            if create_snapshot and store is not None:
                recovery_manager.create_snapshot(store_id, store)
                
            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Log the error
                recovery_manager.logger.error(
                    f"Error in function {func.__name__}: {e}"
                )
                
                # Attempt recovery if store is available
                if store is not None:
                    recovery_manager.logger.info(
                        f"Attempting recovery for store {store_id}"
                    )
                    recovery_manager.recover_store(store_id, store)
                    
                # Re-raise the exception
                raise
                
        return cast(Callable[..., T], wrapper)
        
    return decorator