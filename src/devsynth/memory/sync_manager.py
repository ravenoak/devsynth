"""Coordinate multiple memory stores with simple transaction semantics."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar, runtime_checkable


ValueT = TypeVar("ValueT")
Snapshot = Mapping[str, ValueT]


@runtime_checkable
class MemoryStore(Protocol[ValueT]):
    """Protocol for simple key-value stores.

    Stores used with :class:`SyncManager` must implement read/write helpers and
    be able to snapshot/restore their state. Concrete adapters such as TinyDB
    and DuckDB satisfy this interface in the application layer.
    """

    def write(self, key: str, value: ValueT) -> None:
        """Persist ``value`` under ``key``."""

    def read(self, key: str) -> ValueT:
        """Return the stored value for ``key`` or raise ``KeyError``."""

    def snapshot(self) -> Snapshot:
        """Return a mapping representing the current store state."""

    def restore(self, snapshot: Snapshot) -> None:
        """Restore the store from a previous :meth:`snapshot` output."""

@dataclass(slots=True)
class SyncManager(Generic[ValueT]):
    """Synchronise items across multiple memory stores."""

    stores: Mapping[str, MemoryStore[ValueT]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {"tinydb", "duckdb", "lmdb", "kuzu"}
        missing = required - set(self.stores)
        if missing:
            raise ValueError(f"Missing stores: {', '.join(sorted(missing))}")

    def write(self, key: str, value: ValueT) -> None:
        """Write ``value`` under ``key`` to all configured stores."""

        for store in self.stores.values():
            store.write(key, value)

    def read(self, key: str) -> ValueT:
        """Return ``key`` from the first store containing it."""

        for store in self.stores.values():
            try:
                return store.read(key)
            except KeyError:
                continue
        raise KeyError(key)

    @contextmanager
    def transaction(self):
        """Atomic commit/rollback across all stores."""

        snapshots = {name: store.snapshot() for name, store in self.stores.items()}
        try:
            yield
        except Exception:
            for name, snap in snapshots.items():
                self.stores[name].restore(snap)
            raise
