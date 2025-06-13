"""
LMDB implementation of MemoryStore.

This implementation uses LMDB (Lightning Memory-Mapped Database) to store
and retrieve memory items with transaction support.
"""

import os
import json
import uuid
import tiktoken
try:
    import lmdb
except ImportError as e:  # pragma: no cover - optional dependency
    raise ImportError(
        "LMDBStore requires the 'lmdb' package. Install it with 'pip install lmdb' or use the dev extras."
    ) from e
from typing import Dict, List, Any, Optional, ContextManager
from datetime import datetime
from contextlib import contextmanager

from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import (
    DevSynthError,
    MemoryError,
    MemoryStoreError,
    MemoryItemNotFoundError,
)
from devsynth.security.encryption import encrypt_bytes, decrypt_bytes

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
        except Exception as e:
            logger.warning(
                f"Failed to initialize tokenizer: {e}. Token counting will be approximate."
            )
            self.tokenizer = None

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
    def begin_transaction(self, write: bool = True) -> ContextManager:
        """
        Begin a transaction.

        Args:
            write: Whether the transaction is for writing (default: True)

        Yields:
            An LMDB transaction object
        """
        with self.env.begin(write=write) as txn:
            yield txn

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
                metadata_key = f"metadata:{key}:{value}:{item.id}".encode("utf-8")
                txn.put(metadata_key, b"1", db=self.metadata_db)

        # Store memory_type for searching
        if item.memory_type:
            memory_type_key = f"memory_type:{item.memory_type.value}:{item.id}".encode(
                "utf-8"
            )
            txn.put(memory_type_key, b"1", db=self.metadata_db)

        # Store content for searching
        if item.content:
            content_key = f"content:{item.id}".encode("utf-8")
            txn.put(content_key, item.content.encode("utf-8"), db=self.metadata_db)

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

            logger.info(f"Stored item with ID {item_id} in LMDB")
            return item_id

        except Exception as e:
            logger.error(f"Failed to store item in LMDB: {e}")
            raise MemoryStoreError(f"Failed to store item: {e}")

    def retrieve_in_transaction(self, txn, item_id: str) -> Optional[MemoryItem]:
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

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
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
                return None

            # Update token count
            token_count = self._count_tokens(str(item))
            self.token_count += token_count

            logger.info(f"Retrieved item with ID {item_id} from LMDB")
            return item

        except Exception as e:
            logger.error(f"Error retrieving item from LMDB: {e}")
            raise MemoryStoreError(f"Error retrieving item: {e}")

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
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
                        prefix = f"memory_type:{value.value}:".encode("utf-8")
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
                        prefix = f"metadata:{field}:{value}:".encode("utf-8")
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
                    return False

                # Delete metadata entries
                if item.metadata:
                    for key, value in item.metadata.items():
                        metadata_key = f"metadata:{key}:{value}:{item_id}".encode(
                            "utf-8"
                        )
                        txn.delete(metadata_key, db=self.metadata_db)

                # Delete memory_type entry
                if item.memory_type:
                    memory_type_key = (
                        f"memory_type:{item.memory_type.value}:{item_id}".encode(
                            "utf-8"
                        )
                    )
                    txn.delete(memory_type_key, db=self.metadata_db)

                # Delete content entry
                content_key = f"content:{item_id}".encode("utf-8")
                txn.delete(content_key, db=self.metadata_db)

                # Delete the item itself
                txn.delete(item_id.encode("utf-8"), db=self.items_db)

            logger.info(f"Deleted item with ID {item_id} from LMDB")
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
