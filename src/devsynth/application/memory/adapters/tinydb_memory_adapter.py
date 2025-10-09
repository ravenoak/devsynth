"""TinyDB Memory Adapter Module.

This module provides a memory adapter that handles structured data queries
using TinyDB. It also normalizes common Python types (e.g., ``set`` or
``datetime``) into JSON-friendly representations to avoid serialization
errors.
"""

from __future__ import annotations

import importlib
import uuid
from collections.abc import Mapping
from copy import deepcopy
from types import ModuleType
from typing import Any, cast

from ....domain.models.memory import (
    MemoryItem,
    MemoryType,
    MemoryVector,
    SerializedMemoryItem,
)
from ....exceptions import MemoryTransactionError
from ....logging_setup import DevSynthLogger
from ..dto import (
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
    MemorySearchQuery,
    build_memory_record,
    build_query_results,
)
from ..metadata_serialization import (
    record_from_row,
    row_from_record,
)
from ._tinydb_protocols import (
    TinyDBFactory,
    TinyDBLike,
    TinyDBQueryFactory,
    TinyDBQueryLike,
    TinyDBTableLike,
)
from .storage_adapter import MemorySnapshot, StorageAdapter

tinydb_module: ModuleType = importlib.import_module("tinydb")
QueryFactory = cast(TinyDBQueryFactory, getattr(tinydb_module, "Query"))
TinyDBConstructor = cast(TinyDBFactory, getattr(tinydb_module, "TinyDB"))
MemoryStorage = getattr(importlib.import_module("tinydb.storages"), "MemoryStorage")

logger = DevSynthLogger(__name__)


class TinyDBMemoryAdapter(StorageAdapter):
    """
    TinyDB Memory Adapter handles structured data queries using TinyDB.

    It implements the MemoryStore interface and provides additional methods
    for structured data queries.
    """

    backend_type = "tinydb"

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize the TinyDB Memory Adapter.

        Args:
            db_path: Path to the TinyDB database file. If None, an in-memory
                database is used.
        """
        # Use in-memory storage if no path is provided
        if db_path is None:
            self.db: TinyDBLike = TinyDBConstructor(storage=MemoryStorage)
        else:
            self.db = TinyDBConstructor(db_path)

        # Create a table for memory items
        self.items_table: TinyDBTableLike = self.db.table("memory_items")

        self._query_factory: TinyDBQueryFactory = QueryFactory

        logger.info("TinyDB Memory Adapter initialized")

    def _serialize_value(self, value: Any) -> Any:
        """Recursively convert values to JSON-serializable forms.

        TinyDB relies on JSON serialization. We normalize common non-JSON types
        so they can be stored without raising ``TypeError``.

        Normalizations:
        - datetime -> ISO 8601 string
        - set/tuple -> list
        - bytes -> UTF-8 string if decodable, otherwise base64 string
        - Enum -> its value
        - dict/list -> recursively normalized
        - uuid.UUID -> string
        """
        import base64
        import uuid as _uuid
        from datetime import datetime
        from enum import Enum

        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, _uuid.UUID):
            return str(value)
        if isinstance(value, (set, tuple)):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, list):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        if isinstance(value, (bytes, bytearray)):
            try:
                return value.decode("utf-8")
            except Exception:
                return base64.b64encode(bytes(value)).decode("ascii")
        if isinstance(value, Enum):
            return value.value
        return value

    def _memory_item_to_dict(self, item: MemoryItem) -> SerializedMemoryItem:
        """Serialize ``item`` into a TinyDB-compatible mapping."""

        record = build_memory_record(item, source=self.backend_type)
        row = row_from_record(
            record,
            include_similarity=False,
            include_source=False,
        )
        row["content"] = self._serialize_value(row["content"])
        metadata_payload = row.get("metadata")
        if isinstance(metadata_payload, Mapping):
            row["metadata"] = {
                key: self._serialize_value(value)
                for key, value in metadata_payload.items()
            }
        return cast(SerializedMemoryItem, row)

    def _dict_to_memory_item(self, item_dict: Mapping[str, object]) -> MemoryItem:
        """Reconstruct a :class:`MemoryItem` from a TinyDB row."""

        record = record_from_row(item_dict, default_source=self.backend_type)
        return record.item

    def store(self, item: MemoryItem, transaction_id: str | None = None) -> str:
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
            item.id = str(uuid.uuid4())

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
            query = self._query_factory()
            condition = cast(TinyDBQueryLike, query.id == item.id)
            existing = self.items_table.get(condition)
            if existing:
                # Update the existing item
                self.items_table.update(item_dict, condition)
            else:
                # Insert a new item
                self.items_table.insert(item_dict)

            logger.info(
                "Stored memory item with ID %s in TinyDB Memory Adapter "
                "(transaction: %s)",
                item.id,
                transaction_id,
            )
        else:
            # Not part of a transaction, store normally
            # Check if the item already exists
            query = self._query_factory()
            condition = cast(TinyDBQueryLike, query.id == item.id)
            existing = self.items_table.get(condition)
            if existing:
                # Update the existing item
                self.items_table.update(item_dict, condition)
            else:
                # Insert a new item
                self.items_table.insert(item_dict)

            logger.info(
                "Stored memory item with ID %s in TinyDB Memory Adapter",
                item.id,
            )

        return str(item.id)

    def retrieve(self, item_id: str) -> MemoryItem | None:
        """
        Retrieve a memory item from TinyDB.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        query = self._query_factory()
        condition = cast(TinyDBQueryLike, cast(Any, query.id) == item_id)
        item_dict = self.items_table.get(condition)
        if item_dict:
            typed_row = cast(Mapping[str, object], dict(item_dict))
            return self._dict_to_memory_item(typed_row)
        return None

    def search(self, query: MemorySearchQuery | MemoryMetadata) -> list[MemoryRecord]:
        """
        Search for memory items in TinyDB matching the query.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        # Build TinyDB query
        tinydb_query = self._query_factory()
        query_conditions = None

        for key, value in query.items():
            if key == "type":
                # Handle memory_type specially
                memory_type = MemoryType.from_raw(value)
                condition = cast(
                    TinyDBQueryLike,
                    cast(Any, tinydb_query.memory_type) == memory_type.value,
                )
            elif key.startswith("metadata."):
                # Handle nested metadata fields
                metadata_key = key.split(".", 1)[1]
                condition = cast(
                    TinyDBQueryLike,
                    cast(Any, tinydb_query.metadata[metadata_key]) == value,
                )
            elif key in ["id", "content", "created_at"]:
                # Handle direct fields
                condition = cast(
                    TinyDBQueryLike,
                    cast(Any, getattr(tinydb_query, key)) == value,
                )
            else:
                # Assume it's a metadata field
                condition = cast(
                    TinyDBQueryLike,
                    cast(Any, tinydb_query.metadata[key]) == value,
                )

            # Combine conditions with AND
            if query_conditions is None:
                query_conditions = condition
            else:
                query_conditions &= condition

        # If no conditions, return all items
        raw_results = (
            self.items_table.all()
            if query_conditions is None
            else self.items_table.search(query_conditions)
        )

        return [
            record_from_row(
                cast(Mapping[str, object], dict(item_dict)),
                default_source=self.backend_type,
            )
            for item_dict in raw_results
        ]

    def delete(self, item_id: str, transaction_id: str | None = None) -> bool:
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
            query = self._query_factory()
            condition = cast(TinyDBQueryLike, cast(Any, query.id) == item_id)
            removed = self.items_table.remove(condition)
            if removed:
                logger.info(
                    "Deleted memory item with ID %s from TinyDB Memory Adapter "
                    "(transaction: %s)",
                    item_id,
                    transaction_id,
                )
                return True
            return False
        else:
            # Not part of a transaction, delete normally
            query = self._query_factory()
            condition = cast(TinyDBQueryLike, cast(Any, query.id) == item_id)
            removed = self.items_table.remove(condition)
            if removed:
                logger.info(
                    "Deleted memory item with ID %s from TinyDB Memory Adapter",
                    item_id,
                )
                return True
            return False

    def query_structured_data(self, query: MemorySearchQuery) -> MemoryQueryResults:
        """
        Query structured data in TinyDB.

        This method provides a more flexible way to query TinyDB than the
        standard search method. It supports complex queries with nested
        fields and operators.

        Args:
            query: The query dictionary

        Returns:
            Normalized query results for the TinyDB backend
        """
        # For now, this is just a wrapper around search
        # In a real implementation, this could support more complex queries
        records = self.search(query)
        return build_query_results(self.backend_type, records)

    def retrieve_with_edrr_phase(
        self,
        item_type: MemoryType,
        edrr_phase: str,
        metadata: MemoryMetadata | None = None,
    ) -> Any:
        """
        Retrieve an item stored with a specific EDRR phase.

        Args:
            item_type: Identifier of the stored item as a :class:`MemoryType`.
            edrr_phase: The phase tag used during storage.
            metadata: Optional additional metadata for adapter queries.

        Returns:
            The retrieved item or an empty dictionary if not found.
        """
        search_meta = dict(metadata) if metadata else {}
        search_meta["edrr_phase"] = edrr_phase

        # Build TinyDB query
        tinydb_query = self._query_factory()
        query_conditions = cast(
            TinyDBQueryLike, tinydb_query.memory_type == item_type.value
        )

        for key, value in search_meta.items():
            condition = cast(TinyDBQueryLike, tinydb_query.metadata[key] == value)
            query_conditions &= condition

        results = self.items_table.search(query_conditions)

        if results:
            # Return the content of the first matching item
            item_dict = cast(Mapping[str, object], dict(results[0]))
            memory_item = self._dict_to_memory_item(item_dict)
            return memory_item.content

        return {}

    def close(self) -> None:
        """Close the TinyDB database."""
        self.db.close()

    def get_all(self) -> list[MemoryItem]:
        """
        Get all memory items from TinyDB.

        Returns:
            A list of all memory items
        """
        results = self.items_table.all()
        return [self._dict_to_memory_item(item_dict) for item_dict in results]

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a transaction.

        Args:
            transaction_id: Optional transaction identifier. If ``None`` a new
                identifier is generated. Providing an explicit identifier allows
                external coordination across adapters.

        Returns:
            The active transaction identifier.

        Raises:
            MemoryTransactionError: If a transaction is already active.
        """
        if hasattr(self, "_transaction_id"):
            raise MemoryTransactionError(
                "Transaction already active",
                transaction_id=getattr(self, "_transaction_id"),
                store_type="TinyDBMemoryAdapter",
                operation="begin_transaction",
            )

        if transaction_id is None:
            transaction_id = str(uuid.uuid4())

        logger.debug(f"Beginning transaction {transaction_id} in TinyDBMemoryAdapter")

        # Store the transaction ID and create a snapshot of the current state
        self._transaction_id = transaction_id
        self._transaction_snapshot: MemorySnapshot = {
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

    def commit_transaction(self, transaction_id: str | None = None) -> bool:
        """
        Commit a transaction.

        Args:
            transaction_id: Optional transaction identifier. If ``None`` the
                currently active transaction is committed.

        Returns:
            True if the transaction was committed.

        Raises:
            MemoryTransactionError: If no transaction is active or the provided
                identifier does not match the active transaction.
        """
        if transaction_id is None:
            transaction_id = getattr(self, "_transaction_id", None)
        if (
            not transaction_id
            or not hasattr(self, "_transaction_id")
            or self._transaction_id != transaction_id
        ):
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="TinyDBMemoryAdapter",
                operation="commit_transaction",
            )

        logger.debug(f"Committing transaction {transaction_id} in TinyDBMemoryAdapter")

        # TinyDB doesn't have native transaction support, so we just clear the snapshot
        if hasattr(self, "_transaction_snapshot"):
            delattr(self, "_transaction_snapshot")

        # Clear the transaction ID
        delattr(self, "_transaction_id")

        return True

    def rollback_transaction(self, transaction_id: str | None = None) -> bool:
        """
        Rollback a transaction.

        Args:
            transaction_id: Optional transaction identifier. If ``None`` the
                currently active transaction is rolled back.

        Returns:
            True if the transaction was rolled back.

        Raises:
            MemoryTransactionError: If no transaction is active or the
                identifier does not match the active transaction.
        """
        if transaction_id is None:
            transaction_id = getattr(self, "_transaction_id", None)
        if (
            not transaction_id
            or not hasattr(self, "_transaction_id")
            or self._transaction_id != transaction_id
        ):
            raise MemoryTransactionError(
                f"Transaction {transaction_id} is not active",
                transaction_id=transaction_id,
                store_type="TinyDBMemoryAdapter",
                operation="rollback_transaction",
            )

        logger.debug(
            f"Rolling back transaction {transaction_id} in TinyDBMemoryAdapter"
        )

        # Restore from snapshot if available
        if hasattr(self, "_transaction_snapshot"):
            # Clear the table
            self.items_table.truncate()

            # Restore items from snapshot
            for item in self._transaction_snapshot.values():
                if isinstance(item, MemoryItem):
                    self.store(deepcopy(item))

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

    def snapshot(self) -> dict[str, MemoryItem]:
        """
        Create a snapshot of the current state.

        Returns:
            A dictionary mapping item IDs to memory items
        """
        return {item.id: deepcopy(item) for item in self.get_all()}

    def restore(
        self, snapshot: Mapping[str, MemoryItem] | Mapping[str, MemoryVector]
    ) -> bool:
        """
        Restore from a snapshot.

        Args:
            snapshot: A dictionary mapping item IDs to memory items

        Returns:
            True if the restore was successful
        """
        # Clear the table
        self.items_table.truncate()

        # Restore items from snapshot
        restored = False
        for item in snapshot.values():
            if isinstance(item, MemoryItem):
                self.store(deepcopy(item))
                restored = True

        return restored
