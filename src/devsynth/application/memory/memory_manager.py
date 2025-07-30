"""
Memory Manager Module

This module provides a unified interface to different memory adapters,
allowing for efficient querying of different types of memory and tagging
items with EDRR phases.
"""

from typing import Dict, List, Any, Optional, Union
from .adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from ...domain.models.memory import (
    MemoryItem,
    MemoryType,
    MemoryItemType,
    MemoryVector,
)
from ...domain.interfaces.memory import MemoryStore, VectorStore
from ...logging_setup import DevSynthLogger
from .query_router import QueryRouter
from .sync_manager import SyncManager

logger = DevSynthLogger(__name__)


class MemoryManager:
    """
    Memory Manager provides a unified interface to different memory adapters.

    It allows for efficient querying of different types of memory and tagging
    items with EDRR phases.
    """

    def __init__(
        self,
        adapters: Union[Dict[str, Any], Any] = None,
        query_router: QueryRouter | None = None,
        sync_manager: SyncManager | None = None,
        embedding_provider: Any | None = None,
    ):
        """
        Initialize the Memory Manager with the specified adapters.

        Args:
            adapters: Dictionary of adapters with keys 'graph', 'vector', 'tinydb',
                     or a single adapter that will be used as the default
        """
        if adapters is None:
            # Provide a simple default adapter so unit tests and basic usage work
            # without explicit configuration.
            self.adapters = {"tinydb": TinyDBMemoryAdapter()}
        elif isinstance(adapters, dict):
            self.adapters = adapters
        else:
            # If a single adapter is provided, use it as the default adapter
            self.adapters = {"default": adapters}

        logger.info(
            f"Memory Manager initialized with adapters: {', '.join(self.adapters.keys())}"
        )

        # Initialize helpers
        self.query_router = query_router or QueryRouter(self)
        self.sync_manager = sync_manager or SyncManager(self)
        self.embedding_provider = embedding_provider

    def _embed_text(self, text: str, dimension: int = 5) -> List[float]:
        """Return an embedding for ``text``.

        If an ``embedding_provider`` was supplied during initialization this
        method delegates to ``embedding_provider.embed`` and falls back to a
        deterministic embedding on error.  The fallback keeps unit tests
        hermetic when no external provider is available.
        """
        if self.embedding_provider is not None:
            try:
                result = self.embedding_provider.embed(text)
                if isinstance(result, list) and result and isinstance(result[0], list):
                    return result[0]
                return result
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Embedding provider failed: %s; falling back to deterministic embedding",
                    exc,
                )

        if not text:
            return [0.0] * dimension

        vector = [0.0] * dimension
        for idx, char in enumerate(text):
            vector[idx % dimension] += float(ord(char))

        length = float(len(text))
        return [v / length for v in vector]

    def store_with_edrr_phase(
        self,
        content: Any,
        memory_type: MemoryType,
        edrr_phase: str,
        metadata: Dict[str, Any] = None,
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
            metadata = {}
        metadata["edrr_phase"] = edrr_phase

        # Create the memory item
        memory_item = MemoryItem(
            id="", content=content, memory_type=memory_type, metadata=metadata
        )

        # Store in the appropriate adapter
        # Prefer Graph for EDRR phases due to relationship tracking capabilities,
        # then TinyDB for structured data, then default to first available
        if "graph" in self.adapters:
            return self.adapters["graph"].store(memory_item)
        elif "tinydb" in self.adapters:
            return self.adapters["tinydb"].store(memory_item)
        elif self.adapters:
            # Use the first available adapter
            adapter_name = next(iter(self.adapters))
            return self.adapters[adapter_name].store(memory_item)
        else:
            raise ValueError("No adapters available for storing memory items")

    def retrieve_with_edrr_phase(
        self,
        item_type: str,
        edrr_phase: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Any:
        """Retrieve an item stored with a specific EDRR phase.

        This helper iterates over available adapters and returns the first match
        found. It is intentionally simple so unit tests remain hermetic.

        Args:
            item_type: Identifier of the stored item.
            edrr_phase: The phase tag used during storage.
            metadata: Optional additional metadata for adapter queries.

        Returns:
            The retrieved item or an empty dictionary if not found.
        """
        search_meta = metadata.copy() if metadata else {}
        search_meta["edrr_phase"] = edrr_phase

        for adapter in self.adapters.values():
            if hasattr(adapter, "retrieve_with_edrr_phase"):
                item = adapter.retrieve_with_edrr_phase(
                    item_type, edrr_phase, search_meta
                )
                if item is not None:
                    return item
            if hasattr(adapter, "retrieve"):
                item = adapter.retrieve(item_type)
                if (
                    item is not None
                    and getattr(item, "metadata", {}).get("edrr_phase") == edrr_phase
                ):
                    return getattr(item, "content", item)

        return {}

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        # Try to retrieve from each adapter
        for adapter_name, adapter in self.adapters.items():
            if hasattr(adapter, "retrieve"):
                item = adapter.retrieve(item_id)
                if item is not None:
                    return item

        return None

    def query_related_items(self, item_id: str) -> List[MemoryItem]:
        """
        Query for items related to a given item ID.

        Args:
            item_id: The ID of the item to find related items for

        Returns:
            A list of related memory items
        """
        if "graph" in self.adapters:
            # Use the graph adapter for relationship queries
            graph_adapter = self.adapters["graph"]
            return graph_adapter.query_related_items(item_id)
        else:
            logger.warning("Graph adapter not available for querying related items")
            return []

    def similarity_search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Union[MemoryItem, MemoryVector]]:
        """
        Perform a similarity search with a query embedding.

        Args:
            query_embedding: The query embedding
            top_k: The number of results to return

        Returns:
            A list of similar memory items or vectors
        """
        if "vector" in self.adapters:
            # Use the vector adapter for similarity search
            vector_adapter = self.adapters["vector"]
            return vector_adapter.similarity_search(query_embedding, top_k)
        else:
            logger.warning("Vector adapter not available for similarity search")
            return []

    def query_structured_data(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """
        Query structured data with a query dictionary.

        Args:
            query: The query dictionary

        Returns:
            A list of matching memory items
        """
        if "tinydb" in self.adapters:
            # Use the TinyDB adapter for structured data queries
            tinydb_adapter = self.adapters["tinydb"]
            return tinydb_adapter.query_structured_data(query)
        else:
            logger.warning("TinyDB adapter not available for querying structured data")
            return []

    def query_by_edrr_phase(self, edrr_phase: str) -> List[MemoryItem]:
        """
        Query memory items by EDRR phase.

        Args:
            edrr_phase: The EDRR phase to query for

        Returns:
            A list of memory items with the specified EDRR phase
        """
        results = []

        # Query each adapter for items with the specified EDRR phase
        for adapter_name, adapter in self.adapters.items():
            if hasattr(adapter, "search"):
                # Use the search method if available
                items = adapter.search({"edrr_phase": edrr_phase})
                results.extend(items)

        return results

    def query_evolution_across_edrr_phases(self, item_id: str) -> List[MemoryItem]:
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

        # Get the item and its related items
        graph_adapter = self.adapters["graph"]
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
        self, item_id: str, graph_adapter: Any
    ) -> List[MemoryItem]:
        """
        Get all items related to the given item ID recursively.

        Args:
            item_id: The ID of the item to find related items for
            graph_adapter: The graph adapter to use

        Returns:
            A list of related memory items
        """
        related_items = graph_adapter.query_related_items(item_id)
        result = []

        for item in related_items:
            result.append(item)
            # Recursively get related items, but avoid cycles
            if item.id != item_id:
                result.extend(self._get_all_related_items(item.id, graph_adapter))

        return result

    def store_item(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item.

        Args:
            memory_item: The memory item to store

        Returns:
            The ID of the stored memory item
        """
        # Store in the appropriate adapter
        # Prefer TinyDB for structured data, then Graph for relationships, then default to first available
        if "tinydb" in self.adapters:
            return self.adapters["tinydb"].store(memory_item)
        elif "graph" in self.adapters:
            return self.adapters["graph"].store(memory_item)
        elif self.adapters:
            # Use the first available adapter
            adapter_name = next(iter(self.adapters))
            return self.adapters[adapter_name].store(memory_item)
        else:
            raise ValueError("No adapters available for storing memory items")

    def query_by_type(self, memory_type: MemoryType) -> List[MemoryItem]:
        """
        Query memory items by type.

        Args:
            memory_type: The memory type to query for

        Returns:
            A list of memory items with the specified type
        """
        results = []

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

    def query_by_metadata(self, metadata: Dict[str, Any]) -> List[MemoryItem]:
        """
        Query memory items by metadata.

        Args:
            metadata: The metadata to query for

        Returns:
            A list of memory items with the specified metadata
        """
        results = []

        # Query each adapter for items with the specified metadata
        for adapter_name, adapter in self.adapters.items():
            if hasattr(adapter, "query_by_metadata"):
                # Use the query_by_metadata method if available
                items = adapter.query_by_metadata(metadata)
                results.extend(items)
            elif hasattr(adapter, "search"):
                # Use the search method if available
                items = adapter.search(metadata)
                results.extend(items)
            elif hasattr(adapter, "get_all"):
                # Use the get_all method if available and filter by metadata
                items = []
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
        memory_type: Any = None,
        metadata_filter: Dict[str, Any] = None,
        limit: int = 10,
    ) -> List[MemoryVector]:
        """
        Search memory items using the configured vector store.

        This implementation performs a lightweight semantic search by creating a
        simple embedding for ``query`` and delegating the search to the
        configured :class:`VectorStore`.  Results can optionally be filtered by
        ``memory_type`` and additional metadata.

        Args:
            query: The query string
            memory_type: The type of memory to filter by (``MemoryType`` or str)
            metadata_filter: Optional metadata key/value pairs to match
            limit: Maximum number of results to return

        Returns:
            A list of matching memory vectors ordered by similarity
        """
        memory_type_str = memory_type
        if hasattr(memory_type, "value"):
            memory_type_str = memory_type.value
        elif hasattr(memory_type, "name"):
            memory_type_str = memory_type.name

        logger.info(
            f"Searching memory with query: {query}, type: {memory_type_str}, filter: {metadata_filter}, limit: {limit}"
        )

        if "vector" not in self.adapters:
            logger.warning("Vector adapter not available for semantic search")
            return []

        vector_adapter: VectorStore = self.adapters["vector"]

        query_embedding = self._embed_text(query)

        results = vector_adapter.similarity_search(query_embedding, top_k=limit)

        filtered: List[MemoryVector] = []
        for vector in results:
            if memory_type is not None:
                expected = (
                    memory_type.value
                    if hasattr(memory_type, "value")
                    else str(memory_type)
                )
                actual = vector.metadata.get("memory_type")
                if hasattr(actual, "value"):
                    actual = actual.value
                if actual != expected:
                    continue

            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    if vector.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            filtered.append(vector)
            if len(filtered) >= limit:
                break

        return filtered

    def store(self, memory_item: MemoryItem, **kwargs) -> str:
        """
        Store a memory item. This is an alias for store_item for backward compatibility.

        Args:
            memory_item: The memory item to store
            **kwargs: Additional keyword arguments

        Returns:
            The ID of the stored memory item
        """
        return self.store_item(memory_item)

    def query(self, query_string: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Query memory items using a query string.

        This is a simplified implementation that delegates to search_memory.

        Args:
            query_string: The query string
            **kwargs: Additional keyword arguments for filtering

        Returns:
            A list of memory items matching the query
        """
        logger.info(f"Querying memory with: {query_string}")
        return self.search_memory(query_string, **kwargs)

    def route_query(
        self,
        query: str,
        *,
        store: str | None = None,
        strategy: str = "direct",
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Route a query through the :class:`QueryRouter`."""

        return self.query_router.route(
            query, store=store, strategy=strategy, context=context
        )

    def synchronize(
        self, source_store: str, target_store: str, bidirectional: bool = False
    ) -> Dict[str, int]:
        """Synchronize two stores using the :class:`SyncManager`."""

        return self.sync_manager.synchronize(source_store, target_store, bidirectional)

    # ------------------------------------------------------------------
    def cross_store_query(
        self, query: str, stores: Optional[List[str]] | None = None
    ) -> Dict[str, List[Any]]:
        """Query multiple stores using the :class:`SyncManager`."""

        return self.sync_manager.cross_store_query(query, stores)

    def begin_transaction(self, stores: List[str]):
        """Begin a multi-store transaction."""

        return self.sync_manager.transaction(stores)

    def update_item(self, store: str, item: MemoryItem) -> bool:
        """Update an item and propagate to other stores."""

        return self.sync_manager.update_item(store, item)

    def queue_update(self, store: str, item: MemoryItem) -> None:
        """Queue an update for asynchronous propagation."""

        self.sync_manager.queue_update(store, item)

    def flush_updates(self) -> None:
        """Flush queued updates synchronously."""

        self.sync_manager.flush_queue()

    async def flush_updates_async(self) -> None:
        """Flush queued updates asynchronously."""

        await self.sync_manager.flush_queue_async()

    async def wait_for_sync(self) -> None:
        """Wait for asynchronous sync tasks to complete."""

        await self.sync_manager.wait_for_async()

    def get_sync_stats(self) -> Dict[str, int]:
        """Return statistics about synchronization operations."""

        return self.sync_manager.get_sync_stats()

    def retrieve_relevant_knowledge(
        self,
        task: Dict[str, Any],
        retrieval_strategy: str = "broad",
        max_results: int = 5,
        similarity_threshold: float = 0.5,
    ) -> List[Any]:
        """Retrieve knowledge relevant to the provided task.

        This default implementation returns an empty list, allowing tests to
        override the behaviour with mocks while keeping the interface stable.
        """

        return []

    def retrieve_historical_patterns(self) -> List[Any]:
        """Return historical patterns stored in memory.

        The base implementation returns an empty list so that unit tests remain
        hermetic without requiring persistent storage.
        """

        return []
