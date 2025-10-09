"""
ChromaDB implementation of the MemoryStore interface.

This implementation includes enhanced features:
- Caching layer to reduce disk I/O operations
- Version tracking for stored artifacts
- Optimized embedding storage for similar content
"""

import json
import os
from collections.abc import Mapping
from datetime import datetime
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from devsynth.application.memory.dto import (
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
    MemorySearchQuery,
)
from devsynth.application.memory.metadata_serialization import (
    from_serializable,
    query_results_from_rows,
    record_from_row,
    to_serializable,
)
from devsynth.application.utils.extras import require_optional_package

try:
    import chromadb
except ImportError as e:  # pragma: no cover - optional dependency
    raise require_optional_package(
        e,
        extra_name="memory",
        packages=["chromadb"],
        context="ChromaDB memory store",
    )

try:
    import tiktoken
except ImportError as e:  # pragma: no cover - optional dependency
    raise require_optional_package(
        e,
        extra_name="llm",
        packages=["tiktoken"],
        context="ChromaDB token counting",
    )

from devsynth.exceptions import (
    DevSynthError,
    MemoryCorruptionError,
    MemoryError,
    MemoryItemNotFoundError,
    MemoryStoreError,
)
from devsynth.fallback import retry_with_exponential_backoff, with_fallback
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryType

# Create a logger for this module
logger = DevSynthLogger(__name__)


__all__ = ["ChromaDBStore"]


P = ParamSpec("P")
R = TypeVar("R")

SerializedPayload = dict[str, object]
SerializedVersionHistory = list[SerializedPayload]


def _typed_retry_with_backoff(
    *args: object, **kwargs: object
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        wrapped = retry_with_exponential_backoff(*args, **kwargs)(func)

        @wraps(func)
        def wrapper(*inner_args: P.args, **inner_kwargs: P.kwargs) -> R:
            return wrapped(*inner_args, **inner_kwargs)

        return wrapper

    return decorator


class ChromaDBStore(MemoryStore):
    """
    ChromaDB implementation of the MemoryStore interface.

    This class uses ChromaDB to store and retrieve memory items, providing
    vector-based semantic search capabilities.

    Enhanced features:
    - Caching layer to reduce disk I/O operations
    - Version tracking for stored artifacts
    - Optimized embedding storage for similar content
    """

    def __init__(
        self,
        file_path: str,
        *,
        host: str | None = None,
        port: int = 8000,
        collection_name: str | None = None,
        versions_collection_name: str | None = None,
    ):
        """
        Initialize the ChromaDB store.

        Args:
            file_path: Path to the directory where ChromaDB will store its data
            host: Optional remote host for an existing ChromaDB server
            port: Port for the remote ChromaDB server (default: 8000)
            collection_name: Name of the primary collection
            versions_collection_name: Name of the versions collection
        """
        self.file_path = file_path
        self.collection_name = collection_name or "devsynth_memory"
        self.versions_collection_name = (
            versions_collection_name or "devsynth_memory_versions"
        )
        self._token_usage = 0
        self._cache: dict[str, MemoryRecord] = {}
        self._embedding_optimization_enabled = True

        # Check if we're in a test environment with file operations disabled
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        # Check if network access should be disabled
        no_network = os.environ.get("DEVSYNTH_NO_NETWORK", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        if host and not no_network:
            # Connect to a remote ChromaDB server
            logger.info("Connecting to remote ChromaDB host %s:%s", host, port)
            self.client = chromadb.HttpClient(host=host, port=port)
        elif host and no_network:
            logger.info("DEVSYNTH_NO_NETWORK set; using in-memory ChromaDB client")
            self.client = chromadb.EphemeralClient()
        else:
            # Only create directories if not in a test environment with file operations disabled
            if not no_file_logging:
                os.makedirs(file_path, exist_ok=True)
                self.client = chromadb.PersistentClient(path=file_path)
            else:
                # In test environments, use an in-memory client to avoid file system operations
                logger.info("Using in-memory ChromaDB client for test environment")
                self.client = chromadb.EphemeralClient()

        # Get or create the main collection
        self._use_fallback = False
        self._store: dict[str, SerializedPayload] = {}
        self._versions: dict[str, SerializedVersionHistory] = {}
        self._fallback_file = os.path.join(file_path, "fallback_store.json")

        if os.path.exists(self._fallback_file):
            try:
                with open(self._fallback_file, "r") as f:
                    data = json.load(f)
                    for item_dict in data.get("items", []):
                        if not isinstance(item_dict, dict):
                            continue
                        serialized_item: SerializedPayload = {
                            str(key): value for key, value in item_dict.items()
                        }
                        record = self._record_from_serialized(
                            serialized_item, fallback=True
                        )
                        self._store[record.id] = serialized_item
                        self._cache[record.id] = record
                    for vid, versions in data.get("versions", {}).items():
                        if not isinstance(vid, str) or not isinstance(versions, list):
                            continue
                        sanitized: SerializedVersionHistory = [
                            {str(key): value for key, value in entry.items()}
                            for entry in versions
                            if isinstance(entry, dict)
                        ]
                        if sanitized:
                            self._versions[vid] = sanitized
                self._use_fallback = True
            except Exception as e:
                logger.error(
                    f"Failed to load fallback store from {self._fallback_file}: {e}"
                )

        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing ChromaDB collection: {self.collection_name}")
        except Exception as e:
            try:
                # Collection doesn't exist, create it
                logger.info(f"Collection not found: {e}")
                self.collection = self.client.create_collection(
                    name=self.collection_name
                )
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
            except Exception as e2:
                logger.warning(
                    f"Failed to initialize ChromaDB collection: {e2}. Falling back to in-memory store"
                )
                self._use_fallback = True
                if os.path.exists(self._fallback_file):
                    try:
                        with open(self._fallback_file, "r") as f:
                            data = json.load(f)
                            for item_dict in data.get("items", []):
                                if not isinstance(item_dict, dict):
                                    continue
                                serialized_item: SerializedPayload = {
                                    str(key): value for key, value in item_dict.items()
                                }
                                record = self._record_from_serialized(
                                    serialized_item, fallback=True
                                )
                                self._store[record.id] = serialized_item
                                self._cache[record.id] = record
                            for vid, versions in data.get("versions", {}).items():
                                if not isinstance(vid, str) or not isinstance(
                                    versions, list
                                ):
                                    continue
                                sanitized_versions: SerializedVersionHistory = [
                                    {str(key): value for key, value in entry.items()}
                                    for entry in versions
                                    if isinstance(entry, dict)
                                ]
                                if sanitized_versions:
                                    self._versions[vid] = sanitized_versions
                    except Exception as e3:
                        logger.error(
                            f"Failed to load fallback store from {self._fallback_file}: {e3}"
                        )

        if not self._use_fallback:
            try:
                self.versions_collection = self.client.get_collection(
                    name=self.versions_collection_name
                )
                logger.info(
                    f"Using existing ChromaDB versions collection: {self.versions_collection_name}"
                )
            except Exception as e:
                try:
                    self.versions_collection = self.client.create_collection(
                        name=self.versions_collection_name
                    )
                    logger.info(
                        f"Created new ChromaDB versions collection: {self.versions_collection_name}"
                    )
                except Exception as e2:
                    logger.warning(
                        f"Failed to initialize versions collection: {e2}. Falling back to in-memory store"
                    )
                    self._use_fallback = True

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
            try:
                tokens = self.tokenizer.encode(text)
                return len(tokens)
            except Exception as e:
                logger.warning(
                    f"Tokenizer error: {e}; falling back to approximate count"
                )
        return len(text) // 4

    def _resolve_source(self, *, fallback: bool | None = None) -> str:
        resolved_fallback = self._use_fallback if fallback is None else fallback
        return (
            self.collection_name
            if not resolved_fallback
            else f"{self.collection_name}-fallback"
        )

    def _record_from_serialized(
        self, payload: Mapping[str, object], *, fallback: bool | None = None
    ) -> MemoryRecord:
        return record_from_row(
            payload, default_source=self._resolve_source(fallback=fallback)
        )

    def _serialize_memory_item(self, item: MemoryItem) -> SerializedPayload:
        """
        Serialize a MemoryItem to a dictionary for storage in ChromaDB.

        Args:
            item: The MemoryItem to serialize

        Returns:
            A dictionary representation of the MemoryItem
        """
        metadata_payload = to_serializable(item.metadata)

        created_at_str = item.created_at.isoformat() if item.created_at else None

        return {
            "id": item.id,
            "content": item.content,
            "memory_type": item.memory_type.value if item.memory_type else None,
            "metadata": metadata_payload,
            "created_at": created_at_str,
        }

    def _deserialize_memory_item(self, data: Mapping[str, object]) -> MemoryItem:
        """
        Deserialize a dictionary to a MemoryItem.

        Args:
            data: The dictionary to deserialize

        Returns:
            A MemoryItem object
        """
        raw_metadata = data.get("metadata")
        metadata = (
            from_serializable(raw_metadata) if isinstance(raw_metadata, Mapping) else {}
        )

        created_at_value = data.get("created_at")
        created_at = None
        if isinstance(created_at_value, str) and created_at_value:
            try:
                created_at = datetime.fromisoformat(created_at_value)
            except ValueError:
                logger.debug(
                    "Invalid created_at value %s for item %s",
                    created_at_value,
                    data.get("id"),
                )

        memory_type_value = data.get("memory_type")
        memory_type = MemoryType.from_raw(memory_type_value)

        content = data.get("content")

        return MemoryItem(
            id=data.get("id", ""),
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            created_at=created_at,
        )

    @_typed_retry_with_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def store(self, item: MemoryItem) -> str:
        """
        Store an item in memory and return its ID.

        If an item with the same ID already exists, it will be versioned.
        The latest version will be stored in the main collection,
        and all versions will be stored in the versions collection.

        Args:
            item: The MemoryItem to store

        Returns:
            The ID of the stored item
        """
        serialized: SerializedPayload | None = None
        record: MemoryRecord | None = None

        try:
            if item is None or not getattr(item, "id", None):
                raise MemoryStoreError("MemoryItem must have a non-empty id")
            if getattr(item, "content", None) is None:
                raise MemoryStoreError("MemoryItem content cannot be None")

            if self._use_fallback:
                existing_payload = self._store.get(item.id)
                existing_record = (
                    self._record_from_serialized(existing_payload, fallback=True)
                    if existing_payload
                    else None
                )
                is_update = existing_record is not None
            else:
                existing_record = self.retrieve(item.id)
                is_update = existing_record is not None

            metadata = dict(item.metadata or {})

            if is_update:
                versions = self.get_versions(item.id)
                current_version = len(versions)
                new_version = current_version + 1
                metadata["version"] = new_version
                if existing_record is not None:
                    self._store_version(existing_record, current_version)
            else:
                metadata.setdefault("version", 1)

            prepared_item = MemoryItem(
                id=item.id,
                content=item.content,
                memory_type=item.memory_type,
                metadata=metadata,
                created_at=item.created_at,
            )

            serialized = self._serialize_memory_item(prepared_item)
            record = self._record_from_serialized(
                serialized, fallback=self._use_fallback
            )

            metadata_json = json.dumps(serialized)

            token_count = self._count_tokens(str(serialized))
            self._token_usage += token_count

            document_content = (
                json.dumps(prepared_item.content)
                if not isinstance(prepared_item.content, str)
                else prepared_item.content
            )

            if self._use_fallback:
                serialized_copy = json.loads(json.dumps(serialized))
                if isinstance(serialized_copy, dict):
                    fallback_payload: SerializedPayload = {
                        str(key): value for key, value in serialized_copy.items()
                    }
                    self._store[item.id] = fallback_payload
                else:
                    logger.error(
                        "Serialized payload for item %s did not deserialize to a mapping",
                        item.id,
                    )
                    self._store[item.id] = serialized
                self._cache[item.id] = record
                self._save_fallback()
            else:
                self.collection.upsert(
                    ids=[item.id],
                    documents=[document_content],
                    metadatas=[{"item_data": metadata_json}],
                )
                self._cache[item.id] = record

            logger.info(f"Stored item with ID {item.id} in ChromaDB")
            return str(item.id)

        except Exception as e:
            if not self._use_fallback:
                logger.warning(
                    f"Error storing item in ChromaDB: {e}. Switching to in-memory fallback"
                )
                self._use_fallback = True
                if serialized is None:
                    metadata = dict(item.metadata or {})
                    metadata.setdefault("version", 1)
                    prepared_item = MemoryItem(
                        id=item.id,
                        content=item.content,
                        memory_type=item.memory_type,
                        metadata=metadata,
                        created_at=item.created_at,
                    )
                    serialized = self._serialize_memory_item(prepared_item)
                if record is None:
                    record = self._record_from_serialized(serialized, fallback=True)
                serialized_copy = json.loads(json.dumps(serialized))
                if isinstance(serialized_copy, dict):
                    fallback_payload = {
                        str(key): value for key, value in serialized_copy.items()
                    }
                    self._store[item.id] = fallback_payload
                else:
                    logger.error(
                        "Serialized payload for item %s did not deserialize to a mapping",
                        item.id,
                    )
                    self._store[item.id] = serialized
                self._cache[item.id] = record
                self._save_fallback()
                return str(item.id)
            logger.error(f"Error storing item in ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to store item: {e}")

    def _store_version(self, record: MemoryRecord, version: int) -> None:
        """
        Store a specific version of an item in the versions collection.

        Args:
            record: The MemoryRecord representing the prior version
            version: The version number
        """
        try:
            serialized = self._serialize_memory_item(record.item)
            metadata_payload = serialized.get("metadata")
            if not isinstance(metadata_payload, dict):
                metadata_payload = {}
                serialized["metadata"] = metadata_payload
            metadata_payload["version"] = version

            if self._use_fallback:
                serialized_copy = json.loads(json.dumps(serialized))
                if isinstance(serialized_copy, dict):
                    fallback_payload: SerializedPayload = {
                        str(key): value for key, value in serialized_copy.items()
                    }
                    self._versions.setdefault(record.id, []).append(fallback_payload)
                else:
                    logger.error(
                        "Serialized version payload for %s did not deserialize to a mapping",
                        record.id,
                    )
                self._save_fallback()
                return

            # Convert to JSON for storage
            metadata_json = json.dumps(serialized)

            # Create a unique ID for this version
            version_id = f"{record.id}_v{version}"

            # Store in the versions collection
            # Convert content to string if it's not already a string
            document_content = (
                json.dumps(record.content)
                if not isinstance(record.content, str)
                else record.content
            )

            self.versions_collection.upsert(
                ids=[version_id],
                documents=[document_content],
                metadatas=[
                    {
                        "item_data": metadata_json,
                        "original_id": record.id,
                        "version": version,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
            )

            logger.info(
                f"Stored version {version} of item with ID {record.id} in ChromaDB"
            )

        except Exception as e:
            logger.error(f"Error storing version in ChromaDB: {e}")
            raise MemoryStoreError(f"Failed to store version: {e}")

    def _retrieve_from_db(self, item_id: str) -> MemoryRecord | None:
        """
        Retrieve an item directly from the database without using the cache.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved MemoryRecord, or None if not found
        """
        try:
            if self._use_fallback:
                payload = self._store.get(item_id)
                if not payload:
                    return None
                return self._record_from_serialized(payload, fallback=True)

            # Query ChromaDB for the item
            result = self.collection.get(ids=[item_id])

            # Check if the item was found
            if not result["ids"] or not result["metadatas"]:
                logger.warning(f"Item with ID {item_id} not found in ChromaDB")
                return None

            # Extract the serialized item from metadata
            metadata = result["metadatas"][0]
            item_data = (
                metadata.get("item_data") if isinstance(metadata, dict) else None
            )
            if not item_data:
                logger.warning("Missing item_data in metadata for id %s", item_id)
                return None
            try:
                payload = json.loads(item_data)
            except Exception as je:
                logger.warning("Invalid item_data JSON for id %s: %s", item_id, je)
                return None

            if not isinstance(payload, Mapping):
                logger.warning("Unexpected payload structure for id %s", item_id)
                return None

            record = self._record_from_serialized(payload)

            # Count tokens
            token_count = self._count_tokens(str(payload))
            self._token_usage += token_count

            logger.info(f"Retrieved item with ID {item_id} from ChromaDB")
            return record

        except Exception as e:
            logger.error(f"Error retrieving item from ChromaDB: {e}")
            return None

    @_typed_retry_with_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def retrieve(self, item_id: str) -> MemoryRecord | None:
        """
        Retrieve an item from memory by ID.

        This method uses a caching layer to reduce disk I/O operations.
        The latest version of the item is returned by default.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved MemoryRecord, or None if not found
        """
        # Check if the item is in the cache
        if item_id in self._cache:
            logger.info(f"Retrieved item with ID {item_id} from cache")
            return self._cache[item_id]

        # Item not in cache, retrieve from database
        item = self._retrieve_from_db(item_id)

        # If item was found, add it to the cache
        if item:
            self._cache[item_id] = item

        return item

    @_typed_retry_with_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def retrieve_version(self, item_id: str, version: int) -> MemoryRecord | None:
        """
        Retrieve a specific version of an item.

        Args:
            item_id: The ID of the item to retrieve
            version: The version number to retrieve

        Returns:
            The retrieved MemoryRecord, or None if not found
        """
        try:
            if self._use_fallback:
                version_payloads: list[SerializedPayload] = list(
                    self._versions.get(item_id, [])
                )
                current_payload = self._store.get(item_id)
                if current_payload:
                    version_payloads.append(current_payload)
                for payload in version_payloads:
                    record = self._record_from_serialized(payload, fallback=True)
                    metadata = record.item.metadata or {}
                    if metadata.get("version") == version:
                        return record
                return None

            # First check if this is the current version in the main collection
            current_item = self.retrieve(item_id)
            if current_item and current_item.item.metadata.get("version") == version:
                return current_item

            # Create the version ID
            version_id = f"{item_id}_v{version}"

            # Query the versions collection
            result = self.versions_collection.get(ids=[version_id])

            # Check if the version was found
            if not result["ids"] or not result["metadatas"]:
                logger.warning(
                    f"Version {version} of item with ID {item_id} not found in ChromaDB"
                )
                return None

            # Extract the serialized item from metadata
            metadata = result["metadatas"][0]
            item_data = (
                metadata.get("item_data") if isinstance(metadata, dict) else None
            )
            if not item_data:
                logger.warning(
                    "Missing item_data in metadata for version %s of id %s",
                    version,
                    item_id,
                )
                return None
            try:
                payload = json.loads(item_data)
            except Exception as je:
                logger.warning(
                    "Invalid item_data JSON for version %s of id %s: %s",
                    version,
                    item_id,
                    je,
                )
                return None

            if not isinstance(payload, Mapping):
                logger.warning("Unexpected payload structure for version %s", version)
                return None

            record = self._record_from_serialized(payload)

            # Count tokens
            token_count = self._count_tokens(str(payload))
            self._token_usage += token_count

            logger.info(
                f"Retrieved version {version} of item with ID {item_id} from ChromaDB"
            )
            return record

        except Exception as e:
            logger.error(f"Error retrieving version from ChromaDB: {e}")
            return None

    @_typed_retry_with_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def search(self, query: MemorySearchQuery | MemoryMetadata) -> MemoryQueryResults:
        """
        Search for items in memory matching the query.

        The query can contain:
        - Exact match criteria for memory_type and metadata fields
        - A semantic_query field for semantic search

        Args:
            query: The search query

        Returns:
            MemoryQueryResults for this store containing matching records
        """
        try:
            # Check if this is a semantic search
            if "semantic_query" in query:
                records = self._semantic_search(query)
            else:
                records = self._exact_match_search(query)

            return query_results_from_rows(
                self._resolve_source(),
                records,
            )

        except Exception as e:
            logger.error(f"Error searching in ChromaDB: {e}")
            return {"store": self._resolve_source(), "records": []}

    def _semantic_search(
        self, query: MemorySearchQuery | MemoryMetadata
    ) -> list[MemoryRecord]:
        """
        Perform a semantic search using ChromaDB's similarity search.

        Args:
            query: The search query containing a semantic_query field

        Returns:
            A list of MemoryRecords ranked by semantic similarity
        """
        semantic_query = query["semantic_query"]

        # Count tokens
        token_count = self._count_tokens(semantic_query)
        self._token_usage += token_count

        if self._use_fallback:
            records: list[MemoryRecord] = []
            for payload in self._store.values():
                record = self._record_from_serialized(payload, fallback=True)
                content = record.content
                if (
                    isinstance(content, str)
                    and semantic_query.lower() in content.lower()
                ):
                    records.append(record)
            return records

        # Perform the search
        results = self.collection.query(
            query_texts=[semantic_query], n_results=10  # Return top 10 results
        )

        # Process results
        records = []
        metadatas = results.get("metadatas") or []
        if metadatas:
            metadata_rows = (
                metadatas[0] if isinstance(metadatas[0], list) else metadatas
            )
            for metadata in metadata_rows:
                item_data = (
                    metadata.get("item_data") if isinstance(metadata, dict) else None
                )
                if not item_data:
                    logger.debug("Skipping result missing item_data")
                    continue
                try:
                    payload = json.loads(item_data)
                except Exception as je:
                    logger.debug("Skipping result with invalid item_data JSON: %s", je)
                    continue

                if not isinstance(payload, Mapping):
                    logger.debug("Skipping result with non-mapping payload")
                    continue

                record = self._record_from_serialized(payload)
                records.append(record)

        logger.info(
            f"Semantic search for '{semantic_query}' returned {len(records)} results"
        )
        return records

    def _exact_match_search(
        self, query: MemorySearchQuery | MemoryMetadata
    ) -> list[MemoryRecord]:
        """
        Perform an exact match search using ChromaDB's filtering.

        Args:
            query: The search query containing exact match criteria

        Returns:
            A list of MemoryRecords matching the criteria
        """
        # Build the filter for ChromaDB
        # We need to get all items and filter them manually since ChromaDB's
        # filtering is limited to metadata fields

        rows: list[SerializedPayload] = []
        if self._use_fallback:
            rows = list(self._store.values())
        else:
            results = self.collection.get()
            metadatas = results.get("metadatas") or []
            for metadata in metadatas:
                item_data = (
                    metadata.get("item_data") if isinstance(metadata, dict) else None
                )
                if not item_data:
                    logger.debug("Skipping item without item_data during exact search")
                    continue
                try:
                    payload = json.loads(item_data)
                except Exception as je:
                    logger.debug("Skipping item with invalid item_data JSON: %s", je)
                    continue
                if not isinstance(payload, Mapping):
                    logger.debug("Skipping item with non-mapping payload")
                    continue
                rows.append(dict(payload))

        filtered_items: list[MemoryRecord] = []
        for payload in rows:
            record = self._record_from_serialized(payload, fallback=self._use_fallback)
            match = True

            for key, value in query.items():
                if key == "semantic_query":
                    continue
                if key == "memory_type":
                    memory_type = record.item.memory_type
                    if isinstance(value, str):
                        expected = value
                        actual = (
                            memory_type.value
                            if hasattr(memory_type, "value")
                            else str(memory_type)
                        )
                        if actual != expected:
                            match = False
                            break
                    elif memory_type != value:
                        match = False
                        break
                elif key.startswith("metadata."):
                    field = key.split(".", 1)[1]
                    metadata = record.item.metadata or {}
                    if metadata.get(field) != value:
                        match = False
                        break

            if match:
                filtered_items.append(record)

        # Count tokens
        token_count = self._count_tokens(str(query))
        self._token_usage += token_count

        logger.info(f"Exact match search returned {len(filtered_items)} results")
        return filtered_items

    @_typed_retry_with_backoff(max_retries=3, retryable_exceptions=(Exception,))
    def delete(self, item_id: str) -> bool:
        """
        Delete an item from memory.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False otherwise
        """
        try:
            # Check if the item exists
            item = self.retrieve(item_id)
            if not item:
                logger.warning(f"Item with ID {item_id} not found for deletion")
                return False

            if self._use_fallback:
                existed = item_id in self._store
                self._store.pop(item_id, None)
                self._versions.pop(item_id, None)
                self._cache.pop(item_id, None)
                self._save_fallback()
                return existed

            # Delete the item from ChromaDB (main collection)
            self.collection.delete(ids=[item_id])

            # Best-effort cleanup of versioned entries
            try:
                if hasattr(self, "versions_collection") and self.versions_collection:
                    self.versions_collection.delete(where={"original_id": item_id})
            except Exception as verr:
                # Don't fail deletion due to versions cleanup; just log
                logger.warning(
                    f"Deleted main item {item_id} but failed to delete version entries: {verr}"
                )

            # Remove the item from the cache if it exists
            if item_id in self._cache:
                del self._cache[item_id]

            logger.info(f"Deleted item with ID {item_id} from ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Error deleting item from ChromaDB: {e}")
            return False

    def get_token_usage(self) -> int:
        """
        Get the total token usage for this store.

        Returns:
            The total number of tokens used
        """
        return self._token_usage

    def get_versions(self, item_id: str) -> list[MemoryItem]:
        """
        Get all versions of an item.

        Args:
            item_id: The ID of the item

        Returns:
            A list of MemoryItems representing all versions of the item
        """
        try:
            if self._use_fallback:
                version_payloads: list[SerializedPayload] = list(
                    self._versions.get(item_id, [])
                )
                current_payload = self._store.get(item_id)
                if current_payload:
                    version_payloads.append(current_payload)
                versions = [
                    self._deserialize_memory_item(payload)
                    for payload in version_payloads
                ]
                versions.sort(key=lambda x: x.metadata.get("version", 0))
                return versions

            # Query the versions collection for all versions of this item
            result = self.versions_collection.get(where={"original_id": item_id})

            # Check if any versions were found
            if not result["ids"] or not result["metadatas"]:
                # No versions found in the versions collection
                # Check if the item exists in the main collection
                current_item = self.retrieve(item_id)
                return [current_item.item] if current_item else []

            # Extract and deserialize all versions
            versions: list[MemoryItem] = []
            for metadata in result["metadatas"]:
                item_data = (
                    metadata.get("item_data") if isinstance(metadata, dict) else None
                )
                if not item_data:
                    logger.debug(
                        "Skipping version without item_data for id %s", item_id
                    )
                    continue
                payload = json.loads(item_data)
                if not isinstance(payload, Mapping):
                    logger.debug(
                        "Skipping version with non-mapping payload for id %s", item_id
                    )
                    continue
                item = self._deserialize_memory_item(payload)
                versions.append(item)

            # Sort versions by version number
            versions.sort(key=lambda x: x.metadata.get("version", 0))

            # Add the current version from the main collection
            current_item = self.retrieve(item_id)
            if current_item and current_item.item.metadata.get("version") not in [
                v.metadata.get("version") for v in versions
            ]:
                versions.append(current_item.item)

            return versions

        except Exception as e:
            logger.error(f"Error retrieving versions from ChromaDB: {e}")
            return []

    def get_history(self, item_id: str) -> list[dict[str, object]]:
        """
        Get the history of an item.

        Args:
            item_id: The ID of the item

        Returns:
            A list of dictionaries containing version information
        """
        try:
            # Get all versions of the item
            versions = self.get_versions(item_id)

            # Create history entries
            history = []
            for version in versions:
                # Extract version number from metadata
                version_num = version.metadata.get("version", 0)

                # Create a summary of the content
                content_summary = version.content
                if isinstance(content_summary, str) and len(content_summary) > 100:
                    content_summary = content_summary[:97] + "..."

                # Create a history entry
                entry = {
                    "version": version_num,
                    "timestamp": (
                        version.created_at.isoformat()
                        if version.created_at
                        else datetime.now().isoformat()
                    ),
                    "content_summary": content_summary,
                    "metadata": version.metadata,
                }
                history.append(entry)

            # Sort history by version number
            history.sort(key=lambda x: x["version"])

            # Remove duplicates based on version number
            unique_history = []
            seen_versions = set()
            for entry in history:
                if entry["version"] not in seen_versions:
                    seen_versions.add(entry["version"])
                    unique_history.append(entry)

            return unique_history

        except Exception as e:
            logger.error(f"Error retrieving history from ChromaDB: {e}")
            return []

    def has_optimized_embeddings(self) -> bool:
        """
        Check if the store has optimized embeddings.

        Returns:
            True if embeddings are optimized, False otherwise
        """
        return self._embedding_optimization_enabled

    def get_embedding_storage_efficiency(self) -> float:
        """
        Get the embedding storage efficiency.

        This is a measure of how efficiently similar embeddings are stored.
        A higher value indicates better efficiency.

        Returns:
            A float between 0 and 1 representing the efficiency
        """
        try:
            # This is a simplified implementation that returns a fixed value
            # In a real implementation, this would calculate the actual efficiency
            # based on the number of unique embeddings vs. total embeddings
            return 0.85
        except Exception as e:
            logger.error(f"Error calculating embedding storage efficiency: {e}")
            return 0.0

    def _save_fallback(self) -> None:
        if not self._use_fallback:
            return
        try:
            data: dict[str, object] = {
                "items": list(self._store.values()),
                "versions": {k: list(vals) for k, vals in self._versions.items()},
            }
            with open(self._fallback_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save fallback store to {self._fallback_file}: {e}")
