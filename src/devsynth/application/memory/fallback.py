"""
Fallback mechanisms for memory store failures.

This module provides fallback mechanisms to maintain system availability
when memory stores are unavailable or experiencing issues.
"""

import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem
from devsynth.logging_setup import DevSynthLogger

T = TypeVar("T")


class FallbackError(Exception):
    """Exception raised when all fallback attempts fail."""

    def __init__(self, message: str, errors: Optional[Dict[str, Exception]] = None):
        """
        Initialize the fallback error.

        Args:
            message: Error message
            errors: Dictionary mapping store IDs to exceptions
        """
        super().__init__(message)
        self.errors = errors or {}


class StoreStatus(Enum):
    """Status of a memory store."""

    AVAILABLE = "AVAILABLE"  # Store is available and functioning normally
    DEGRADED = "DEGRADED"  # Store is available but experiencing issues
    UNAVAILABLE = "UNAVAILABLE"  # Store is unavailable


class FallbackStore(MemoryStore):
    """
    Memory store with fallback capabilities.

    This class wraps multiple memory stores and provides fallback capabilities
    when the primary store is unavailable or experiencing issues.
    """

    def __init__(
        self,
        primary_store: MemoryStore,
        fallback_stores: List[MemoryStore],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a fallback store.

        Args:
            primary_store: Primary memory store
            fallback_stores: List of fallback memory stores
            logger: Optional logger instance
        """
        self.primary_store = primary_store
        self.fallback_stores = fallback_stores
        self.logger = logger or DevSynthLogger(__name__)

        # Store status tracking
        self.store_status: Dict[MemoryStore, StoreStatus] = {
            primary_store: StoreStatus.AVAILABLE
        }
        for store in fallback_stores:
            self.store_status[store] = StoreStatus.AVAILABLE

        # Last error tracking
        self.last_errors: Dict[MemoryStore, Exception] = {}

        # Pending operations for reconciliation
        self.pending_operations: List[Dict[str, Any]] = []

    def store(self, item: MemoryItem) -> str:
        """
        Store a memory item with fallback.

        Args:
            item: Memory item to store

        Returns:
            ID of the stored item

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                item_id = self.primary_store.store(item)

                # If we were in degraded mode, try to reconcile pending operations
                if self.store_status[self.primary_store] == StoreStatus.DEGRADED:
                    self.logger.info(
                        "Primary store is available again, reconciling pending operations"
                    )
                    self._reconcile_pending_operations()

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE

                # Store in fallback stores asynchronously (in a real implementation)
                # For now, just store sequentially
                for store in self.fallback_stores:
                    try:
                        store.store(item)
                        self.store_status[store] = StoreStatus.AVAILABLE
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to store item in fallback store: {e}"
                        )
                        self.last_errors[store] = e
                        self.store_status[store] = StoreStatus.DEGRADED

                return item_id
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    item_id = store.store(item)

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    # Add to pending operations for reconciliation
                    self.pending_operations.append(
                        {"type": "store", "item": item, "timestamp": time.time()}
                    )

                    self.logger.info(
                        f"Successfully stored item in fallback store, "
                        f"added to pending operations for reconciliation"
                    )

                    return item_id
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # All stores failed
        error_message = "All stores failed to store item"
        self.logger.error(error_message)
        raise FallbackError(error_message, errors)

    def retrieve(self, item_id: str) -> MemoryItem:
        """
        Retrieve a memory item with fallback.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            Retrieved memory item

        Raises:
            FallbackError: If all stores fail
            KeyError: If the item is not found in any store
        """
        # Try primary store first
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                item = self.primary_store.retrieve(item_id)

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE

                return item
            except KeyError:
                # Item not found, try fallback stores
                pass
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    item = store.retrieve(item_id)

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    return item
                except KeyError:
                    # Item not found, try next store
                    pass
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # Item not found in any store
        error_message = f"Item {item_id} not found in any store"
        self.logger.error(error_message)
        raise KeyError(error_message)

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Search for memory items with fallback.

        Args:
            query: Search query

        Returns:
            List of matching memory items

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                items = self.primary_store.search(query)

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE

                return items
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    items = store.search(query)

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    return items
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # All stores failed
        error_message = "All stores failed to search"
        self.logger.error(error_message)
        raise FallbackError(error_message, errors)

    def delete(self, item_id: str) -> bool:
        """
        Delete a memory item with fallback.

        Args:
            item_id: ID of the item to delete

        Returns:
            True if the item was deleted, False otherwise

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        primary_success = False
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                primary_success = self.primary_store.delete(item_id)

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        fallback_success = False
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    result = store.delete(item_id)
                    fallback_success = fallback_success or result

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # If primary store failed but fallback succeeded, add to pending operations
        if not primary_success and fallback_success:
            self.pending_operations.append(
                {"type": "delete", "item_id": item_id, "timestamp": time.time()}
            )

            self.logger.info(
                f"Successfully deleted item in fallback store, "
                f"added to pending operations for reconciliation"
            )

        # Return success if either primary or fallback succeeded
        return primary_success or fallback_success

    def get_all_items(self) -> List[MemoryItem]:
        """
        Get all memory items with fallback.

        Returns:
            List of all memory items

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                items = self.primary_store.get_all_items()

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE

                return items
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    items = store.get_all_items()

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    return items
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # All stores failed
        error_message = "All stores failed to get all items"
        self.logger.error(error_message)
        raise FallbackError(error_message, errors)

    def begin_transaction(self) -> str:
        """
        Begin a transaction with fallback.

        Returns:
            Transaction ID

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                transaction_id = self.primary_store.begin_transaction()

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE

                # Begin transaction on fallback stores
                for store in self.fallback_stores:
                    try:
                        store.begin_transaction()
                        self.store_status[store] = StoreStatus.AVAILABLE
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to begin transaction on fallback store: {e}"
                        )
                        self.last_errors[store] = e
                        self.store_status[store] = StoreStatus.DEGRADED

                return transaction_id
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    transaction_id = store.begin_transaction()

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    # Add to pending operations for reconciliation
                    self.pending_operations.append(
                        {
                            "type": "begin_transaction",
                            "transaction_id": transaction_id,
                            "timestamp": time.time(),
                        }
                    )

                    self.logger.info(
                        f"Successfully began transaction in fallback store, "
                        f"added to pending operations for reconciliation"
                    )

                    return transaction_id
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # All stores failed
        error_message = "All stores failed to begin transaction"
        self.logger.error(error_message)
        raise FallbackError(error_message, errors)

    def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction with fallback.

        Args:
            transaction_id: Transaction ID

        Returns:
            True if the transaction was committed, False otherwise

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        primary_success = False
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                primary_success = self.primary_store.commit_transaction(transaction_id)

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        fallback_success = False
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    result = store.commit_transaction(transaction_id)
                    fallback_success = fallback_success or result

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # If primary store failed but fallback succeeded, add to pending operations
        if not primary_success and fallback_success:
            self.pending_operations.append(
                {
                    "type": "commit_transaction",
                    "transaction_id": transaction_id,
                    "timestamp": time.time(),
                }
            )

            self.logger.info(
                f"Successfully committed transaction in fallback store, "
                f"added to pending operations for reconciliation"
            )

        # Return success if either primary or fallback succeeded
        return primary_success or fallback_success

    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction with fallback.

        Args:
            transaction_id: Transaction ID

        Returns:
            True if the transaction was rolled back, False otherwise

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        primary_success = False
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                primary_success = self.primary_store.rollback_transaction(
                    transaction_id
                )

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        fallback_success = False
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    result = store.rollback_transaction(transaction_id)
                    fallback_success = fallback_success or result

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # If primary store failed but fallback succeeded, add to pending operations
        if not primary_success and fallback_success:
            self.pending_operations.append(
                {
                    "type": "rollback_transaction",
                    "transaction_id": transaction_id,
                    "timestamp": time.time(),
                }
            )

            self.logger.info(
                f"Successfully rolled back transaction in fallback store, "
                f"added to pending operations for reconciliation"
            )

        # Return success if either primary or fallback succeeded
        return primary_success or fallback_success

    def is_transaction_active(self, transaction_id: str) -> bool:
        """
        Check if a transaction is active with fallback.

        Args:
            transaction_id: Transaction ID

        Returns:
            True if the transaction is active, False otherwise

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        if self.store_status[self.primary_store] != StoreStatus.UNAVAILABLE:
            try:
                result = self.primary_store.is_transaction_active(transaction_id)

                # Update status
                self.store_status[self.primary_store] = StoreStatus.AVAILABLE

                return result
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                self.last_errors[self.primary_store] = e
                self.store_status[self.primary_store] = StoreStatus.DEGRADED

        # Try fallback stores
        errors = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    result = store.is_transaction_active(transaction_id)

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    return result
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    self.last_errors[store] = e
                    self.store_status[store] = StoreStatus.DEGRADED
                    errors[str(id(store))] = e

        # All stores failed
        error_message = "All stores failed to check transaction status"
        self.logger.error(error_message)
        raise FallbackError(error_message, errors)

    def _reconcile_pending_operations(self) -> None:
        """
        Reconcile pending operations with the primary store.

        This method is called when the primary store becomes available again
        after being in degraded mode.
        """
        if not self.pending_operations:
            return

        self.logger.info(
            f"Reconciling {len(self.pending_operations)} pending operations"
        )

        # Process pending operations in order
        for operation in self.pending_operations[:]:
            try:
                operation_type = operation["type"]

                if operation_type == "store":
                    item = operation["item"]
                    self.primary_store.store(item)
                elif operation_type == "delete":
                    item_id = operation["item_id"]
                    self.primary_store.delete(item_id)
                elif operation_type == "begin_transaction":
                    # Skip begin_transaction operations
                    pass
                elif operation_type == "commit_transaction":
                    # Skip commit_transaction operations
                    pass
                elif operation_type == "rollback_transaction":
                    # Skip rollback_transaction operations
                    pass

                # Remove from pending operations
                self.pending_operations.remove(operation)

            except Exception as e:
                self.logger.warning(
                    f"Failed to reconcile {operation_type} operation: {e}"
                )

        self.logger.info(
            f"Reconciliation complete, {len(self.pending_operations)} operations remaining"
        )

    def get_store_status(self) -> Dict[str, str]:
        """
        Get the status of all stores.

        Returns:
            Dictionary mapping store IDs to status strings
        """
        return {
            "primary": self.store_status[self.primary_store].value,
            "fallbacks": [
                self.store_status[store].value for store in self.fallback_stores
            ],
        }

    def get_pending_operations_count(self) -> int:
        """
        Get the number of pending operations.

        Returns:
            Number of pending operations
        """
        return len(self.pending_operations)


def with_fallback(
    primary_store: MemoryStore, fallback_stores: List[MemoryStore]
) -> FallbackStore:
    """
    Create a fallback store.

    Args:
        primary_store: Primary memory store
        fallback_stores: List of fallback memory stores

    Returns:
        Fallback store
    """
    return FallbackStore(primary_store, fallback_stores)
