"""Coordinate multiple memory stores with simple transaction semantics."""

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Generic,
    Iterator,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

ValueT = TypeVar("ValueT")
Snapshot: TypeAlias = Mapping[str, ValueT]


if TYPE_CHECKING:

    @runtime_checkable
    class MemoryStore(Protocol[ValueT]):
        """Protocol for simple key-value stores."""

        def write(self, key: str, value: ValueT) -> None:
            """Persist ``value`` under ``key``."""

        def read(self, key: str) -> ValueT:
            """Return the stored value for ``key`` or raise ``KeyError``."""

        def snapshot(self) -> Snapshot:
            """Return a mapping representing the current store state."""

        def restore(self, snapshot: Snapshot) -> None:
            """Restore the store from a previous :meth:`snapshot` output."""

else:

    @runtime_checkable
    class MemoryStore(Protocol):
        """Runtime-safe protocol for simple key-value stores."""

        def write(self, key: str, value: object) -> None:
            """Persist ``value`` under ``key``."""

        def read(self, key: str) -> object:
            """Return the stored value for ``key`` or raise ``KeyError``."""

        def snapshot(self) -> Mapping[str, object]:
            """Return a mapping representing the current store state."""

        def restore(self, snapshot: Mapping[str, object]) -> None:
            """Restore the store from a previous :meth:`snapshot` output."""

    MemoryStore.__parameters__ = (ValueT,)

    @classmethod
    def _memory_store_getitem(cls, _type_args: object) -> type["MemoryStore"]:
        """Return the base protocol to keep ``isinstance`` checks runtime-safe."""

        return cls

    MemoryStore.__class_getitem__ = classmethod(_memory_store_getitem)


@dataclass(slots=True)
class SyncManager(Generic[ValueT]):
    """Synchronise items across multiple memory stores."""

    stores: Mapping[str, MemoryStore[ValueT]] = field(default_factory=dict)
    required_stores: frozenset[str] = field(
        default_factory=lambda: frozenset({"tinydb"})
    )
    optional_stores: frozenset[str] = field(
        default_factory=lambda: frozenset({"duckdb", "lmdb", "kuzu"})
    )

    def __post_init__(self) -> None:
        configured = frozenset(self.stores)
        missing = self.required_stores - configured
        if missing:
            raise ValueError(f"Missing stores: {', '.join(sorted(missing))}")

        allowed = self.required_stores | self.optional_stores
        unexpected = configured - allowed
        if unexpected:
            raise ValueError(
                "Unexpected stores configured: " f"{', '.join(sorted(unexpected))}"
            )

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
    def transaction(self) -> Iterator[None]:
        """Atomic commit/rollback across all stores."""

        snapshots = {name: store.snapshot() for name, store in self.stores.items()}
        try:
            yield
        except Exception:
            for name, snap in snapshots.items():
                self.stores[name].restore(snap)
            raise


__all__ = ["MemoryStore", "SyncManager", "ValueT", "Snapshot"]
