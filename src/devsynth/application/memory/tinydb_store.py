"""
TinyDB implementation of MemoryStore.
"""

import os
import json
import uuid
import tiktoken
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage, Storage, touch
from tinydb.middlewares import CachingMiddleware

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
from devsynth.security.audit import audit_event


class EncryptedJSONStorage(Storage):
    """JSON storage with encryption at rest."""

    def __init__(self, path: str, key: str, create_dirs: bool = False):
        super().__init__()
        self._key = key
        touch(path, create_dirs=create_dirs)
        self._handle = open(path, "r+b")

    def close(self) -> None:
        self._handle.close()

    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()
        if not size:
            return None
        self._handle.seek(0)
        data = self._handle.read()
        data = decrypt_bytes(data, key=self._key)
        return json.loads(data.decode("utf-8"))

    def write(self, data: Dict[str, Dict[str, Any]]):
        self._handle.seek(0)
        raw = json.dumps(data).encode("utf-8")
        raw = encrypt_bytes(raw, key=self._key)
        self._handle.write(raw)
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.truncate()


# Create a logger for this module
logger = DevSynthLogger(__name__)


class TinyDBStore(MemoryStore):
    """TinyDB implementation of the MemoryStore interface."""

    def __init__(
        self,
        base_path: str,
        *,
        encryption_enabled: bool = False,
        encryption_key: Union[str, None] = None,
    ):
        """
        Initialize a TinyDBStore.

        Args:
            base_path: Base path for storing the TinyDB database file
        """
        self.base_path = base_path
        self.db_file = os.path.join(self.base_path, "memory.json")
        self.token_count = 0
        self.encryption_enabled = encryption_enabled
        self.encryption_key = encryption_key

        # Ensure the directory exists
        os.makedirs(self.base_path, exist_ok=True)

        # Initialize TinyDB with caching for better performance
        if self.encryption_enabled:
            storage = CachingMiddleware(
                lambda p: EncryptedJSONStorage(p, self.encryption_key or "")
            )
        else:
            storage = CachingMiddleware(JSONStorage)
        self.db = TinyDB(self.db_file, storage=storage)

        # Initialize the tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
        except Exception as e:
            logger.warning(
                f"Failed to initialize tokenizer: {e}. Token counting will be approximate."
            )
            self.tokenizer = None

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

    def _serialize_memory_item(self, item: MemoryItem) -> Dict[str, Any]:
        """
        Serialize a MemoryItem to a dictionary for storage in TinyDB.

        Args:
            item: The MemoryItem to serialize

        Returns:
            A dictionary representation of the MemoryItem
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

        return serialized

    def _deserialize_memory_item(self, data: Dict[str, Any]) -> MemoryItem:
        """
        Deserialize a dictionary to a MemoryItem.

        Args:
            data: The dictionary to deserialize

        Returns:
            A MemoryItem object
        """
        # Convert memory_type string to enum
        memory_type = MemoryType(data["memory_type"]) if data["memory_type"] else None

        # Convert created_at string to datetime
        created_at = (
            datetime.fromisoformat(data["created_at"]) if data["created_at"] else None
        )

        # Create a MemoryItem
        item = MemoryItem(
            id=data["id"],
            content=data["content"],
            memory_type=memory_type,
            metadata=data["metadata"],
            created_at=created_at,
        )

        return item

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
            # Generate an ID if not provided
            if not item.id:
                item.id = str(uuid.uuid4())

            # Serialize the item
            serialized = self._serialize_memory_item(item)

            # Store in TinyDB
            self.db.upsert(serialized, Query().id == item.id)

            # Update token count
            token_count = self._count_tokens(str(serialized))
            self.token_count += token_count

            logger.info(f"Stored item with ID {item.id} in TinyDB")
            audit_event(
                "store_memory",
                store="TinyDBStore",
                item_id=item.id,
            )
            return item.id

        except Exception as e:
            logger.error(f"Failed to store item in TinyDB: {e}")
            raise MemoryStoreError(
                "Failed to store item",
                store_type="tinydb",
                operation="store",
                original_error=e,
            )

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
            # Query TinyDB for the item
            result = self.db.get(Query().id == item_id)

            # Check if the item was found
            if not result:
                logger.warning(f"Item with ID {item_id} not found in TinyDB")
                audit_event(
                    "retrieve_memory",
                    store="TinyDBStore",
                    item_id=item_id,
                    found=False,
                )
                return None

            # Deserialize to a MemoryItem
            item = self._deserialize_memory_item(result)

            # Update token count
            token_count = self._count_tokens(str(result))
            self.token_count += token_count

            logger.info(f"Retrieved item with ID {item_id} from TinyDB")
            audit_event(
                "retrieve_memory",
                store="TinyDBStore",
                item_id=item_id,
                found=True,
            )
            return item

        except Exception as e:
            logger.error(f"Error retrieving item from TinyDB: {e}")
            raise MemoryStoreError(
                "Error retrieving item",
                store_type="tinydb",
                operation="retrieve",
                original_error=e,
            )

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
            logger.info(f"Searching items in TinyDB with query: {query}")

            # Get all items from TinyDB
            all_items = self.db.all()

            # Filter items based on query
            filtered_items = []
            for item_data in all_items:
                match = True

                for key, value in query.items():
                    if key == "memory_type" and isinstance(value, MemoryType):
                        # Compare memory_type enum value
                        if item_data["memory_type"] != value.value:
                            match = False
                            break
                    elif key == "content" and isinstance(value, str):
                        # Case-insensitive content search
                        if value.lower() not in str(item_data["content"]).lower():
                            match = False
                            break
                    elif key.startswith("metadata."):
                        # Extract the metadata field name
                        field = key.split(".", 1)[1]
                        if (
                            "metadata" not in item_data
                            or field not in item_data["metadata"]
                            or item_data["metadata"][field] != value
                        ):
                            match = False
                            break
                    else:
                        # Direct field comparison
                        if key not in item_data or item_data[key] != value:
                            match = False
                            break

                if match:
                    # Deserialize matching items
                    filtered_items.append(self._deserialize_memory_item(item_data))

            # Update token count
            if filtered_items:
                token_count = sum(
                    self._count_tokens(str(item)) for item in filtered_items
                )
                self.token_count += token_count

            logger.info(f"Found {len(filtered_items)} matching items in TinyDB")
            return filtered_items

        except Exception as e:
            logger.error(f"Error searching items in TinyDB: {e}")
            raise MemoryStoreError(
                "Error searching items",
                store_type="tinydb",
                operation="search",
                original_error=e,
            )

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
            # Check if the item exists
            if not self.db.get(Query().id == item_id):
                logger.warning(f"Item with ID {item_id} not found for deletion")
                audit_event(
                    "delete_memory",
                    store="TinyDBStore",
                    item_id=item_id,
                    deleted=False,
                )
                return False

            # Delete the item
            self.db.remove(Query().id == item_id)

            logger.info(f"Deleted item with ID {item_id} from TinyDB")
            audit_event(
                "delete_memory",
                store="TinyDBStore",
                item_id=item_id,
                deleted=True,
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting item from TinyDB: {e}")
            raise MemoryStoreError(
                "Error deleting item",
                store_type="tinydb",
                operation="delete",
                original_error=e,
            )

    def get_token_usage(self) -> int:
        """
        Get the current token usage estimate.

        Returns:
            The estimated token usage
        """
        return self.token_count

    def close(self):
        """
        Close the database connection and ensure all data is persisted.

        This method should be called when the store is no longer needed
        to ensure that all data is properly persisted to disk.
        """
        if hasattr(self, "db") and self.db:
            # Ensure all data is written to disk
            self.db.storage.flush()
            # Close the database
            self.db.close()
            logger.info(f"Closed TinyDB database at {self.db_file}")
