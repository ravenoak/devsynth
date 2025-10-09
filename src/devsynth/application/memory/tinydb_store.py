"""
TinyDB implementation of MemoryStore.
"""

import json
import os
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime

import tiktoken
from tinydb import Query, TinyDB  # type: ignore[import-not-found]
from tinydb.middlewares import CachingMiddleware  # type: ignore[import-not-found]
from tinydb.storages import (  # type: ignore[import-not-found]
    JSONStorage,
    Storage,
    touch,
)

from devsynth.exceptions import (
    DevSynthError,
    MemoryError,
    MemoryItemNotFoundError,
    MemoryStoreError,
)
from devsynth.logging_setup import DevSynthLogger
from devsynth.security.audit import audit_event
from devsynth.security.encryption import decrypt_bytes, encrypt_bytes

from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType
from .dto import (
    MemoryMetadata,
    MemoryMetadataValue,
    MemoryRecord,
    MemorySearchQuery,
    build_memory_record,
)


def _coerce_metadata_value(value: object) -> MemoryMetadataValue:
    """Normalize arbitrary objects into ``MemoryMetadataValue`` entries."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, datetime):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _coerce_metadata_value(inner_value)
            for key, inner_value in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_coerce_metadata_value(inner) for inner in value]
    raise TypeError(f"Unsupported metadata value: {value!r}")


def _deserialize_metadata(payload: object) -> MemoryMetadata | None:
    """Convert raw payloads from TinyDB into ``MemoryMetadata`` mappings."""

    if not isinstance(payload, Mapping):
        return None
    normalized: dict[str, MemoryMetadataValue] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TypeError("Metadata keys must be strings")
        normalized[key] = _coerce_metadata_value(value)
    return normalized


def _deserialize_table(payload: object) -> dict[str, dict[str, object]]:
    """Ensure TinyDB tables deserialize into nested dictionaries."""

    if not isinstance(payload, Mapping):
        raise TypeError("TinyDB payload must be a mapping")
    normalized: dict[str, dict[str, object]] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise TypeError("TinyDB table keys must be strings")
        if not isinstance(value, Mapping):
            raise TypeError("TinyDB table rows must be mappings")
        normalized[key] = {
            str(inner_key): inner_value for inner_key, inner_value in value.items()
        }
    return normalized


class EncryptedJSONStorage(Storage):
    """JSON storage with encryption at rest."""

    def __init__(self, path: str, key: str, create_dirs: bool = False):
        super().__init__()
        self._key = key
        touch(path, create_dirs=create_dirs)
        self._handle = open(path, "r+b")

    def close(self) -> None:
        self._handle.close()

    def read(self) -> dict[str, dict[str, object]] | None:
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()
        if not size:
            return None
        self._handle.seek(0)
        data = self._handle.read()
        data = decrypt_bytes(data, key=self._key)
        payload = json.loads(data.decode("utf-8"))
        return _deserialize_table(payload)

    def write(self, data: dict[str, dict[str, object]]) -> None:
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
        encryption_key: str | None = None,
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

    def _serialize_memory_item(self, item: MemoryItem) -> dict[str, object]:
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
        metadata_payload: dict[str, MemoryMetadataValue] | None = None
        if item.metadata:
            metadata_payload = {
                key: _coerce_metadata_value(value)
                for key, value in item.metadata.items()
            }

        serialized = {
            "id": item.id,
            "content": item.content,
            "memory_type": memory_type_str,
            "metadata": metadata_payload,
            "created_at": created_at_str,
        }

        return serialized

    def _deserialize_memory_item(self, data: Mapping[str, object]) -> MemoryItem:
        """
        Deserialize a dictionary to a MemoryItem.

        Args:
            data: The dictionary to deserialize

        Returns:
            A MemoryItem object
        """
        payload = dict(data)

        metadata_payload = payload.get("metadata")
        metadata = _deserialize_metadata(metadata_payload)

        memory_type_raw = payload.get("memory_type")
        memory_type = (
            MemoryType(memory_type_raw)
            if isinstance(memory_type_raw, str) and memory_type_raw
            else None
        )

        created_at_raw = payload.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_raw)
            if isinstance(created_at_raw, str) and created_at_raw
            else None
        )

        identifier = str(payload.get("id", ""))
        content = payload.get("content")

        return MemoryItem(
            id=identifier,
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            created_at=created_at,
        )

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
            return str(item.id)

        except Exception as e:
            logger.error(f"Failed to store item in TinyDB: {e}")
            raise MemoryStoreError(
                "Failed to store item",
                store_type="tinydb",
                operation="store",
                original_error=e,
            )

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

    def search(self, query: MemorySearchQuery | MemoryMetadata) -> list[MemoryRecord]:
        """
        Search for items in memory matching the query.

        Args:
            query: Mapping of search criteria compatible with ``MemoryMetadata``

        Returns:
            List of matching memory records provided by the TinyDB store

        Raises:
            MemoryStoreError: If the search operation fails
        """
        try:
            logger.info(f"Searching items in TinyDB with query: {query}")

            # Get all items from TinyDB
            all_items = self.db.all()

            # Filter items based on query
            filtered_items: list[MemoryRecord] = []
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
                    item = self._deserialize_memory_item(item_data)
                    filtered_items.append(
                        build_memory_record(item, source=self.__class__.__name__)
                    )

            # Update token count
            if filtered_items:
                token_count = sum(
                    self._count_tokens(str(record.item)) for record in filtered_items
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

    def close(self) -> None:
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

    supports_transactions: bool = False
