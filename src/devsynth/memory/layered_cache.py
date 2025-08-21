"""Multi-layered memory system with tiered cache strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List


@dataclass
class DictCacheLayer:
    """Simple dictionary-backed cache layer."""

    store: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        return self.store[key]

    def set(self, key: str, value: Any) -> None:
        self.store[key] = value

    def contains(self, key: str) -> bool:
        return key in self.store


class MultiLayeredMemory:
    """Orchestrates multiple cache layers with promotion and statistics."""

    def __init__(self, layers: Iterable[DictCacheLayer]):
        self.layers: List[DictCacheLayer] = list(layers)
        if not self.layers:
            raise ValueError("At least one cache layer is required")
        self._accesses = 0
        self._hits: List[int] = [0 for _ in self.layers]

    def set(self, key: str, value: Any) -> None:
        """Write-through to all cache layers."""
        for layer in self.layers:
            layer.set(key, value)

    def get(self, key: str) -> Any:
        """Retrieve ``key`` promoting values up the hierarchy."""
        self._accesses += 1
        for idx, layer in enumerate(self.layers):
            if layer.contains(key):
                self._hits[idx] += 1
                value = layer.get(key)
                for promote_idx in range(idx):
                    self.layers[promote_idx].set(key, value)
                return value
        raise KeyError(key)

    def hit_ratio(self, layer: int | None = None) -> float:
        """Return overall or per-layer hit ratio."""
        if self._accesses == 0:
            return 0.0
        if layer is None:
            return sum(self._hits) / self._accesses
        return self._hits[layer] / self._accesses
