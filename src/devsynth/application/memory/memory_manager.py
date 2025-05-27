"""
Memory Manager Module

This module provides a unified interface to different memory adapters,
allowing for efficient querying of different types of memory and tagging
items with EDRR phases.
"""
from typing import Dict, List, Any, Optional, Union
from ...domain.models.memory import MemoryItem, MemoryType, MemoryItemType, MemoryVector
from ...domain.interfaces.memory import MemoryStore, VectorStore
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

class MemoryManager:
    """
    Memory Manager provides a unified interface to different memory adapters.

    It allows for efficient querying of different types of memory and tagging
    items with EDRR phases.
    """

    def __init__(self, adapters: Union[Dict[str, Any], Any] = None):
        """
        Initialize the Memory Manager with the specified adapters.

        Args:
            adapters: Dictionary of adapters with keys 'graph', 'vector', 'tinydb',
                     or a single adapter that will be used as the default
        """
        if adapters is None:
            self.adapters = {}
        elif isinstance(adapters, dict):
            self.adapters = adapters
        else:
            # If a single adapter is provided, use it as the default adapter
            self.adapters = {'default': adapters}

        logger.info(f"Memory Manager initialized with adapters: {', '.join(self.adapters.keys())}")

    def store_with_edrr_phase(self, content: Any, memory_type: MemoryType, edrr_phase: str, 
                             metadata: Dict[str, Any] = None) -> str:
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
            id="",
            content=content,
            memory_type=memory_type,
            metadata=metadata
        )

        # Store in the appropriate adapter
        # Prefer TinyDB for structured data, then Graph for relationships, then default to first available
        if 'tinydb' in self.adapters:
            return self.adapters['tinydb'].store(memory_item)
        elif 'graph' in self.adapters:
            return self.adapters['graph'].store(memory_item)
        elif self.adapters:
            # Use the first available adapter
            adapter_name = next(iter(self.adapters))
            return self.adapters[adapter_name].store(memory_item)
        else:
            raise ValueError("No adapters available for storing memory items")

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
            if hasattr(adapter, 'retrieve'):
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
        if 'graph' in self.adapters:
            # Use the graph adapter for relationship queries
            graph_adapter = self.adapters['graph']
            return graph_adapter.query_related_items(item_id)
        else:
            logger.warning("Graph adapter not available for querying related items")
            return []

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Union[MemoryItem, MemoryVector]]:
        """
        Perform a similarity search with a query embedding.

        Args:
            query_embedding: The query embedding
            top_k: The number of results to return

        Returns:
            A list of similar memory items or vectors
        """
        if 'vector' in self.adapters:
            # Use the vector adapter for similarity search
            vector_adapter = self.adapters['vector']
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
        if 'tinydb' in self.adapters:
            # Use the TinyDB adapter for structured data queries
            tinydb_adapter = self.adapters['tinydb']
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
            if hasattr(adapter, 'search'):
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
        if 'graph' not in self.adapters:
            logger.warning("Graph adapter not available for querying evolution across EDRR phases")
            return []

        # Get the item and its related items
        graph_adapter = self.adapters['graph']
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
            key=lambda x: edrr_order.get(x.metadata.get("edrr_phase", ""), 999)
        )

        return sorted_items

    def _get_all_related_items(self, item_id: str, graph_adapter: Any) -> List[MemoryItem]:
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
        if 'tinydb' in self.adapters:
            return self.adapters['tinydb'].store(memory_item)
        elif 'graph' in self.adapters:
            return self.adapters['graph'].store(memory_item)
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
            if hasattr(adapter, 'query_by_type'):
                # Use the query_by_type method if available
                items = adapter.query_by_type(memory_type)
                results.extend(items)
            elif hasattr(adapter, 'search'):
                # Use the search method if available
                # Convert memory_type to string value if it's an enum
                memory_type_value = memory_type.value if hasattr(memory_type, 'value') else memory_type
                items = adapter.search({"memory_type": memory_type_value})
                results.extend(items)
            elif hasattr(adapter, 'get_all'):
                # Use the get_all method if available and filter by type
                items = [item for item in adapter.get_all() if item.memory_type == memory_type]
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
            if hasattr(adapter, 'query_by_metadata'):
                # Use the query_by_metadata method if available
                items = adapter.query_by_metadata(metadata)
                results.extend(items)
            elif hasattr(adapter, 'search'):
                # Use the search method if available
                items = adapter.search(metadata)
                results.extend(items)
            elif hasattr(adapter, 'get_all'):
                # Use the get_all method if available and filter by metadata
                items = []
                for item in adapter.get_all():
                    if all(item.metadata.get(key) == value for key, value in metadata.items()):
                        items.append(item)
                results.extend(items)

        return results
