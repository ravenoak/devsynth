"""
Transaction Context Module

This module provides a transaction context for memory operations across multiple adapters.
It implements a two-phase commit protocol for cross-store transactions.
"""

import uuid
from typing import Dict, List, Any, Optional, Set
from contextlib import contextmanager

from ...logging_setup import DevSynthLogger
from ...domain.models.memory import MemoryItem
from ...exceptions import MemoryTransactionError

logger = DevSynthLogger(__name__)


class TransactionContext:
    """
    Transaction context for memory operations across multiple adapters.

    This class implements a two-phase commit protocol for cross-store transactions.
    It handles adapters with and without native transaction support.
    """

    def __init__(self, adapters: List[Any]):
        """
        Initialize the transaction context.

        Args:
            adapters: List of memory adapters to include in the transaction
        """
        self.adapters = adapters
        self.transaction_id = str(uuid.uuid4())
        self.snapshots = {}
        self.operations = []
        self.prepared_adapters = []

    def __enter__(self):
        """
        Begin the transaction on all adapters.

        For adapters with native transaction support, call begin_transaction.
        For adapters without native transaction support, take a snapshot of the current state.

        Returns:
            self: The transaction context

        Raises:
            MemoryTransactionError: If the transaction cannot be started
        """
        logger.debug(
            f"Starting transaction {self.transaction_id} for {len(self.adapters)} adapters"
        )

        try:
            for adapter in self.adapters:
                if hasattr(adapter, "begin_transaction"):
                    adapter.begin_transaction(self.transaction_id)
                else:
                    # For adapters without native transaction support,
                    # take a snapshot of the current state
                    if hasattr(adapter, "get_all"):
                        items = adapter.get_all()
                        self.snapshots[id(adapter)] = {
                            item.id: self._copy_item(item) for item in items
                        }
                    else:
                        logger.warning(
                            f"Adapter {adapter.__class__.__name__} does not support get_all, "
                            f"cannot create snapshot"
                        )
                        self.snapshots[id(adapter)] = {}

                    logger.debug(
                        f"Created snapshot for {adapter.__class__.__name__} with "
                        f"{len(self.snapshots[id(adapter)])} items"
                    )
        except Exception as e:
            # If begin_transaction fails, rollback any adapters that were already started
            self._rollback()
            raise MemoryTransactionError(f"Failed to start transaction: {e}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        End the transaction on all adapters.

        If no exception occurred, commit the transaction.
        If an exception occurred, rollback the transaction.

        Args:
            exc_type: Exception type, if an exception occurred
            exc_val: Exception value, if an exception occurred
            exc_tb: Exception traceback, if an exception occurred

        Returns:
            bool: True if the exception was handled, False otherwise
        """
        if exc_type is None:
            # No exception occurred, commit the transaction
            try:
                self._commit()
                return True
            except Exception as e:
                logger.error(f"Failed to commit transaction {self.transaction_id}: {e}")
                self._rollback()
                raise MemoryTransactionError(f"Failed to commit transaction: {e}")
        else:
            # Exception occurred, rollback the transaction
            logger.error(f"Transaction {self.transaction_id} failed: {exc_val}")
            self._rollback()
            return False

    def _commit(self):
        """
        Commit the transaction using a two-phase commit protocol.

        Phase 1: Prepare all adapters for commit
        Phase 2: Commit all adapters

        If any adapter fails to prepare, rollback all adapters.

        Raises:
            MemoryTransactionError: If the transaction cannot be committed
        """
        logger.debug(f"Committing transaction {self.transaction_id}")

        # Phase 1: Flush and prepare
        try:
            for adapter in self.adapters:
                self._flush_adapter(adapter)
                if hasattr(adapter, "prepare_commit"):
                    adapter.prepare_commit(self.transaction_id)
                    self.prepared_adapters.append(adapter)
        except Exception as e:
            # If prepare fails, rollback all adapters
            logger.error(f"Failed to prepare transaction {self.transaction_id}: {e}")
            self._rollback()
            raise MemoryTransactionError(f"Failed to prepare transaction: {e}")

        # Phase 2: Flush and commit
        commit_errors = []
        for adapter in self.adapters:
            try:
                self._flush_adapter(adapter)
                if hasattr(adapter, "commit_transaction"):
                    adapter.commit_transaction(self.transaction_id)
            except Exception as e:
                error_msg = (
                    f"Failed to commit transaction {self.transaction_id} on "
                    f"{adapter.__class__.__name__}: {e}"
                )
                logger.error(error_msg)
                commit_errors.append(error_msg)

        if commit_errors:
            # If any commit fails, log the errors but don't rollback
            # (we're in an inconsistent state, but rolling back might make it worse)
            logger.error(
                f"Transaction {self.transaction_id} partially committed with errors: {commit_errors}"
            )
            raise MemoryTransactionError(
                f"Transaction partially committed with errors: {commit_errors}"
            )

        logger.debug(f"Transaction {self.transaction_id} committed successfully")

    def _flush_adapter(self, adapter: Any) -> None:
        """Flush pending writes for an adapter if supported."""

        for method_name in (
            "flush_updates",
            "flush_pending_writes",
            "flush_queue",
            "flush",
        ):
            method = getattr(adapter, method_name, None)
            if callable(method):
                logger.debug(
                    f"Flushing pending writes for {adapter.__class__.__name__} using {method_name}"
                )
                method()
                break

    def _rollback(self):
        """
        Rollback the transaction on all adapters.

        For adapters with native transaction support, call rollback_transaction.
        For adapters without native transaction support, restore from snapshot.
        """
        logger.debug(f"Rolling back transaction {self.transaction_id}")

        rollback_errors = []

        # Rollback adapters with native transaction support
        for adapter in self.adapters:
            try:
                if hasattr(adapter, "rollback_transaction"):
                    adapter.rollback_transaction(self.transaction_id)
            except Exception as e:
                error_msg = f"Failed to rollback transaction {self.transaction_id} on {adapter.__class__.__name__}: {e}"
                logger.error(error_msg)
                rollback_errors.append(error_msg)

        # Restore snapshots for adapters without native transaction support
        for adapter in self.adapters:
            if not hasattr(adapter, "rollback_transaction"):
                adapter_id = id(adapter)
                if adapter_id in self.snapshots:
                    try:
                        # Delete all items
                        if hasattr(adapter, "get_all") and hasattr(adapter, "delete"):
                            current_items = adapter.get_all()
                            for item in current_items:
                                adapter.delete(item.id)

                        # Restore items from snapshot
                        if hasattr(adapter, "store"):
                            for item in self.snapshots[adapter_id].values():
                                adapter.store(item)
                    except Exception as e:
                        error_msg = f"Failed to restore snapshot for {adapter.__class__.__name__}: {e}"
                        logger.error(error_msg)
                        rollback_errors.append(error_msg)

        if rollback_errors:
            logger.error(
                f"Transaction {self.transaction_id} rollback completed with errors: {rollback_errors}"
            )
        else:
            logger.debug(f"Transaction {self.transaction_id} rolled back successfully")

    def _copy_item(self, item: MemoryItem) -> MemoryItem:
        """
        Create a deep copy of a memory item.

        Args:
            item: Memory item to copy

        Returns:
            MemoryItem: Deep copy of the memory item
        """
        from copy import deepcopy

        return deepcopy(item)
