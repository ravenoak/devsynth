"""Multi-layered memory system with tiered cache strategy.

See :doc:`docs/analysis/layered_cache.md` for complexity and hit-rate
derivations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Generic, List, Protocol, TypeVar, runtime_checkable
from collections.abc import Iterable

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


@runtime_checkable
class CacheLayerProtocol(Protocol[T_co]):
    """Protocol capturing the minimal cache layer interface."""

    def get(self, key: str) -> T_co:  # pragma: no cover - protocol
        ...

    def set(self, key: str, value: T_co) -> None:  # pragma: no cover - protocol
        ...

    def contains(self, key: str) -> bool:  # pragma: no cover - protocol
        ...


@dataclass
class DictCacheLayer(Generic[T]):
    """Simple dictionary-backed cache layer."""

    store: dict[str, T] = field(default_factory=dict)

    def get(self, key: str) -> T:
        return self.store[key]

    def set(self, key: str, value: T) -> None:
        self.store[key] = value

    def contains(self, key: str) -> bool:
        return key in self.store

    # Read/write aliases for interface parity. ReqID: memory-adapter-read-and-write-operations
    def read(self, key: str) -> T:
        return self.get(key)

    def write(self, key: str, value: T) -> None:
        self.set(key, value)


class MultiLayeredMemory(Generic[T]):
    """Orchestrates multiple cache layers with promotion and statistics."""

    def __init__(self, layers: Iterable[CacheLayerProtocol[T]]):
        self.layers: list[CacheLayerProtocol[T]] = list(layers)
        if not self.layers:
            raise ValueError("At least one cache layer is required")
        self._accesses = 0
        self._hits: list[int] = [0 for _ in self.layers]

    def set(self, key: str, value: T) -> None:
        """Write-through to all cache layers."""
        for layer in self.layers:
            layer.set(key, value)

    # Maintain a conventional API alongside ``set``/``get``. ReqID: memory-adapter-read-and-write-operations
    def write(self, key: str, value: T) -> None:
        self.set(key, value)

    def get(self, key: str) -> T:
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

    def read(self, key: str) -> T:
        return self.get(key)

    def hit_ratio(self, layer: int | None = None) -> float:
        """Return overall or per-layer hit ratio."""
        if self._accesses == 0:
            return 0.0
        if layer is None:
            return sum(self._hits) / self._accesses
        return self._hits[layer] / self._accesses


__all__ = ["CacheLayerProtocol", "DictCacheLayer", "MultiLayeredMemory"]
