"""Fallback mechanisms for memory store failures using typed DTOs."""

from __future__ import annotations

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, cast, TYPE_CHECKING

from collections.abc import Mapping

from devsynth.domain.interfaces.memory import (
    MemorySearchResponse,
    MemoryStore,
    SupportsTransactions,
)
from devsynth.domain.models.memory import MemoryItem
from devsynth.logging_setup import DevSynthLogger

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from devsynth.application.memory.dto import (
        GroupedMemoryResults,
        MemoryMetadata,
        MemoryQueryResults,
        MemoryRecord,
    )

MemoryStoreProtocol = MemoryStore


@dataclass(slots=True)
class PendingOperation:
    operation: str
    timestamp: float
    item: MemoryItem | None = None
    item_id: str | None = None
    transaction_id: str | None = None


class FallbackError(Exception):
    """Exception raised when all fallback attempts fail."""

    def __init__(self, message: str, errors: Optional[dict[str, Exception]] = None):
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


class FallbackStore(MemoryStore, SupportsTransactions):
    """
    Memory store with fallback capabilities.

    This class wraps multiple memory stores and provides fallback capabilities
    when the primary store is unavailable or experiencing issues.
    """

    supports_transactions: bool = True

    def __init__(
        self,
        primary_store: MemoryStoreProtocol,
        fallback_stores: list[MemoryStoreProtocol],
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
        self.store_status: dict[MemoryStoreProtocol, StoreStatus] = {
            primary_store: StoreStatus.AVAILABLE
        }
        for store in fallback_stores:
            self.store_status[store] = StoreStatus.AVAILABLE

        # Last error tracking
        self.last_errors: dict[MemoryStoreProtocol, Exception] = {}

        # Pending operations for reconciliation
        self.pending_operations: list[PendingOperation] = []

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
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    item_id = store.store(item)

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    # Add to pending operations for reconciliation
                    self.pending_operations.append(
                        PendingOperation(
                            operation="store",
                            item=item,
                            timestamp=time.time(),
                        )
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

    def retrieve(self, item_id: str) -> MemoryItem | MemoryRecord:
        """
        Retrieve a memory artefact with fallback.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            Retrieved memory item or DTO record

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
        errors: dict[str, Exception] = {}
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

    def search(
        self, query: Mapping[str, object] | MemoryMetadata
    ) -> MemorySearchResponse:
        """
        Search for memory artefacts with fallback.

        Args:
            query: Search query or metadata filter

        Returns:
            Typed collection of matching memory records or items

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
        errors: dict[str, Exception] = {}
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
        errors: dict[str, Exception] = {}
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
                PendingOperation(
                    operation="delete",
                    item_id=item_id,
                    timestamp=time.time(),
                )
            )

            self.logger.info(
                f"Successfully deleted item in fallback store, "
                f"added to pending operations for reconciliation"
            )

        # Return success if either primary or fallback succeeded
        return primary_success or fallback_success

    def get_all_items(self) -> list[MemoryItem]:
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
        errors: dict[str, Exception] = {}
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
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            if self.store_status[store] != StoreStatus.UNAVAILABLE:
                try:
                    transaction_id = store.begin_transaction()

                    # Update status
                    self.store_status[store] = StoreStatus.AVAILABLE

                    # Add to pending operations for reconciliation
                    self.pending_operations.append(
                        PendingOperation(
                            operation="begin_transaction",
                            transaction_id=transaction_id,
                            timestamp=time.time(),
                        )
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
        errors: dict[str, Exception] = {}
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
                PendingOperation(
                    operation="commit_transaction",
                    transaction_id=transaction_id,
                    timestamp=time.time(),
                )
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
        errors: dict[str, Exception] = {}
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
                PendingOperation(
                    operation="rollback_transaction",
                    transaction_id=transaction_id,
                    timestamp=time.time(),
                )
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
        errors: dict[str, Exception] = {}
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
                operation_type = operation.operation

                if operation_type == "store" and operation.item:
                    self.primary_store.store(operation.item)
                elif operation_type == "delete" and operation.item_id:
                    self.primary_store.delete(operation.item_id)
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

    def get_store_status(self) -> dict[str, str]:
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
    primary_store: MemoryStoreProtocol,
    fallback_stores: list[MemoryStoreProtocol],
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
