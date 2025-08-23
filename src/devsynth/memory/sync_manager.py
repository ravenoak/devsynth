"""Lightweight synchronization manager for multiple memory stores.

This module coordinates TinyDB, DuckDB, LMDB, and Kuzu stores to provide a
unified persistence layer.  Each write is broadcast to all configured stores and
reads fall back through stores until a match is found.

The manager makes a best‑effort attempt to instantiate all supported stores but
will quietly skip any whose optional dependencies are missing.  Users may also
pass pre‑constructed store instances via the ``stores`` parameter.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable, Mapping, MutableMapping, Optional

from devsynth.domain.models.memory import MemoryItem
from devsynth.logging_setup import DevSynthLogger

try:  # pragma: no cover - optional dependency loading
    from devsynth.application.memory.tinydb_store import TinyDBStore
except Exception:  # pragma: no cover - store unavailable
    TinyDBStore = None  # type: ignore

try:  # pragma: no cover - optional dependency loading
    from devsynth.application.memory.duckdb_store import DuckDBStore
except Exception:  # pragma: no cover - store unavailable
    DuckDBStore = None  # type: ignore

try:  # pragma: no cover - optional dependency loading
    from devsynth.application.memory.lmdb_store import LMDBStore
except Exception:  # pragma: no cover - store unavailable
    LMDBStore = None  # type: ignore

try:  # pragma: no cover - optional dependency loading
    from devsynth.application.memory.kuzu_store import KuzuStore
except Exception:  # pragma: no cover - store unavailable
    KuzuStore = None  # type: ignore

logger = DevSynthLogger(__name__)

StoreMapping = MutableMapping[str, object]


class SynchronizationManager:
    """Coordinate persistence across multiple memory stores."""

    def __init__(
        self,
        *,
        base_path: Optional[str] = None,
        stores: Optional[Mapping[str, object]] = None,
    ) -> None:
        self.stores: StoreMapping = {}
        if stores:
            self.stores.update(stores)
        if base_path:
            self._init_default_stores(base_path)
        if not self.stores:
            raise ValueError("No memory stores available for synchronization")

    # ------------------------------------------------------------------
    def _init_default_stores(self, base_path: str) -> None:
        """Attempt to construct all supported stores for ``base_path``."""

        if TinyDBStore is not None:
            try:
                self.stores.setdefault("tinydb", TinyDBStore(base_path))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("TinyDB store unavailable: %s", exc)
        if DuckDBStore is not None:
            try:
                self.stores.setdefault("duckdb", DuckDBStore(base_path))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("DuckDB store unavailable: %s", exc)
        if LMDBStore is not None:
            try:
                self.stores.setdefault("lmdb", LMDBStore(base_path))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("LMDB store unavailable: %s", exc)
        if KuzuStore is not None:
            try:
                # ``KuzuStore`` uses ``file_path`` instead of ``base_path``
                self.stores.setdefault("kuzu", KuzuStore(base_path))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Kuzu store unavailable: %s", exc)

    # ------------------------------------------------------------------
    def store(self, item: MemoryItem) -> str:
        """Persist ``item`` across all configured stores.

        Returns the item identifier as stored in the underlying adapters.
        """

        last_id: Optional[str] = None
        for store in self.stores.values():
            try:
                last_id = store.store(deepcopy(item))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Store %s failed to persist item %s: %s", store, item.id, exc
                )
        return last_id or item.id

    # ------------------------------------------------------------------
    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Return the first item matching ``item_id`` from any store."""

        for store in self.stores.values():
            try:
                result = store.retrieve(item_id)
            except Exception:  # pragma: no cover - defensive
                continue
            if result is not None:
                return result
        return None

    # ------------------------------------------------------------------
    def synchronize(self, source: str) -> None:
        """Mirror all items from ``source`` store to remaining stores.

        If the source store lacks ``get_all_items`` the method is a no‑op.
        """

        src_store = self.stores.get(source)
        if not src_store or not hasattr(src_store, "get_all_items"):
            return
        try:
            items: Iterable[MemoryItem] = src_store.get_all_items()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - defensive
            return
        for name, store in self.stores.items():
            if name == source:
                continue
            for item in items:
                try:
                    if store.retrieve(item.id) is None:
                        store.store(deepcopy(item))
                except Exception:  # pragma: no cover - defensive
                    continue
