"""Multi-layered memory system with tiered caches."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from devsynth.domain.models.memory import MemoryType


@dataclass
class CacheStats:
    """Cache hit and miss counters."""

    hits: int = 0
    misses: int = 0


class _LRUCache:
    """Least-recently-used cache layer."""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self._store: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()


class MultiLayerCache:
    """Hierarchy of cache layers checked in order."""

    def __init__(self, sizes: Iterable[int]):
        self.layers: List[_LRUCache] = [_LRUCache(size) for size in sizes]
        self.stats: List[CacheStats] = [CacheStats() for _ in self.layers]

    def get(self, key: str) -> Optional[Any]:
        for index, layer in enumerate(self.layers):
            value = layer.get(key)
            if value is not None:
                self.stats[index].hits += 1
                for higher in range(index):
                    self.layers[higher].set(key, value)
                return value
            self.stats[index].misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        for layer in self.layers:
            layer.set(key, value)

    def clear(self) -> None:
        for layer, stat in zip(self.layers, self.stats):
            layer.clear()
            stat.hits = stat.misses = 0

    def get_stats(self) -> List[CacheStats]:
        return self.stats


@dataclass
class MultiLayeredMemorySystem:
    """In-memory storage organized by :class:`MemoryType` with a tiered cache."""

    cache_sizes: Iterable[int] = (32, 64, 128)
    cache: MultiLayerCache = field(init=False)
    layers: Dict[MemoryType, Dict[str, Any]] = field(
        default_factory=lambda: {
            MemoryType.CONTEXT: {},
            MemoryType.TASK_HISTORY: {},
            MemoryType.KNOWLEDGE: {},
        }
    )

    def __post_init__(self) -> None:
        self.cache = MultiLayerCache(self.cache_sizes)

    def store(self, content: Any, memory_type: MemoryType) -> str:
        """Persist *content* under *memory_type* and return its identifier."""

        item_id = str(uuid4())
        self.layers.setdefault(memory_type, {})[item_id] = content
        return item_id

    def retrieve(self, item_id: str, memory_type: MemoryType) -> Optional[Any]:
        """Retrieve *item_id* from cache or persistent layer."""

        key = f"{memory_type.value}:{item_id}"
        value = self.cache.get(key)
        if value is not None:
            return value
        value = self.layers.get(memory_type, {}).get(item_id)
        if value is not None:
            self.cache.set(key, value)
        return value

    def get_cache_stats(self) -> List[CacheStats]:
        """Return hit/miss statistics for each cache layer."""

        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """Remove all cached entries and reset statistics."""

        self.cache.clear()
