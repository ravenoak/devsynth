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
from .transaction_context import TransactionContext
from .circuit_breaker import CircuitBreaker, circuit_breaker_registry, with_circuit_breaker
from .retry import retry_with_backoff, retry_memory_operation
from .error_logger import memory_error_logger
from ...exceptions import CircuitBreakerOpenError, MemoryTransactionError

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
        query_router: Union[QueryRouter, None] = None,
        sync_manager: Union[SyncManager, None] = None,
        embedding_provider: Union[Any, None] = None,
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

    @retry_memory_operation(max_retries=3, initial_backoff=0.1, max_backoff=2.0)
    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
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
        errors = {}
        for adapter_name, adapter in self.adapters.items():
            if hasattr(adapter, "retrieve"):
                try:
                    # Use circuit breaker to protect the retrieve operation
                    circuit = circuit_breaker_registry.get_or_create(
                        f"memory_retrieve_{adapter_name}",
                        failure_threshold=3,
                        reset_timeout=60.0
                    )
                    
                    item = circuit.execute(adapter.retrieve, item_id)
                    if item is not None:
                        return item
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
                        context={"item_id": item_id, "circuit_breaker": True}
                    )
                except Exception as e:
                    # Retrieve operation failed, log and continue to next adapter
                    logger.error(
                        f"Failed to retrieve memory item from {adapter_name}: {e}"
                    )
                    errors[adapter_name] = str(e)
                    
                    # Log to error logger
                    memory_error_logger.log_error(
                        operation="retrieve",
                        adapter_name=adapter_name,
                        error=e,
                        context={"item_id": item_id}
                    )
        
        if errors:
            logger.warning(f"Failed to retrieve item {item_id} from any adapter: {errors}")
            
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
        errors = {}
        for adapter_name in adapter_preference:
            if adapter_name not in self.adapters:
                continue
                
            adapter = self.adapters[adapter_name]
            circuit = circuit_breaker_registry.get_or_create(
                f"memory_store_{adapter_name}",
                failure_threshold=3,
                reset_timeout=60.0
            )
            
            try:
                # Use the circuit breaker to protect the store operation
                return circuit.execute(adapter.store, memory_item)
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
                    context={"item_id": memory_item.id, "circuit_breaker": True}
                )
            except Exception as e:
                # Store operation failed, log and continue to next adapter
                logger.error(
                    f"Failed to store memory item in {adapter_name}: {e}"
                )
                errors[adapter_name] = str(e)
                    
                # Log to error logger
                memory_error_logger.log_error(
                    operation="store_item",
                    adapter_name=adapter_name,
                    error=e,
                    context={"item_id": memory_item.id}
                )
                
        # If we get here, all adapters failed
        error_msg = f"Failed to store memory item in any adapter: {errors}"
        logger.error(error_msg)
        raise MemoryTransactionError(
            error_msg,
            operation="store_item"
        )

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
        store: Union[str, None] = None,
        strategy: str = "direct",
        context: Optional[Dict[str, Any]] = None,
        stores: Optional[List[str]] | None = None,
    ) -> Any:
        """Route a query through the :class:`QueryRouter`."""

        return self.query_router.route(
            query, store=store, strategy=strategy, context=context, stores=stores
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
        adapters = []
        for store_name in stores:
            adapter = self.adapters.get(store_name)
            if adapter:
                adapters.append(adapter)
            else:
                logger.warning(f"Store {store_name} not found, skipping")
                
        # If no valid adapters were found, fall back to the sync manager
        if not adapters:
            logger.warning("No valid adapters found for transaction, falling back to sync manager")
            return self.sync_manager.transaction(stores)
            
        # Create and return a transaction context
        return TransactionContext(adapters)

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
        
    def get_error_summary(self) -> Dict[str, Any]:
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
        operation: Optional[str] = None,
        adapter_name: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get recent memory operation errors, optionally filtered by criteria.
        
        Args:
            operation: Filter by operation (e.g., "store", "retrieve")
            adapter_name: Filter by adapter name
            error_type: Filter by error type
            limit: Maximum number of errors to return
            
        Returns:
            A list of error entries
        """
        return memory_error_logger.get_recent_errors(
            operation=operation,
            adapter_name=adapter_name,
            error_type=error_type,
            limit=limit
        )
        
    def clear_error_log(self) -> None:
        """
        Clear the in-memory error log.
        
        This method clears the in-memory error log, but does not affect
        persisted error logs on disk.
        """
        memory_error_logger.clear_errors()
