"""
TinyDB Memory Adapter Module

This module provides a memory adapter that handles structured data queries
using TinyDB.
"""

import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional

from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage

from ....domain.models.memory import MemoryItem, MemoryType
from ....exceptions import MemoryTransactionError
from ....logging_setup import DevSynthLogger
from .storage_adapter import StorageAdapter

logger = DevSynthLogger(__name__)


class TinyDBMemoryAdapter(StorageAdapter):
    """
    TinyDB Memory Adapter handles structured data queries using TinyDB.

    It implements the MemoryStore interface and provides additional methods
    for structured data queries.
    """

    backend_type = "tinydb"

    def __init__(self, db_path: str = None):
        """
        Initialize the TinyDB Memory Adapter.

        Args:
            db_path: Path to the TinyDB database file. If None, an in-memory database is used.
        """
        # Use in-memory storage if no path is provided
        if db_path is None:
            self.db = TinyDB(storage=MemoryStorage)
        else:
            self.db = TinyDB(db_path)

        # Create a table for memory items
        self.items_table = self.db.table("memory_items")

        logger.info("TinyDB Memory Adapter initialized")

    def _memory_item_to_dict(self, item: MemoryItem) -> Dict[str, Any]:
        """
        Convert a MemoryItem to a dictionary for storage in TinyDB.

        Args:
            item: The memory item to convert

        Returns:
            A dictionary representation of the memory item
        """
        # Handle both enum and string types for memory_type
        memory_type_value = item.memory_type
        if hasattr(item.memory_type, "value"):
            memory_type_value = item.memory_type.value

        return {
            "id": item.id,
            "content": item.content,
            "memory_type": memory_type_value,
            "metadata": item.metadata,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }

    def _dict_to_memory_item(self, item_dict: Dict[str, Any]) -> MemoryItem:
        """
        Convert a dictionary from TinyDB to a MemoryItem.

        Args:
            item_dict: The dictionary to convert

        Returns:
            A MemoryItem
        """
        from datetime import datetime

        return MemoryItem(
            id=item_dict["id"],
            content=item_dict["content"],
            memory_type=MemoryType(item_dict["memory_type"]),
            metadata=item_dict["metadata"],
            created_at=(
                datetime.fromisoformat(item_dict["created_at"])
                if item_dict["created_at"]
                else None
            ),
        )

    def store(self, item: MemoryItem, transaction_id: str = None) -> str:
        """
        Store a memory item in TinyDB.

        Args:
            item: The memory item to store
            transaction_id: Optional transaction ID to use for this operation

        Returns:
            The ID of the stored memory item
        """
        # Generate an ID if not provided
        if not item.id:
            item.id = f"tinydb_{len(self.items_table) + 1}"

        # Convert to dictionary
        item_dict = self._memory_item_to_dict(item)

        # Check if this operation is part of a transaction
        if transaction_id:
            # Check if this is the active transaction
            if (
                not hasattr(self, "_transaction_id")
                or self._transaction_id != transaction_id
            ):
                raise MemoryTransactionError(
                    f"Transaction {transaction_id} is not active",
                    transaction_id=transaction_id,
                    store_type="TinyDBMemoryAdapter",
                    operation="store",
                )

            # Store the item in memory but don't commit to disk yet
            # Check if the item already exists
            existing = self.items_table.get(Query().id == item.id)
            if existing:
                # Update the existing item
                self.items_table.update(item_dict, Query().id == item.id)
            else:
                # Insert a new item
                self.items_table.insert(item_dict)

            logger.info(
                f"Stored memory item with ID {item.id} in TinyDB Memory Adapter (transaction: {transaction_id})"
            )
        else:
            # Not part of a transaction, store normally
            # Check if the item already exists
            existing = self.items_table.get(Query().id == item.id)
            if existing:
                # Update the existing item
                self.items_table.update(item_dict, Query().id == item.id)
            else:
                # Insert a new item
                self.items_table.insert(item_dict)

            logger.info(
                f"Stored memory item with ID {item.id} in TinyDB Memory Adapter"
            )

        return item.id

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from TinyDB.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        item_dict = self.items_table.get(Query().id == item_id)
        if item_dict:
            return self._dict_to_memory_item(item_dict)
        return None

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Search for memory items in TinyDB matching the query.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        # Build TinyDB query
        tinydb_query = Query()
        query_conditions = None

        for key, value in query.items():
            if key == "type":
                # Handle memory_type specially
                condition = tinydb_query.memory_type == value.value
            elif key.startswith("metadata."):
                # Handle nested metadata fields
                metadata_key = key.split(".", 1)[1]
                condition = tinydb_query.metadata[metadata_key] == value
            elif key in ["id", "content", "created_at"]:
                # Handle direct fields
                condition = getattr(tinydb_query, key) == value
            else:
                # Assume it's a metadata field
                condition = tinydb_query.metadata[key] == value

            # Combine conditions with AND
            if query_conditions is None:
                query_conditions = condition
            else:
                query_conditions &= condition

        # If no conditions, return all items
        if query_conditions is None:
            results = self.items_table.all()
        else:
            results = self.items_table.search(query_conditions)

        # Convert to MemoryItem objects
        return [self._dict_to_memory_item(item_dict) for item_dict in results]

    def delete(self, item_id: str, transaction_id: str = None) -> bool:
        """
        Delete a memory item from TinyDB.

        Args:
            item_id: The ID of the memory item to delete
            transaction_id: Optional transaction ID to use for this operation

        Returns:
            True if the item was deleted, False otherwise

        Raises:
            MemoryTransactionError: If the transaction is not active
        """
        # Check if this operation is part of a transaction
        if transaction_id:
            # Check if this is the active transaction
            if (
                not hasattr(self, "_transaction_id")
                or self._transaction_id != transaction_id
            ):
                raise MemoryTransactionError(
                    f"Transaction {transaction_id} is not active",
                    transaction_id=transaction_id,
                    store_type="TinyDBMemoryAdapter",
                    operation="delete",
                )

            # Delete the item in memory but don't commit to disk yet
            removed = self.items_table.remove(Query().id == item_id)
            if removed:
                logger.info(
                    f"Deleted memory item with ID {item_id} from TinyDB Memory Adapter (transaction: {transaction_id})"
                )
                return True
            return False
        else:
            # Not part of a transaction, delete normally
            removed = self.items_table.remove(Query().id == item_id)
            if removed:
                logger.info(
                    f"Deleted memory item with ID {item_id} from TinyDB Memory Adapter"
                )
                return True
            return False

    def query_structured_data(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Query structured data in TinyDB.

        This method provides a more flexible way to query TinyDB than the standard search method.
        It supports complex queries with nested fields and operators.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        # For now, this is just a wrapper around search
        # In a real implementation, this could support more complex queries
        return self.search(query)

    def retrieve_with_edrr_phase(
        self,
        item_type: str,
        edrr_phase: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Any:
        """
        Retrieve an item stored with a specific EDRR phase.

        Args:
            item_type: Identifier of the stored item.
            edrr_phase: The phase tag used during storage.
            metadata: Optional additional metadata for adapter queries.

        Returns:
            The retrieved item or an empty dictionary if not found.
        """
        search_meta = metadata.copy() if metadata else {}
        search_meta["edrr_phase"] = edrr_phase

        # Build TinyDB query
        tinydb_query = Query()
        query_conditions = tinydb_query.memory_type == item_type

        for key, value in search_meta.items():
            condition = tinydb_query.metadata[key] == value
            query_conditions &= condition

        results = self.items_table.search(query_conditions)

        if results:
            # Return the content of the first matching item
            item_dict = results[0]
            memory_item = self._dict_to_memory_item(item_dict)
            return memory_item.content

        return {}

    def close(self):
        """Close the TinyDB database."""
        self.db.close()

    def get_all(self) -> List[MemoryItem]:
        """
        Get all memory items from TinyDB.

        Returns:
            A list of all memory items
        """
        results = self.items_table.all()
        return [self._dict_to_memory_item(item_dict) for item_dict in results]

    def begin_transaction(self, transaction_id: str) -> str:
        """
        Begin a transaction.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            The transaction ID

        Raises:
            MemoryTransactionError: If the transaction cannot be started
        """
        logger.debug(f"Beginning transaction {transaction_id} in TinyDBMemoryAdapter")

        # Store the transaction ID and create a snapshot of the current state
        self._transaction_id = transaction_id
        self._transaction_snapshot = {
            item.id: deepcopy(item) for item in self.get_all()
        }

        return transaction_id

    def prepare_commit(self, transaction_id: str) -> bool:
        """
        Prepare to commit a transaction.

        This is the first phase of a two-phase commit protocol.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            True if the transaction is prepared for commit

        Raises:
            MemoryTransactionError: If the transaction cannot be prepared
        """
        logger.debug(
            f"Preparing to commit transaction {transaction_id} in TinyDBMemoryAdapter"
        )

        # Check if this is the active transaction
        if (
            not hasattr(self, "_transaction_id")
            or self._transaction_id != transaction_id
        ):
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="TinyDBMemoryAdapter",
                operation="prepare_commit",
            )

        # TinyDB doesn't have a native prepare phase, so we just return True
        return True

    def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            True if the transaction was committed

        Raises:
            MemoryTransactionError: If the transaction cannot be committed
        """
        logger.debug(f"Committing transaction {transaction_id} in TinyDBMemoryAdapter")

        # Check if this is the active transaction
        if (
            not hasattr(self, "_transaction_id")
            or self._transaction_id != transaction_id
        ):
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="TinyDBMemoryAdapter",
                operation="commit_transaction",
            )

        # TinyDB doesn't have native transaction support, so we just clear the snapshot
        if hasattr(self, "_transaction_snapshot"):
            delattr(self, "_transaction_snapshot")

        # Clear the transaction ID
        delattr(self, "_transaction_id")

        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            True if the transaction was rolled back

        Raises:
            MemoryTransactionError: If the transaction cannot be rolled back
        """
        logger.debug(
            f"Rolling back transaction {transaction_id} in TinyDBMemoryAdapter"
        )

        # Check if this is the active transaction
        if (
            not hasattr(self, "_transaction_id")
            or self._transaction_id != transaction_id
        ):
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="TinyDBMemoryAdapter",
                operation="rollback_transaction",
            )

        # Restore from snapshot if available
        if hasattr(self, "_transaction_snapshot"):
            # Clear the table
            self.items_table.truncate()

            # Restore items from snapshot
            for item in self._transaction_snapshot.values():
                self.store(item)

            # Clear the snapshot
            delattr(self, "_transaction_snapshot")

        # Clear the transaction ID
        delattr(self, "_transaction_id")

        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return True if the given transaction ID is currently active."""

        return (
            hasattr(self, "_transaction_id") and self._transaction_id == transaction_id
        )

    def snapshot(self) -> Dict[str, MemoryItem]:
        """
        Create a snapshot of the current state.

        Returns:
            A dictionary mapping item IDs to memory items
        """
        return {item.id: deepcopy(item) for item in self.get_all()}

    def restore(self, snapshot: Dict[str, MemoryItem]) -> bool:
        """
        Restore from a snapshot.

        Args:
            snapshot: A dictionary mapping item IDs to memory items

        Returns:
            True if the restore was successful
        """
        if snapshot is None:
            return False

        # Clear the table
        self.items_table.truncate()

        # Restore items from snapshot
        for item in snapshot.values():
            self.store(item)

        return True
