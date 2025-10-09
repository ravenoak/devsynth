"""Fallback mechanisms for memory store failures using typed DTOs."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Protocol, TypeAlias, cast

from devsynth.application.memory.dto import (
    GroupedMemoryResults,
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
)
from devsynth.domain.interfaces.memory import (
    MemorySearchResponse,
    MemoryStore,
    SupportsTransactions,
)
from devsynth.domain.models.memory import MemoryItem
from devsynth.logging_setup import DevSynthLogger


class FallbackMemoryStore(MemoryStore, SupportsTransactions, Protocol):
    def get_all_items(self) -> list[MemoryItem]:  # pragma: no cover - protocol
        ...


MemoryStoreProtocol = FallbackMemoryStore

MemoryRetrieveResult: TypeAlias = MemoryRecord
"""Typed DTO returned from :meth:`FallbackStore.retrieve`."""

MemorySearchResult: TypeAlias = MemoryQueryResults | GroupedMemoryResults
"""Typed DTO returned from :meth:`FallbackStore.search`."""


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


@dataclass(slots=True)
class StoreState:
    """Track runtime health for a specific :class:`MemoryStore` instance."""

    status: StoreStatus = StoreStatus.AVAILABLE
    last_error: Exception | None = None

    def mark_available(self) -> None:
        self.status = StoreStatus.AVAILABLE
        self.last_error = None

    def mark_degraded(self, error: Exception) -> None:
        self.status = StoreStatus.DEGRADED
        self.last_error = error

    def mark_unavailable(self, error: Exception | None = None) -> None:
        self.status = StoreStatus.UNAVAILABLE
        self.last_error = error


@dataclass(slots=True)
class StoreStatusReport:
    """Snapshot of the fallback store health."""

    primary: StoreStatus
    fallbacks: list[StoreStatus]
    last_errors: dict[str, str | None]


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
        self._store_states: dict[MemoryStoreProtocol, StoreState] = {}
        self._register_store(primary_store)
        for store in fallback_stores:
            self._register_store(store)

        # Pending operations for reconciliation
        self.pending_operations: list[PendingOperation] = []

    def _register_store(self, store: MemoryStoreProtocol) -> None:
        if store not in self._store_states:
            self._store_states[store] = StoreState()

    def _state_for(self, store: MemoryStoreProtocol) -> StoreState:
        return self._store_states.setdefault(store, StoreState())

    def _resolve_store_name(self, store: MemoryStoreProtocol) -> str:
        return cast(str, getattr(store, "name", store.__class__.__name__))

    def _coerce_record(
        self, store: MemoryStoreProtocol, payload: MemoryItem | MemoryRecord
    ) -> MemoryRecord:
        store_name = self._resolve_store_name(store)
        if isinstance(payload, MemoryRecord):
            if payload.source == store_name:
                return payload
            return MemoryRecord(
                item=payload.item,
                similarity=payload.similarity,
                source=payload.source or store_name,
                metadata=payload.metadata,
            )
        metadata: MemoryMetadata | None = None
        if isinstance(payload.metadata, MutableMapping):
            metadata = cast(MemoryMetadata, dict(payload.metadata))
        elif payload.metadata is not None:
            metadata = cast(MemoryMetadata, payload.metadata)
        return MemoryRecord(
            item=payload,
            source=store_name,
            metadata=metadata,
        )

    def _normalize_search_result(
        self, store: MemoryStoreProtocol, response: MemorySearchResponse
    ) -> MemorySearchResult:
        if isinstance(response, dict):
            if "by_store" in response:
                return cast(GroupedMemoryResults, response)
            query_result = cast(MemoryQueryResults, response)
            records_payload = cast(
                Iterable[MemoryItem | MemoryRecord], query_result.get("records", [])
            )
            normalized_records = [
                self._coerce_record(store, record) for record in records_payload
            ]
            store_name = query_result.get("store")
            result: MemoryQueryResults = {
                "store": (
                    store_name
                    if store_name is not None
                    else self._resolve_store_name(store)
                ),
                "records": normalized_records,
            }
            if "total" in query_result:
                result["total"] = cast(int, query_result["total"])
            if "latency_ms" in query_result:
                result["latency_ms"] = cast(float, query_result["latency_ms"])
            if "metadata" in query_result:
                result["metadata"] = cast(MemoryMetadata, query_result["metadata"])
            return result

        records = [self._coerce_record(store, record) for record in response]
        return {
            "store": self._resolve_store_name(store),
            "records": records,
        }

    @property
    def store_states(self) -> dict[MemoryStoreProtocol, StoreState]:
        return dict(self._store_states)

    @property
    def last_errors(self) -> dict[MemoryStoreProtocol, Exception]:
        return {
            store: state.last_error
            for store, state in self._store_states.items()
            if state.last_error is not None
        }

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
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                item_id = self.primary_store.store(item)

                # If we were in degraded mode, try to reconcile pending operations
                if primary_state.status == StoreStatus.DEGRADED:
                    self.logger.info(
                        "Primary store is available again, reconciling pending operations"
                    )
                    self._reconcile_pending_operations()

                # Update status
                primary_state.mark_available()

                # Store in fallback stores asynchronously (in a real implementation)
                # For now, just store sequentially
                for store in self.fallback_stores:
                    try:
                        store.store(item)
                        self._state_for(store).mark_available()
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to store item in fallback store: {e}"
                        )
                        self._state_for(store).mark_degraded(e)

                return item_id
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    item_id = store.store(item)

                    # Update status
                    store_state.mark_available()

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
                    store_state.mark_degraded(e)
                    errors[str(id(store))] = e

        # All stores failed
        error_message = "All stores failed to store item"
        self.logger.error(error_message)
        raise FallbackError(error_message, errors)

    def retrieve(self, item_id: str) -> MemoryRetrieveResult:
        """
        Retrieve a memory artefact with fallback and normalize to a DTO.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            Typed memory record DTO

        Raises:
            FallbackError: If all stores fail
            KeyError: If the item is not found in any store
        """
        # Try primary store first
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                item = self.primary_store.retrieve(item_id)

                # Update status
                primary_state.mark_available()

                return self._coerce_record(self.primary_store, item)
            except KeyError:
                # Item not found, try fallback stores
                pass
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    item = store.retrieve(item_id)

                    # Update status
                    store_state.mark_available()

                    return self._coerce_record(store, item)
                except KeyError:
                    # Item not found, try next store
                    pass
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    store_state.mark_degraded(e)
                    errors[str(id(store))] = e

        # Item not found in any store
        error_message = f"Item {item_id} not found in any store"
        self.logger.error(error_message)
        raise KeyError(error_message)

    def search(
        self, query: Mapping[str, object] | MemoryMetadata
    ) -> MemorySearchResult:
        """
        Search for memory artefacts with fallback.

        Args:
            query: Search query or metadata filter

        Returns:
            DTO encapsulating matching memory records

        Raises:
            FallbackError: If all stores fail
        """
        # Try primary store first
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                items = self.primary_store.search(query)

                # Update status
                primary_state.mark_available()

                return self._normalize_search_result(self.primary_store, items)
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    items = store.search(query)

                    # Update status
                    store_state.mark_available()

                    return self._normalize_search_result(store, items)
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    store_state.mark_degraded(e)
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
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                primary_success = self.primary_store.delete(item_id)

                # Update status
                primary_state.mark_available()
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        fallback_success = False
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    result = store.delete(item_id)
                    fallback_success = fallback_success or result

                    # Update status
                    store_state.mark_available()
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    store_state.mark_degraded(e)
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
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                items = self.primary_store.get_all_items()

                # Update status
                primary_state.mark_available()

                return items
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    items = store.get_all_items()

                    # Update status
                    store_state.mark_available()

                    return items
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    store_state.mark_degraded(e)
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
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                transaction_id = self.primary_store.begin_transaction()

                # Update status
                primary_state.mark_available()

                # Begin transaction on fallback stores
                for store in self.fallback_stores:
                    try:
                        store.begin_transaction()
                        self._state_for(store).mark_available()
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to begin transaction on fallback store: {e}"
                        )
                        self._state_for(store).mark_degraded(e)

                return transaction_id
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    transaction_id = store.begin_transaction()

                    # Update status
                    store_state.mark_available()

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
                    store_state.mark_degraded(e)
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
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                primary_success = self.primary_store.commit_transaction(transaction_id)

                # Update status
                primary_state.mark_available()
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        fallback_success = False
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    result = store.commit_transaction(transaction_id)
                    fallback_success = fallback_success or result

                    # Update status
                    store_state.mark_available()
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    store_state.mark_degraded(e)
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
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                primary_success = self.primary_store.rollback_transaction(
                    transaction_id
                )

                # Update status
                primary_state.mark_available()
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        fallback_success = False
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    result = store.rollback_transaction(transaction_id)
                    fallback_success = fallback_success or result

                    # Update status
                    store_state.mark_available()
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    store_state.mark_degraded(e)
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
        primary_state = self._state_for(self.primary_store)
        if primary_state.status != StoreStatus.UNAVAILABLE:
            try:
                result = self.primary_store.is_transaction_active(transaction_id)

                # Update status
                primary_state.mark_available()

                return result
            except Exception as e:
                self.logger.warning(f"Primary store failed: {e}")
                primary_state.mark_degraded(e)

        # Try fallback stores
        errors: dict[str, Exception] = {}
        for store in self.fallback_stores:
            store_state = self._state_for(store)
            if store_state.status != StoreStatus.UNAVAILABLE:
                try:
                    result = store.is_transaction_active(transaction_id)

                    # Update status
                    store_state.mark_available()

                    return result
                except Exception as e:
                    self.logger.warning(f"Fallback store failed: {e}")
                    store_state.mark_degraded(e)
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

    def get_store_status(self) -> StoreStatusReport:
        """Return a typed snapshot describing all managed stores."""

        last_errors: dict[str, str | None] = {
            self._resolve_store_name(store): (
                str(state.last_error) if state.last_error is not None else None
            )
            for store, state in self._store_states.items()
        }
        return StoreStatusReport(
            primary=self._state_for(self.primary_store).status,
            fallbacks=[self._state_for(store).status for store in self.fallback_stores],
            last_errors=last_errors,
        )

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
