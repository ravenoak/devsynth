"""
Multi-Layered Memory System Module

This module provides a multi-layered memory system with short-term, episodic,
and semantic memory layers. It categorizes memory items into appropriate layers
based on their type and provides methods for querying across layers.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Literal

from ...domain.models.memory import MemoryItem, MemoryType
from ...logging_setup import DevSynthLogger
from .tiered_cache import TieredCache

logger = DevSynthLogger(__name__)


LayerName = Literal["short-term", "episodic", "semantic"]
LayerStore = dict[str, MemoryItem]


class MultiLayeredMemorySystem:
    """
    Multi-Layered Memory System with short-term, episodic, and semantic memory layers.

    This class categorizes memory items into appropriate layers based on their type
    and provides methods for querying across layers. It also supports a tiered cache
    strategy for faster access to frequently used items.
    """

    def __init__(self) -> None:
        """Initialize the multi-layered memory system."""
        # Initialize memory layers
        self.short_term_memory: LayerStore = {}
        self.episodic_memory: LayerStore = {}
        self.semantic_memory: LayerStore = {}

        # Initialize cache
        self.cache: TieredCache[MemoryItem] | None = None
        self.cache_enabled: bool = False
        self.cache_stats: dict[str, int] = {"hits": 0, "misses": 0}

        logger.info("Multi-layered memory system initialized")

    def store(self, memory_item: MemoryItem) -> str:
        """
        Store a memory item in the appropriate memory layer.

        Args:
            memory_item: The memory item to store

        Returns:
            The ID of the stored memory item
        """
        # Generate an ID if not provided
        if not memory_item.id:
            memory_item.id = str(uuid.uuid4())
        else:
            memory_item.id = str(memory_item.id)

        # Determine the appropriate memory layer based on the memory type
        if memory_item.memory_type in [MemoryType.CONTEXT, MemoryType.CONVERSATION]:
            # Store in short-term memory
            self.short_term_memory[memory_item.id] = memory_item
            logger.debug(f"Stored item {memory_item.id} in short-term memory")
        elif memory_item.memory_type in [MemoryType.TASK_HISTORY, MemoryType.ERROR_LOG]:
            # Store in episodic memory
            self.episodic_memory[memory_item.id] = memory_item
            logger.debug(f"Stored item {memory_item.id} in episodic memory")
        elif memory_item.memory_type in [
            MemoryType.KNOWLEDGE,
            MemoryType.DOCUMENTATION,
        ]:
            # Store in semantic memory
            self.semantic_memory[memory_item.id] = memory_item
            logger.debug(f"Stored item {memory_item.id} in semantic memory")
        else:
            # Default to short-term memory for unknown types
            self.short_term_memory[memory_item.id] = memory_item
            logger.debug(f"Stored item {memory_item.id} in short-term memory (default)")

        return memory_item.id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        """
        Retrieve a memory item by ID.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        # Check cache first if enabled
        if self.cache_enabled:
            cached_item = self.cache.get(item_id) if self.cache is not None else None
            if cached_item is not None:
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit for item {item_id}")
                return cached_item
            self.cache_stats["misses"] += 1
            logger.debug(f"Cache miss for item {item_id}")

        # Check each memory layer
        if item_id in self.short_term_memory:
            item = self.short_term_memory[item_id]
        elif item_id in self.episodic_memory:
            item = self.episodic_memory[item_id]
        elif item_id in self.semantic_memory:
            item = self.semantic_memory[item_id]
        else:
            logger.debug(f"Item {item_id} not found in any memory layer")
            return None

        # Add to cache if enabled
        if self.cache_enabled and self.cache is not None:
            self.cache.put(item_id, item)

        return item

    def get_items_by_layer(self, layer: LayerName | str) -> list[MemoryItem]:
        """
        Get all memory items in a specific layer.

        Args:
            layer: The memory layer to query ("short-term", "episodic", or "semantic")

        Returns:
            A list of memory items in the specified layer
        """
        if layer == "short-term":
            return list(self.short_term_memory.values())
        elif layer == "episodic":
            return list(self.episodic_memory.values())
        elif layer == "semantic":
            return list(self.semantic_memory.values())
        else:
            logger.warning(f"Unknown memory layer: {layer}")
            return []

    def _normalize_layer(self, layer: object | None) -> LayerName | None:
        if isinstance(layer, str):
            candidate = layer.strip().lower()
            if candidate == "short-term":
                return "short-term"
            if candidate == "episodic":
                return "episodic"
            if candidate == "semantic":
                return "semantic"
        return None

    def query(self, query_params: Mapping[str, object]) -> list[MemoryItem]:
        """
        Query memory items across layers.

        Args:
            query_params: Query parameters, including optional "layer" parameter

        Returns:
            A list of memory items matching the query
        """
        # Check if a specific layer is requested
        layer_param = query_params.get("layer")
        normalized = self._normalize_layer(layer_param)

        if normalized is not None:
            return self.get_items_by_layer(normalized)

        all_items: list[MemoryItem] = []
        all_items.extend(self.short_term_memory.values())
        all_items.extend(self.episodic_memory.values())
        all_items.extend(self.semantic_memory.values())
        return all_items

    def enable_tiered_cache(self, max_size: int = 100) -> None:
        """
        Enable the tiered cache strategy.

        Args:
            max_size: The maximum number of items to store in the cache
        """
        self.cache = TieredCache[MemoryItem](max_size=max_size)
        self.cache_enabled = True
        logger.info(f"Tiered cache enabled with max size {max_size}")

    def disable_tiered_cache(self) -> None:
        """Disable the tiered cache strategy."""
        self.cache = None
        self.cache_enabled = False
        logger.info("Tiered cache disabled")

    def is_tiered_cache_enabled(self) -> bool:
        """
        Check if the tiered cache strategy is enabled.

        Returns:
            True if the tiered cache is enabled, False otherwise
        """
        return self.cache_enabled

    def get_cache_stats(self) -> dict[str, int]:
        """
        Get cache statistics.

        Returns:
            A dictionary with cache statistics (hits, misses)
        """
        return self.cache_stats

    def get_cache_size(self) -> int:
        """
        Get the current size of the cache.

        Returns:
            The number of items in the cache, or 0 if cache is disabled
        """
        if self.cache_enabled:
            return self.cache.size()
        return 0

    def get_cache_max_size(self) -> int:
        """
        Get the maximum size of the cache.

        Returns:
            The maximum number of items in the cache, or 0 if cache is disabled
        """
        if self.cache_enabled:
            return self.cache.max_size
        return 0

    def clear_cache(self) -> None:
        """Clear the cache."""
        if self.cache_enabled:
            self.cache.clear()
            logger.info("Cache cleared")

    def clear(self) -> None:
        """Clear all memory layers and cache."""
        self.short_term_memory.clear()
        self.episodic_memory.clear()
        self.semantic_memory.clear()
        if self.cache_enabled:
            self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0}
        logger.info("All memory layers and cache cleared")
