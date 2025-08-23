"""Coordinate multiple memory stores with simple transaction semantics.

This module provides a minimal :class:`SyncManager` that keeps TinyDB,
DuckDB, LMDB, and Kuzu style stores in sync. It aims to satisfy the
requirements outlined in
``docs/specifications/complete-memory-system-integration.md``.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Protocol, runtime_checkable


@runtime_checkable
class MemoryStore(Protocol):
    """Protocol for simple key-value stores.

    Stores used with :class:`SyncManager` must implement a small set of
    operations for writing, reading and snapshotting state.  This mirrors
    the behaviour of real adapters such as TinyDB, DuckDB, LMDB and Kuzu
    but keeps the implementation lightweight for unit testing.
    """

    def write(
        self, key: str, value: Any
    ) -> None:  # ReqID: memory-adapter-read-and-write-operations
        ...

    def read(self, key: str) -> Any:  # ReqID: memory-adapter-read-and-write-operations
        ...

    def snapshot(self) -> Dict[str, Any]: ...

    def restore(self, snapshot: Dict[str, Any]) -> None: ...


@dataclass
class SyncManager:
    """Synchronise items across multiple memory stores.

    Parameters
    ----------
    stores:
        Mapping of store name to store instance.  The manager expects
        `tinydb`, `duckdb`, `lmdb` and `kuzu` entries to coordinate a
        complete set of adapters.
    """

    stores: Mapping[str, MemoryStore] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {"tinydb", "duckdb", "lmdb", "kuzu"}
        missing = required - set(self.stores)
        if missing:
            raise ValueError(f"Missing stores: {', '.join(sorted(missing))}")

    # ------------------------------------------------------------------
    def write(self, key: str, value: Any) -> None:
        """Write `value` under `key` to all configured stores."""

        for store in self.stores.values():
            store.write(key, value)

    def read(self, key: str) -> Any:
        """Return `key` from the first store containing it."""

        for store in self.stores.values():
            try:
                return store.read(key)
            except KeyError:
                continue
        raise KeyError(key)

    # ------------------------------------------------------------------
    @contextmanager
    def transaction(self):
        """Atomic commit/rollback across all stores.

        A snapshot of each store is taken before yielding control.  If an
        exception escapes the context, every store is restored to its
        previous state.  Otherwise all mutations are committed implicitly.
        """

        snapshots = {name: store.snapshot() for name, store in self.stores.items()}
        try:
            yield
        except Exception:
            for name, snap in snapshots.items():
                self.stores[name].restore(snap)
            raise
