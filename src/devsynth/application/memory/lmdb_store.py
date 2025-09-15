"""
LMDB implementation of MemoryStore.

This implementation uses LMDB (Lightning Memory-Mapped Database) to store
and retrieve memory items with transaction support.
"""

import json
import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, ContextManager

import tiktoken

try:  # pragma: no cover - optional dependency
    import lmdb  # type: ignore[import]
except Exception:  # pragma: no cover - graceful fallback
    lmdb = None  # type: ignore[assignment]

from devsynth.exceptions import MemoryStoreError
from devsynth.logging_setup import DevSynthLogger
from devsynth.security.audit import audit_event
from devsynth.security.encryption import decrypt_bytes, encrypt_bytes

from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType

# Create a logger for this module
logger = DevSynthLogger(__name__)


class LMDBStore(MemoryStore):
    """
    LMDB implementation of the MemoryStore interface.

    This class uses LMDB (Lightning Memory-Mapped Database) to store
    and retrieve memory items with transaction support.
    """

    def __init__(
        self,
        base_path: str,
        map_size: int = 10485760,
        *,
        encryption_enabled: bool = False,
        encryption_key: str | None = None,
    ):
        """
        Initialize a LMDBStore.

        Args:
            base_path: Base path for storing the LMDB database
            map_size: Maximum size database may grow to (default: 10MB)
        """
        if lmdb is None:
            raise ImportError(
                "LMDBStore requires the 'lmdb' package. Install it with "
                "'pip install lmdb' or use the dev extras."
            )

        self.base_path = base_path
        self.db_path = os.path.join(self.base_path, "memory.lmdb")
        self.token_count = 0
        self.map_size = map_size
        self.encryption_enabled = encryption_enabled
        self.encryption_key = encryption_key

        # Ensure the directory exists
        os.makedirs(self.base_path, exist_ok=True)

        # Initialize LMDB environment
        self.env = lmdb.open(
            self.db_path,
            map_size=self.map_size,  # 10MB by default
            metasync=True,
            sync=True,
            max_dbs=2,  # Main DB and metadata DB
        )

        # Open databases
        self.items_db = self.env.open_db(b"items")
        self.metadata_db = self.env.open_db(b"metadata")

        # Initialize the tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
        except Exception as exc:
            logger.warning(
                "Failed to initialize tokenizer: %s. "
                "Token counting will be approximate.",
                exc,
            )
            self.tokenizer = None

        # Track explicit transactions so SyncManager can manage commit and
        # rollback even when the context manager form isn't used. Each entry
        # maps a transaction identifier to the underlying LMDB transaction
        # object.
        self._transactions: dict[str, lmdb.Transaction] = {}

    def close(self):
        """Close the LMDB environment."""
        if hasattr(self, "env") and self.env:
            self.env.close()
            self.env = None
            logger.info("LMDB environment closed")

    def __del__(self):
        """Ensure the environment is closed when the object is deleted."""
        self.close()

    @contextmanager
    def begin_transaction(
        self, write: bool = True, transaction_id: str | None = None
    ) -> ContextManager:
        """Begin a transaction and optionally register it by ``transaction_id``."""

        txn = self.env.begin(write=write)
        if transaction_id:
            self._transactions[transaction_id] = txn
        try:
            yield txn
            txn.commit()
        except Exception:
            txn.abort()
            raise
        finally:
            if transaction_id:
                self._transactions.pop(transaction_id, None)

    def commit_transaction(self, transaction_id: str) -> None:
        """Commit a previously started explicit transaction."""

        txn = self._transactions.pop(transaction_id, None)
        if txn is None:
            logger.warning(f"No transaction {transaction_id} to commit")
            return
        try:
            txn.commit()
        except Exception as exc:
            logger.error(f"LMDB commit failed for {transaction_id}: {exc}")
            raise

    def rollback_transaction(self, transaction_id: str) -> None:
        """Abort a previously started explicit transaction."""

        txn = self._transactions.pop(transaction_id, None)
        if txn is None:
            logger.warning(f"No transaction {transaction_id} to roll back")
            return
        try:
            txn.abort()
        except Exception as exc:
            logger.error(f"LMDB rollback failed for {transaction_id}: {exc}")
            raise

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if an explicit transaction is still active."""

        return transaction_id in self._transactions

    def _count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text
        """
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        else:
            # Approximate token count (roughly 4 characters per token)
            return len(text) // 4

    def _encrypt(self, data: bytes) -> bytes:
        if not self.encryption_enabled:
            return data
        return encrypt_bytes(data, key=self.encryption_key)

    def _decrypt(self, data: bytes) -> bytes:
        if not self.encryption_enabled:
            return data
        return decrypt_bytes(data, key=self.encryption_key)

    def _serialize_memory_item(self, item: MemoryItem) -> bytes:
        """
        Serialize a MemoryItem to bytes for storage in LMDB.

        Args:
            item: The MemoryItem to serialize

        Returns:
            A bytes representation of the MemoryItem
        """
        # Convert memory_type enum to string
        memory_type_str = item.memory_type.value if item.memory_type else None

        # Convert created_at to ISO format string
        created_at_str = item.created_at.isoformat() if item.created_at else None

        # Create a serialized representation
        serialized = {
            "id": item.id,
            "content": item.content,
            "memory_type": memory_type_str,
            "metadata": item.metadata,
            "created_at": created_at_str,
        }

        # Convert to JSON and then to bytes
        return json.dumps(serialized).encode("utf-8")

    def _deserialize_memory_item(self, data: bytes) -> MemoryItem:
        """
        Deserialize bytes to a MemoryItem.

        Args:
            data: The bytes to deserialize

        Returns:
            A MemoryItem object
        """
        # Convert bytes to JSON
        serialized = json.loads(data.decode("utf-8"))

        # Convert memory_type string to enum
        memory_type = (
            MemoryType(serialized["memory_type"]) if serialized["memory_type"] else None
        )

        # Convert created_at string to datetime
        created_at = (
            datetime.fromisoformat(serialized["created_at"])
            if serialized["created_at"]
            else None
        )

        # Create a MemoryItem
        item = MemoryItem(
            id=serialized["id"],
            content=serialized["content"],
            memory_type=memory_type,
            metadata=serialized["metadata"],
            created_at=created_at,
        )

        return item

    def store_in_transaction(self, txn, item: MemoryItem) -> str:
        """
        Store an item in memory within a transaction and return its ID.

        Args:
            txn: The LMDB transaction
            item: The MemoryItem to store

        Returns:
            The ID of the stored item
        """
        # Generate an ID if not provided
        if not item.id:
            item.id = str(uuid.uuid4())

        # Serialize and optionally encrypt the item
        serialized = self._serialize_memory_item(item)
        serialized = self._encrypt(serialized)

        # Store in LMDB
        txn.put(item.id.encode("utf-8"), serialized, db=self.items_db)

        # Store metadata for searching
        if item.metadata:
            for key, value in item.metadata.items():
                # Create a composite key for metadata: key:value:id
                metadata_key = f"metadata:{key}:{value}:{item.id}".encode()
                txn.put(metadata_key, b"1", db=self.metadata_db)

        # Store memory_type for searching
        if item.memory_type:
            memory_type_key = f"memory_type:{item.memory_type.value}:{item.id}".encode()
            txn.put(memory_type_key, b"1", db=self.metadata_db)

        # Store content for searching
        if item.content:
            content_key = f"content:{item.id}".encode()
            content_bytes = item.content.encode("utf-8")
            if self.encryption_enabled:
                content_bytes = self._encrypt(content_bytes)
            txn.put(content_key, content_bytes, db=self.metadata_db)

        return item.id

    def store(self, item: MemoryItem) -> str:
        """
        Store an item in memory and return its ID.

        Args:
            item: The MemoryItem to store

        Returns:
            The ID of the stored item

        Raises:
            MemoryStoreError: If the item cannot be stored
        """
        try:
            with self.begin_transaction() as txn:
                item_id = self.store_in_transaction(txn, item)

            # Update token count
            token_count = self._count_tokens(str(item))
            self.token_count += token_count

            audit_event(
                "store_memory",
                store="LMDBStore",
                item_id=item_id,
            )

            logger.info(f"Stored item with ID {item_id} in LMDB")
            return item_id

        except Exception as e:
            logger.error(f"Failed to store item in LMDB: {e}")
            raise MemoryStoreError(f"Failed to store item: {e}")

    def retrieve_in_transaction(self, txn, item_id: str) -> MemoryItem | None:
        """
        Retrieve an item from memory within a transaction by ID.

        Args:
            txn: The LMDB transaction
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved MemoryItem, or None if not found
        """
        # Get the item from LMDB
        data = txn.get(item_id.encode("utf-8"), db=self.items_db)

        # Check if the item was found
        if not data:
            return None

        # Decrypt and deserialize the item
        data = self._decrypt(data)
        item = self._deserialize_memory_item(data)

        return item

    def retrieve(self, item_id: str) -> MemoryItem | None:
        """
        Retrieve an item from memory by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved MemoryItem, or None if not found

        Raises:
            MemoryStoreError: If there is an error retrieving the item
        """
        try:
            with self.begin_transaction(write=False) as txn:
                item = self.retrieve_in_transaction(txn, item_id)

            if not item:
                logger.warning(f"Item with ID {item_id} not found in LMDB")
                audit_event(
                    "retrieve_memory",
                    store="LMDBStore",
                    item_id=item_id,
                    found=False,
                )
                return None

            # Update token count
            token_count = self._count_tokens(str(item))
            self.token_count += token_count

            audit_event(
                "retrieve_memory",
                store="LMDBStore",
                item_id=item_id,
                found=True,
            )

            logger.info(f"Retrieved item with ID {item_id} from LMDB")
            return item

        except Exception as e:
            logger.error(f"Error retrieving item from LMDB: {e}")
            raise MemoryStoreError(f"Error retrieving item: {e}")

    def search(self, query: dict[str, Any]) -> list[MemoryItem]:
        """
        Search for items in memory matching the query.

        Args:
            query: Dictionary of search criteria

        Returns:
            List of matching memory items

        Raises:
            MemoryStoreError: If the search operation fails
        """
        try:
            logger.info(f"Searching items in LMDB with query: {query}")

            matching_ids = set()
            first_query = True

            with self.begin_transaction(write=False) as txn:
                # Process each query criterion
                for key, value in query.items():
                    current_ids = set()

                    if key == "memory_type" and isinstance(value, MemoryType):
                        # Search by memory_type
                        prefix = f"memory_type:{value.value}:".encode()
                        cursor = txn.cursor(db=self.metadata_db)
                        if cursor.set_range(prefix):
                            while cursor.key().startswith(prefix):
                                # Extract the ID from the key
                                key_parts = cursor.key().decode("utf-8").split(":")
                                if len(key_parts) >= 3:
                                    current_ids.add(key_parts[2])
                                if not cursor.next():
                                    break

                    elif key == "content" and isinstance(value, str):
                        # Search by content (full scan required)
                        cursor = txn.cursor(db=self.items_db)
                        if cursor.first():
                            while True:
                                item_data = cursor.value()
                                item_data = self._decrypt(item_data)
                                item = self._deserialize_memory_item(item_data)
                                if value.lower() in item.content.lower():
                                    current_ids.add(item.id)
                                if not cursor.next():
                                    break

                    elif key.startswith("metadata."):
                        # Extract the metadata field name
                        field = key.split(".", 1)[1]

                        # Search by metadata field
                        prefix = f"metadata:{field}:{value}:".encode()
                        cursor = txn.cursor(db=self.metadata_db)
                        if cursor.set_range(prefix):
                            while cursor.key().startswith(prefix):
                                # Extract the ID from the key
                                key_parts = cursor.key().decode("utf-8").split(":")
                                if len(key_parts) >= 4:
                                    current_ids.add(key_parts[3])
                                if not cursor.next():
                                    break

                    # Intersect with previous results for AND logic
                    if first_query:
                        matching_ids = current_ids
                        first_query = False
                    else:
                        matching_ids &= current_ids

                # Retrieve all matching items
                items = []
                for item_id in matching_ids:
                    item = self.retrieve_in_transaction(txn, item_id)
                    if item:
                        items.append(item)

            # Update token count
            if items:
                token_count = sum(self._count_tokens(str(item)) for item in items)
                self.token_count += token_count

            logger.info(f"Found {len(items)} matching items in LMDB")
            return items

        except Exception as e:
            logger.error(f"Error searching items in LMDB: {e}")
            raise MemoryStoreError(f"Error searching items: {e}")

    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False if it was not found

        Raises:
            MemoryStoreError: If the delete operation fails
        """
        try:
            with self.begin_transaction() as txn:
                # Check if the item exists
                item = self.retrieve_in_transaction(txn, item_id)
                if not item:
                    logger.warning(f"Item with ID {item_id} not found for deletion")
                    audit_event(
                        "delete_memory",
                        store="LMDBStore",
                        item_id=item_id,
                        deleted=False,
                    )
                    return False

                # Delete metadata entries
                if item.metadata:
                    for key, value in item.metadata.items():
                        metadata_key = f"metadata:{key}:{value}:{item_id}".encode()
                        txn.delete(metadata_key, db=self.metadata_db)

                # Delete memory_type entry
                if item.memory_type:
                    memory_type_key = (
                        f"memory_type:{item.memory_type.value}:{item_id}".encode()
                    )
                    txn.delete(memory_type_key, db=self.metadata_db)

                # Delete content entry
                content_key = f"content:{item_id}".encode()
                txn.delete(content_key, db=self.metadata_db)

                # Delete the item itself
                txn.delete(item_id.encode("utf-8"), db=self.items_db)

            logger.info(f"Deleted item with ID {item_id} from LMDB")
            audit_event(
                "delete_memory",
                store="LMDBStore",
                item_id=item_id,
                deleted=True,
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting item from LMDB: {e}")
            raise MemoryStoreError(f"Error deleting item: {e}")

    def get_token_usage(self) -> int:
        """
        Get the current token usage estimate.

        Returns:
            The estimated token usage
        """
        return self.token_count

    def get_all_items(self) -> list[MemoryItem]:
        """Return all stored :class:`MemoryItem` objects."""

        items: list[MemoryItem] = []
        try:
            with self.begin_transaction(write=False) as txn:
                cursor = txn.cursor(db=self.items_db)
                if cursor.first():
                    while True:
                        data = self._decrypt(cursor.value())
                        item = self._deserialize_memory_item(data)
                        items.append(item)
                        if not cursor.next():
                            break
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to fetch all items: %s", exc)
        return items
