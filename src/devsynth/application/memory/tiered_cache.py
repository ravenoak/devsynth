"""
Tiered Cache Module

This module provides a tiered cache strategy with an in-memory cache for
frequently used items. It implements a Least Recently Used (LRU) cache
eviction policy to manage cache size.
"""

from collections import OrderedDict
from typing import Generic, Optional, TypeVar

from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

T = TypeVar("T")


class TieredCache(Generic[T]):
    """
    Tiered Cache with LRU eviction policy.

    This class implements a tiered cache strategy with an in-memory cache for
    frequently used items. It uses a Least Recently Used (LRU) cache eviction
    policy to manage cache size.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize the tiered cache.

        Args:
            max_size: The maximum number of items to store in the cache
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, T] = OrderedDict()
        logger.info(f"Tiered cache initialized with max size {max_size}")

    def get(self, key: str) -> T | None:
        """
        Get an item from the cache.

        Args:
            key: The key of the item to retrieve

        Returns:
            The cached item, or None if not found
        """
        if key in self.cache:
            # Move the item to the end of the OrderedDict to mark it as most recently used
            value = self.cache.pop(key)
            self.cache[key] = value
            logger.debug(f"Cache hit for key {key}")
            return value

        logger.debug(f"Cache miss for key {key}")
        return None

    def put(self, key: str, value: T) -> None:
        """
        Put an item in the cache.

        Args:
            key: The key of the item to store
            value: The item to store
        """
        # If the key already exists, remove it first
        if key in self.cache:
            self.cache.pop(key)

        # If the cache is full, remove the least recently used item (first item in OrderedDict)
        if len(self.cache) >= self.max_size:
            # Get the key of the least recently used item
            lru_key, _ = next(iter(self.cache.items()))
            self.cache.pop(lru_key)
            logger.debug(
                f"Removed least recently used item with key {lru_key} from cache"
            )

        # Add the new item to the end of the OrderedDict
        self.cache[key] = value
        logger.debug(f"Added item with key {key} to cache")

    def remove(self, key: str) -> None:
        """
        Remove an item from the cache.

        Args:
            key: The key of the item to remove
        """
        if key in self.cache:
            self.cache.pop(key)
            logger.debug(f"Removed item with key {key} from cache")

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        logger.info("Cache cleared")

    def size(self) -> int:
        """
        Get the current size of the cache.

        Returns:
            The number of items in the cache
        """
        return len(self.cache)

    def contains(self, key: str) -> bool:
        """
        Check if the cache contains an item.

        Args:
            key: The key of the item to check

        Returns:
            True if the cache contains the item, False otherwise
        """
        return key in self.cache

    def get_keys(self) -> list[str]:
        """
        Get all keys in the cache.

        Returns:
            A list of all keys in the cache
        """
        return list(self.cache.keys())

    def get_values(self) -> list[T]:
        """
        Get all values in the cache.

        Returns:
            A list of all values in the cache
        """
        return list(self.cache.values())

    def get_items(self) -> list[tuple[str, T]]:
        """
        Get all items in the cache.

        Returns:
            A list of all items (key-value pairs) in the cache
        """
        return list(self.cache.items())
