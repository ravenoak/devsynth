"""
Memory Manager Module

This module provides a unified interface to different memory adapters,
allowing for efficient querying of different types of memory and tagging
items with EDRR phases.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Protocol

from ...config import get_settings
from ...domain.interfaces.memory import MemoryStore
from ...domain.models.memory import MemoryItem, MemoryItemType, MemoryType
from ...exceptions import CircuitBreakerOpenError, MemoryTransactionError
from ...logging_setup import DevSynthLogger
from .adapter_types import (
    AdapterRegistry,
    MemoryAdapter,
    SupportsEdrrRetrieval,
    SupportsGraphQueries,
    SupportsRetrieve,
    SupportsSearch,
    SupportsStructuredQuery,
)
from .adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from .vector_protocol import VectorStoreProtocol

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .adapters.s3_memory_adapter import S3MemoryAdapter

from .circuit_breaker import (
    CircuitBreaker,
    circuit_breaker_registry,
    with_circuit_breaker,
)
from .dto import (
    GroupedMemoryResults,
    MemoryMetadata,
    MemoryMetadataValue,
    MemoryQueryResults,
    MemoryRecord,
    MemoryRecordInput,
    MemorySearchQuery,
    build_memory_record,
    build_query_results,
)
from .error_logger import ErrorRecord, ErrorSummary, memory_error_logger
from .query_router import QueryRouter
from .retry import retry_memory_operation, retry_with_backoff
from .sync_manager import SyncManager
from .transaction_context import TransactionContext

logger = DevSynthLogger(__name__)


def _build_s3_adapter(bucket: str) -> MemoryAdapter | None:
    """Return an instantiated S3 adapter when the optional dependency exists."""

    try:  # pragma: no cover - optional dependency import
        from .adapters.s3_memory_adapter import S3MemoryAdapter as RuntimeS3Adapter
    except Exception as exc:  # pragma: no cover - defensive logging for CI
        logger.debug("S3 adapter unavailable: %s", exc)
        return None

    try:
        return RuntimeS3Adapter(bucket)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to init S3MemoryAdapter: %s", exc)
        return None


class EmbeddingProvider(Protocol):
    """Structural protocol for embedding providers."""

    def embed(
        self, text: str
    ) -> Sequence[float] | Sequence[Sequence[float]]:  # pragma: no cover - protocol
        ...


class SyncHook(Protocol):
    """Callable invoked after synchronization events."""

    def __call__(
        self, item: MemoryItem | None, /
    ) -> None:  # pragma: no cover - protocol
        ...


class MemoryManager:
    """
    Memory Manager provides a unified interface to different memory adapters.

    It allows for efficient querying of different types of memory and tagging
    items with EDRR phases.
    """

    def __init__(
        self,
        adapters: Mapping[str, MemoryAdapter] | MemoryAdapter | None = None,
        query_router: QueryRouter | None = None,
        sync_manager: SyncManager | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        """
        Initialize the Memory Manager with the specified adapters.

        Args:
            adapters: Dictionary of adapters with keys 'graph', 'vector', 'tinydb',
                     or a single adapter that will be used as the default
        """
        self.adapters: AdapterRegistry

        if adapters is None:
            settings = get_settings()
            store_type = os.getenv(
                "DEVSYNTH_MEMORY_STORE",
                getattr(settings, "memory_store_type", "tinydb"),
            ).lower()
            if store_type == "s3":
                bucket = os.getenv(
                    "DEVSYNTH_S3_BUCKET",
                    getattr(settings, "s3_bucket_name", "devsynth-memory"),
                )
                adapter = _build_s3_adapter(bucket)
                if adapter is not None:
                    self.adapters = {"s3": adapter}
                else:
                    self.adapters = {"tinydb": TinyDBMemoryAdapter()}
            else:
                # Default to TinyDB for simple usage and unit tests
                self.adapters = {"tinydb": TinyDBMemoryAdapter()}
        elif isinstance(adapters, Mapping):
            self.adapters = dict(adapters)
        else:
            # If a single adapter is provided, use it as the default adapter
            self.adapters = {"default": adapters}

        logger.info(
            f"Memory Manager initialized with adapters: {', '.join(self.adapters.keys())}"
        )

        # Initialize helpers
        self.query_router = query_router or QueryRouter(self)
        self.sync_manager = sync_manager or SyncManager(self)
        self.embedding_provider: EmbeddingProvider | None = embedding_provider
        # Registered hooks called after synchronization events
        self._sync_hooks: list[SyncHook] = []

    def register_sync_hook(self, hook: SyncHook) -> None:
        """Register a callback invoked after memory synchronization."""

        self._sync_hooks.append(hook)

    def _notify_sync_hooks(self, item: MemoryItem | None) -> None:
        """Invoke registered synchronization hooks with ``item``."""

        for hook in list(self._sync_hooks):
            try:
                hook(item)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(f"Sync hook failed: {exc}")

    @lru_cache(maxsize=128)
    def _cached_embedding(self, text: str, dimension: int) -> tuple[float, ...]:
        """Return a cached embedding for ``text``.

        The result is cached to avoid recomputing embeddings for repeated
        inputs, improving performance especially when an external provider is
        used.
        """
        if self.embedding_provider is not None:
            try:
                result = self.embedding_provider.embed(text)
                if isinstance(result, list) and result and isinstance(result[0], list):
                    result = result[0]
                return tuple(float(value) for value in result)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Embedding provider failed: %s; falling back to deterministic embedding",
                    exc,
                )

        if not text:
            return tuple([0.0] * dimension)

        vector = [0.0] * dimension
        for idx, char in enumerate(text):
            vector[idx % dimension] += float(ord(char))

        length = float(len(text))
        return tuple(v / length for v in vector)

    def _embed_text(self, text: str, dimension: int = 5) -> list[float]:
        """Return an embedding for ``text`` using an LRU cache."""
        return list(self._cached_embedding(text, dimension))

    def store_with_edrr_phase(
        self,
        content: MemoryMetadataValue,
        memory_type: MemoryType,
        edrr_phase: str,
        metadata: MemoryMetadata | None = None,
    ) -> str:
        """
        Store a memory item with an EDRR phase.

        Args:
            content: The content of the memory item
            memory_type: The type of memory (e.g., CODE, REQUIREMENT)
            edrr_phase: The EDRR phase (EXPAND, DIFFERENTIATE, REFINE, RETROSPECT)
            metadata: Additional metadata for the memory item

        Returns:
            The ID of the stored memory item
        """
        # Create metadata with EDRR phase
        if metadata is None:
            metadata_payload: dict[str, MemoryMetadataValue] = {}
        else:
            metadata_payload = dict(metadata)
        metadata_payload["edrr_phase"] = edrr_phase

        # Create the memory item
        memory_item = MemoryItem(
            id="",
            content=content,
            memory_type=memory_type,
            metadata=metadata_payload,
        )

        # Determine primary store preference order
        if not self.adapters:
            raise ValueError("No adapters available for storing memory items")

        if "graph" in self.adapters:
            primary_store = "graph"
        elif "tinydb" in self.adapters:
            primary_store = "tinydb"
        else:
            primary_store = next(iter(self.adapters))

        # Use the sync manager to propagate to all stores
        self.sync_manager.update_item(primary_store, memory_item)
        return memory_item.id

    def retrieve_with_edrr_phase(
        self,
        item_type: MemoryType | str,
        edrr_phase: str,
        metadata: MemoryMetadata | None = None,
    ) -> MemoryRecord | None:
        """Retrieve an item stored with a specific EDRR phase.

        This helper iterates over available adapters and returns the first match
        found. Results are normalized into :class:`MemoryRecord` instances so
        downstream callers can rely on DTO semantics regardless of the adapter
        implementation.

        Args:
            item_type: Identifier of the stored item as a :class:`MemoryType` or
                a compatible raw value.
            edrr_phase: The phase tag used during storage.
            metadata: Optional additional metadata for adapter queries.

        Returns:
            A normalized memory record or ``None`` if not found.
        """

        normalized_type = (
            item_type
            if isinstance(item_type, MemoryType)
            else MemoryType.from_raw(item_type)
        )
        search_meta: dict[str, MemoryMetadataValue] = dict(metadata) if metadata else {}
        search_meta["edrr_phase"] = edrr_phase

        for adapter_name, adapter in self.adapters.items():
            if isinstance(adapter, SupportsEdrrRetrieval):
                item = adapter.retrieve_with_edrr_phase(
                    normalized_type, edrr_phase, search_meta
                )
                if item is not None:
                    return build_memory_record(item, source=adapter_name)
            if isinstance(adapter, SupportsRetrieve):
                artefact = adapter.retrieve(normalized_type.value)
                if artefact is None:
                    continue
                record = build_memory_record(artefact, source=adapter_name)
                if record.metadata.get("edrr_phase") == edrr_phase:
                    return record

        return None

    @retry_memory_operation(max_retries=3, initial_backoff=0.1, max_backoff=2.0)
    def retrieve(self, item_id: str) -> MemoryItem | None:
        """
        Retrieve a memory item by ID.

        This method uses retry with exponential backoff to improve reliability
        when retrieving items from memory adapters. It will try each adapter
        in turn, and if all fail, it will return None.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        # Try to retrieve from each adapter
        errors: dict[str, str] = {}
        for adapter_name, adapter in self.adapters.items():
            if not isinstance(adapter, SupportsRetrieve):
                continue
            try:
                # Use circuit breaker to protect the retrieve operation
                circuit = circuit_breaker_registry.get_or_create(
                    f"memory_retrieve_{adapter_name}",
                    failure_threshold=3,
                    reset_timeout=60.0,
                )

                item = circuit.execute(adapter.retrieve, item_id)
                if item is not None and isinstance(item, MemoryItem):
                    return item
                if item is not None:
                    return build_memory_record(item, source=adapter_name).item
            except CircuitBreakerOpenError as e:
                # Circuit is open, log and continue to next adapter
                logger.warning(
                    f"Circuit breaker for {adapter_name} is open, skipping: {e}"
                )
                errors[adapter_name] = f"Circuit breaker open: {e}"

                # Log to error logger
                memory_error_logger.log_error(
                    operation="retrieve",
                    adapter_name=adapter_name,
                    error=e,
                    context={"item_id": item_id, "circuit_breaker": True},
                )
            except Exception as e:
                # Retrieve operation failed, log and continue to next adapter
                logger.error(f"Failed to retrieve memory item from {adapter_name}: {e}")
                errors[adapter_name] = str(e)

                # Log to error logger
                memory_error_logger.log_error(
                    operation="retrieve",
                    adapter_name=adapter_name,
                    error=e,
                    context={"item_id": item_id},
                )

        if errors:
            logger.warning(
                f"Failed to retrieve item {item_id} from any adapter: {errors}"
            )

        return None

    def query_related_items(self, item_id: str) -> list[MemoryItem]:
        """
        Query for items related to a given item ID.

        Args:
            item_id: The ID of the item to find related items for

        Returns:
            A list of related memory items
        """
        if "graph" in self.adapters:
            graph_adapter = self.adapters["graph"]
            if isinstance(graph_adapter, SupportsGraphQueries):
                return list(graph_adapter.query_related_items(item_id))
            logger.warning("Graph adapter missing relationship API")
            return []
        logger.warning("Graph adapter not available for querying related items")
        return []

    def similarity_search(
        self, query_embedding: Sequence[float], top_k: int = 5
    ) -> list[MemoryRecord]:
        """Perform a similarity search and normalize results into DTOs."""

        if "vector" in self.adapters:
            vector_adapter = self.adapters["vector"]
            if isinstance(vector_adapter, VectorStoreProtocol):
                results = vector_adapter.similarity_search(query_embedding, top_k)
                return [
                    build_memory_record(candidate, source="vector")
                    for candidate in results
                ]

        logger.warning("Vector adapter not available for similarity search")
        return []

    def query_structured_data(self, query: MemorySearchQuery) -> MemoryQueryResults:
        """Query structured data and return a :class:`MemoryQueryResults` DTO."""

        if "tinydb" in self.adapters:
            tinydb_adapter = self.adapters["tinydb"]
            if isinstance(tinydb_adapter, SupportsStructuredQuery):
                raw = tinydb_adapter.query_structured_data(query)
            else:
                raw = []
            return build_query_results("tinydb", raw)

        logger.warning("TinyDB adapter not available for querying structured data")
        return build_query_results("tinydb", [])

    def query_by_edrr_phase(self, edrr_phase: str) -> list[MemoryRecord]:
        """Query memory items by EDRR phase and normalize the results."""

        records: list[MemoryRecord] = []

        for adapter_name, adapter in self.adapters.items():
            if not isinstance(adapter, SupportsSearch):
                continue
            items = adapter.search({"edrr_phase": edrr_phase})
            records.extend(
                build_memory_record(item, source=adapter_name) for item in items
            )

        return records

    def query_evolution_across_edrr_phases(self, item_id: str) -> list[MemoryItem]:
        """
        Query for the evolution of an item across EDRR phases.

        Args:
            item_id: The ID of the item to find evolution for

        Returns:
            A list of related memory items in EDRR phase order
        """
        if "graph" not in self.adapters:
            logger.warning(
                "Graph adapter not available for querying evolution across EDRR phases"
            )
            return []

        graph_adapter = self.adapters["graph"]
        if not isinstance(graph_adapter, SupportsGraphQueries) or not isinstance(
            graph_adapter, SupportsRetrieve
        ):
            logger.warning("Graph adapter missing retrieval or relationship support")
            return []

        item = graph_adapter.retrieve(item_id)
        if item is None:
            return []

        # Get all related items recursively
        related_items = self._get_all_related_items(item_id, graph_adapter)

        # Add the original item
        all_items = [item] + related_items

        # Sort by EDRR phase
        edrr_order = {"EXPAND": 0, "DIFFERENTIATE": 1, "REFINE": 2, "RETROSPECT": 3}
        sorted_items = sorted(
            all_items,
            key=lambda x: edrr_order.get(x.metadata.get("edrr_phase", ""), 999),
        )

        return sorted_items

    def _get_all_related_items(
        self, item_id: str, graph_adapter: SupportsGraphQueries
    ) -> list[MemoryItem]:
        """
        Get all items related to the given item ID recursively.

        Args:
            item_id: The ID of the item to find related items for
            graph_adapter: The graph adapter to use

        Returns:
            A list of related memory items
        """
        related_items = list(graph_adapter.query_related_items(item_id))
        result: list[MemoryItem] = []

        for item in related_items:
            result.append(item)
            # Recursively get related items, but avoid cycles
            if item.id != item_id:
                result.extend(self._get_all_related_items(item.id, graph_adapter))

        return result

    def store_item(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item.

        This method uses the circuit breaker pattern to protect against failures
        when storing items in memory adapters. If the primary adapter fails,
        it will try fallback adapters in order of preference.

        Args:
            memory_item: The memory item to store

        Returns:
            The ID of the stored memory item

        Raises:
            ValueError: If no adapters are available for storing memory items
            MemoryTransactionError: If all adapters fail to store the item
        """
        # Define adapter preference order
        adapter_preference = ["tinydb", "graph"]

        # Add any other adapters not in the preference list
        for adapter_name in self.adapters:
            if adapter_name not in adapter_preference:
                adapter_preference.append(adapter_name)

        if not adapter_preference:
            raise ValueError("No adapters available for storing memory items")

        # Try adapters in order of preference
        errors: dict[str, str] = {}
        for adapter_name in adapter_preference:
            if adapter_name not in self.adapters:
                continue

            adapter = self.adapters[adapter_name]
            circuit = circuit_breaker_registry.get_or_create(
                f"memory_store_{adapter_name}", failure_threshold=3, reset_timeout=60.0
            )

            try:
                # Use the circuit breaker to protect the store operation
                # Check if adapter supports MemoryStore protocol (has store method)
                if hasattr(adapter, 'store'):
                    return circuit.execute(adapter.store, memory_item)
                else:
                    # Skip vector adapters for MemoryItem storage
                    logger.debug(f"Skipping vector adapter {adapter_name} for MemoryItem storage")
                    continue
            except CircuitBreakerOpenError as e:
                # Circuit is open, log and continue to next adapter
                logger.warning(
                    f"Circuit breaker for {adapter_name} is open, skipping: {e}"
                )
                errors[adapter_name] = f"Circuit breaker open: {e}"

                # Log to error logger
                memory_error_logger.log_error(
                    operation="store_item",
                    adapter_name=adapter_name,
                    error=e,
                    context={"item_id": memory_item.id, "circuit_breaker": True},
                )
            except Exception as e:
                # Store operation failed, log and continue to next adapter
                logger.error(f"Failed to store memory item in {adapter_name}: {e}")
                errors[adapter_name] = str(e)

                # Log to error logger
                memory_error_logger.log_error(
                    operation="store_item",
                    adapter_name=adapter_name,
                    error=e,
                    context={"item_id": memory_item.id},
                )

        # If we get here, all adapters failed
        error_msg = f"Failed to store memory item in any adapter: {errors}"
        logger.error(error_msg)
        raise MemoryTransactionError(error_msg, operation="store_item")

    def query_by_type(self, memory_type: MemoryType) -> list[MemoryItem]:
        """
        Query memory items by type.

        Args:
            memory_type: The memory type to query for

        Returns:
            A list of memory items with the specified type
        """
        results: list[MemoryItem] = []

        # Query each adapter for items with the specified type
        for adapter_name, adapter in self.adapters.items():
            if hasattr(adapter, "query_by_type"):
                # Use the query_by_type method if available
                items = adapter.query_by_type(memory_type)
                results.extend(items)
            elif hasattr(adapter, "search"):
                # Use the search method if available
                # Convert memory_type to string value if it's an enum
                memory_type_value = (
                    memory_type.value if hasattr(memory_type, "value") else memory_type
                )
                items = adapter.search({"memory_type": memory_type_value})
                results.extend(items)
            elif hasattr(adapter, "get_all"):
                # Use the get_all method if available and filter by type
                items = [
                    item
                    for item in adapter.get_all()
                    if item.memory_type == memory_type
                ]
                results.extend(items)

        return results

    def query_by_metadata(
        self, metadata: Mapping[str, MemoryMetadataValue]
    ) -> list[MemoryItem]:
        """
        Query memory items by metadata.

        Args:
            metadata: The metadata to query for

        Returns:
            A list of memory items with the specified metadata
        """
        results: list[MemoryItem] = []

        # Query each adapter for items with the specified metadata
        for adapter_name, adapter in self.adapters.items():
            if hasattr(adapter, "query_by_metadata"):
                # Use the query_by_metadata method if available
                items = adapter.query_by_metadata(metadata)
                results.extend(items)
            elif hasattr(adapter, "search"):
                # Use the search method if available
                items = adapter.search(dict(metadata))
                results.extend(items)
            elif hasattr(adapter, "get_all"):
                # Use the get_all method if available and filter by metadata
                items: list[MemoryItem] = []
                for item in adapter.get_all():
                    if all(
                        item.metadata.get(key) == value
                        for key, value in metadata.items()
                    ):
                        items.append(item)
                results.extend(items)

        return results

    def search_memory(
        self,
        query: str,
        memory_type: MemoryType | str | None = None,
        metadata_filter: MemoryMetadata | None = None,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        """Search memory items and return normalized :class:`MemoryRecord` values."""
        if isinstance(memory_type, MemoryType):
            memory_type_str: str | None = memory_type.value
        elif isinstance(memory_type, str):
            memory_type_str = memory_type
        elif memory_type is None:
            memory_type_str = None
        else:
            memory_type_str = str(memory_type)

        logger.info(
            f"Searching memory with query: {query}, type: {memory_type_str}, filter: {metadata_filter}, limit: {limit}"
        )

        if "vector" not in self.adapters:
            logger.info("Vector adapter not available; using keyword fallback search")
            aggregated: list[MemoryRecord] = []

            def maybe_add(item: MemoryRecordInput, store_name: str) -> None:
                record = build_memory_record(item, source=store_name)
                try:
                    content_text = str(record.content or "")
                except Exception:
                    content_text = ""
                if query and query.lower() not in content_text.lower():
                    return
                aggregated.append(record)

            for store_name, adapter in self.adapters.items():
                if hasattr(adapter, "get_all"):
                    try:
                        for it in adapter.get_all():
                            maybe_add(it, store_name)
                    except Exception:
                        continue
                elif hasattr(adapter, "search"):
                    try:
                        for it in adapter.search({}):
                            maybe_add(it, store_name)
                    except Exception:
                        continue

            filtered: list[MemoryRecord] = []
            for record in aggregated:
                metadata = record.item.metadata or {}
                if memory_type_str is not None:
                    expected = memory_type_str
                    actual = metadata.get("memory_type")
                    if hasattr(actual, "value"):
                        actual = actual.value
                    if actual != expected:
                        continue
                if metadata_filter:
                    ok = True
                    for k, v in metadata_filter.items():
                        if metadata.get(k) != v:
                            ok = False
                            break
                    if not ok:
                        continue
                filtered.append(record)
                if len(filtered) >= limit:
                    break
            return filtered

        vector_adapter = self.adapters.get("vector")
        if not isinstance(vector_adapter, VectorStoreProtocol):
            logger.warning("Vector adapter not available for vector similarity search")
            return []

        query_embedding = self._embed_text(query)

        results = vector_adapter.similarity_search(query_embedding, top_k=limit)

        filtered: list[MemoryRecord] = []
        for candidate in results:
            record = build_memory_record(candidate, source="vector")
            metadata = record.item.metadata or {}
            if memory_type_str is not None:
                expected = memory_type_str
                actual = metadata.get("memory_type")
                if hasattr(actual, "value"):
                    actual = actual.value
                if actual != expected:
                    continue

            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    if metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            filtered.append(record)
            if len(filtered) >= limit:
                break

        return filtered

    def store(self, memory_item: MemoryItem, **_: object) -> str:
        """
        Store a memory item. This is an alias for store_item for backward compatibility.

        Args:
            memory_item: The memory item to store
            **kwargs: Additional keyword arguments

        Returns:
            The ID of the stored memory item
        """
        return self.store_item(memory_item)

    def query(
        self,
        query_string: str,
        *,
        memory_type: MemoryType | str | None = None,
        metadata_filter: MemoryMetadata | None = None,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        """Delegate to :meth:`search_memory` and return normalized records."""

        logger.info(f"Querying memory with: {query_string}")
        return self.search_memory(
            query_string,
            memory_type=memory_type,
            metadata_filter=metadata_filter,
            limit=limit,
        )

    def route_query(
        self,
        query: str,
        *,
        store: str | None = None,
        strategy: str = "direct",
        context: Mapping[str, MemoryMetadataValue] | None = None,
        stores: Sequence[str] | None = None,
    ) -> MemoryQueryResults | GroupedMemoryResults | list[MemoryRecord]:
        """Route a query through the :class:`QueryRouter`."""

        context_payload: MemoryMetadata | None = (
            dict(context) if context is not None else None
        )
        return self.query_router.route(
            query,
            store=store,
            strategy=strategy,
            context=context_payload,
            stores=list(stores) if stores is not None else None,
        )

    def synchronize(
        self, source_store: str, target_store: str, bidirectional: bool = False
    ) -> dict[str, int]:
        """Synchronize two stores using the :class:`SyncManager`."""

        return self.sync_manager.synchronize(source_store, target_store, bidirectional)

    def synchronize_core_stores(self) -> dict[str, int]:
        """Synchronize LMDB and FAISS stores into the Kuzu store."""

        return self.sync_manager.synchronize_core()

    # ------------------------------------------------------------------
    def cross_store_query(
        self, query: str, stores: Sequence[str] | None = None
    ) -> GroupedMemoryResults:
        """Query multiple stores using the :class:`SyncManager`."""

        store_list = list(stores) if stores is not None else None
        return self.sync_manager.cross_store_query(query, store_list)

    def begin_transaction(
        self, stores: Sequence[str]
    ) -> AbstractContextManager[object]:
        """
        Begin a multi-store transaction.

        This method creates a transaction context that spans multiple memory adapters.
        It uses the TransactionContext class which implements a two-phase commit protocol
        for cross-store transactions.

        Args:
            stores: List of store names to include in the transaction

        Returns:
            A transaction context manager

        Example:
            ```python
            with memory_manager.begin_transaction(['graph', 'tinydb']):
                memory_manager.store_item(item1)
                memory_manager.store_item(item2)
            # Transaction is automatically committed if no exception occurs,
            # or rolled back if an exception is raised
            ```
        """
        # Get the adapters for the specified stores
        adapters: list[MemoryAdapter] = []
        for store_name in stores:
            adapter = self.adapters.get(store_name)
            if adapter:
                adapters.append(adapter)
            else:
                logger.warning(f"Store {store_name} not found, skipping")

        # If no valid adapters were found, fall back to the sync manager
        if not adapters:
            logger.warning(
                "No valid adapters found for transaction, falling back to sync manager"
            )
            return self.sync_manager.transaction(list(stores))

        # Create and return a transaction context
        return TransactionContext(adapters)

    def update_item(self, store: str, item: MemoryItem) -> bool:
        """Update an item and propagate to other stores."""

        return self.sync_manager.update_item(store, item)

    def queue_update(self, store: str, item: MemoryItem) -> None:
        """Queue an update for asynchronous propagation."""

        self.sync_manager.queue_update(store, item)

    def flush_updates(self) -> None:
        """Flush queued updates synchronously and persist adapters."""

        self.sync_manager.flush_queue()
        for adapter in self.adapters.values():
            try:
                if hasattr(adapter, "flush"):
                    adapter.flush()
                elif hasattr(adapter, "memory_store") and hasattr(
                    adapter.memory_store, "flush"
                ):
                    adapter.memory_store.flush()
            except Exception:
                logger.debug("Adapter flush failed", exc_info=True)

    async def flush_updates_async(self) -> None:
        """Flush queued updates asynchronously."""

        await self.sync_manager.flush_queue_async()

    async def wait_for_sync(self) -> None:
        """Wait for asynchronous sync tasks to complete."""

        await self.sync_manager.wait_for_async()

    def get_sync_stats(self) -> dict[str, int]:
        """Return statistics about synchronization operations."""

        return self.sync_manager.get_sync_stats()

    def retrieve_relevant_knowledge(
        self,
        task: Mapping[str, MemoryMetadataValue],
        retrieval_strategy: str = "broad",
        max_results: int = 5,
        similarity_threshold: float = 0.5,
    ) -> list[MemoryRecord]:
        """Retrieve knowledge relevant to the provided task.

        This default implementation returns an empty list, allowing tests to
        override the behaviour with mocks while keeping the interface stable.
        """

        return []

    def retrieve_historical_patterns(self) -> list[MemoryRecord]:
        """Return historical patterns stored in memory.

        The base implementation returns an empty list so that unit tests remain
        hermetic without requiring persistent storage.
        """

        return []

    def get_error_summary(self) -> ErrorSummary:
        """
        Get a summary of memory operation errors.

        This method provides statistics about errors that have occurred during
        memory operations, grouped by adapter, operation, and error type.

        Returns:
            A dictionary with error statistics
        """
        return memory_error_logger.get_error_summary()

    def get_recent_errors(
        self,
        operation: str | None = None,
        adapter_name: str | None = None,
        error_type: str | None = None,
        limit: int = 10,
    ) -> list[ErrorRecord]:
        """
        Get recent memory operation errors, optionally filtered by criteria.

        Args:
            operation: Filter by operation (e.g., "store", "retrieve")
            adapter_name: Filter by adapter name
            error_type: Filter by error type
            limit: Maximum number of errors to return

        Returns:
            A list of structured error entries
        """
        return memory_error_logger.get_recent_errors(
            operation=operation,
            adapter_name=adapter_name,
            error_type=error_type,
            limit=limit,
        )

    def clear_error_log(self) -> None:
        """
        Clear the in-memory error log.

        This method clears the in-memory error log, but does not affect
        persisted error logs on disk.
        """
        memory_error_logger.clear_errors()
