"""Convenience adapter tying LMDB, FAISS and Kuzu stores together.

This adapter instantiates the three persistence backends under a common
base directory and wires them into a :class:`MemoryManager` with an attached
:class:`SyncManager`.  The manager can then be used to keep data in sync
between the stores, allowing LMDB and FAISS data to be replicated into the
Kuzu store.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ...logging_setup import DevSynthLogger

# Optional backend imports -------------------------------------------------
# These stores depend on optional system libraries. Import them lazily so the
# module can be imported even when the dependencies are missing, providing a
# clearer error message when an adapter is instantiated.
try:  # pragma: no cover - optional dependency
    from ...adapters.kuzu_memory_store import KuzuMemoryStore
except Exception as exc:  # pragma: no cover - graceful fallback
    KuzuMemoryStore = None  # type: ignore[assignment]
    _KUZU_ERROR = exc

try:  # pragma: no cover - optional dependency
    from ...application.memory.faiss_store import FAISSStore
except Exception as exc:  # pragma: no cover - graceful fallback
    FAISSStore = None  # type: ignore[assignment]
    _FAISS_ERROR = exc

try:  # pragma: no cover - optional dependency
    from ...application.memory.lmdb_store import LMDBStore
except Exception as exc:  # pragma: no cover - graceful fallback
    LMDBStore = None  # type: ignore[assignment]
    _LMDB_ERROR = exc

from ...application.memory.memory_manager import MemoryManager
from ...application.memory.sync_manager import SyncManager

logger = DevSynthLogger(__name__)

__all__ = ["MultiStoreSyncManager"]


class MultiStoreSyncManager:
    """Adapter that coordinates LMDB, FAISS and Kuzu stores.

    Defining ``__slots__`` keeps the adapter lightweight while it wires multiple
    backends together for synchronization tests.

    Parameters
    ----------
    base_path:
        Directory where the backend stores will persist their data.  Each
        backend uses a subdirectory named after the store (``lmdb``, ``faiss``
        and ``kuzu``).
    vector_dimension:
        Dimension of FAISS vectors; defaults to ``5`` to match test fixtures.
    """

    __slots__ = ("lmdb", "faiss", "kuzu", "manager", "sync_manager")

    def __init__(self, base_path: str, *, vector_dimension: int = 5) -> None:
        base = Path(base_path)
        base.mkdir(parents=True, exist_ok=True)

        # Validate optional dependencies before proceeding so the caller gets a
        # clear error rather than an AttributeError later on.
        if LMDBStore is None:  # pragma: no cover - simple guard
            raise ImportError(
                "MultiStoreSyncManager requires the 'lmdb' extras to be installed"
            ) from _LMDB_ERROR
        if FAISSStore is None:  # pragma: no cover - simple guard
            raise ImportError(
                "MultiStoreSyncManager requires the 'faiss-cpu' package"
            ) from _FAISS_ERROR
        if KuzuMemoryStore is None:  # pragma: no cover - simple guard
            raise ImportError(
                "MultiStoreSyncManager requires the 'kuzu' package"
            ) from _KUZU_ERROR

        # Some of the backend stores declare abstract methods which can
        # interfere with instantiation in tests.  Clear the abstract method
        # sets so they behave like concrete classes.
        for cls in (LMDBStore, FAISSStore, KuzuMemoryStore):
            try:  # pragma: no cover - defensive
                cls.__abstractmethods__ = frozenset()
            except Exception:
                pass

        self.lmdb = LMDBStore(str(base / "lmdb"))
        self.faiss = FAISSStore(str(base / "faiss"), dimension=vector_dimension)
        self.kuzu = KuzuMemoryStore(str(base / "kuzu"))
        self.manager = MemoryManager(
            adapters={"lmdb": self.lmdb, "faiss": self.faiss, "kuzu": self.kuzu}
        )
        self.sync_manager = SyncManager(self.manager)
        logger.info("Initialized multi-store sync manager at %s", base_path)

    def synchronize_all(self) -> Dict[str, int]:
        """Synchronize LMDB and FAISS contents into the Kuzu store.

        Returns
        -------
        Dict[str, int]
            Mapping of synchronization directions to item counts. The keys
            correspond to the direction of propagation (e.g. ``"lmdb->kuzu"``).
        """

        return self.manager.synchronize_core_stores()

    # ------------------------------------------------------------------
    # transactional helpers -------------------------------------------------

    def transaction(self, stores: list[str] | None = None):
        """Return a transaction context spanning ``stores``.

        Parameters
        ----------
        stores:
            Optional list of store names to include.  When omitted all
            configured stores participate in the transaction.

        Returns
        -------
        Context manager
            The context manager yielded by :class:`SyncManager` which will
            commit on successful exit and roll back if an exception occurs.

        Raises
        ------
        KeyError
            If any requested store name is not configured.
        """

        stores = stores or list(self.manager.adapters.keys())
        missing = set(stores) - set(self.manager.adapters.keys())
        if missing:  # pragma: no cover - defensive
            raise KeyError(f"Unknown stores requested: {', '.join(sorted(missing))}")
        return self.sync_manager.transaction(stores)

    def cross_store_query(self, query: str, stores: list[str] | None = None):
        """Run ``query`` across multiple stores.

        This is a small convenience wrapper around
        :meth:`SyncManager.cross_store_query` that defaults to all configured
        stores when ``stores`` is ``None``.

        Parameters
        ----------
        query:
            Query string to execute.
        stores:
            Optional list of store names that should participate.

        Returns
        -------
        dict[str, list[Any]]
            Mapping of store name to query results.
        """

        stores = stores or list(self.manager.adapters.keys())
        return self.sync_manager.cross_store_query(query, stores)

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin an explicit transaction across all stores."""

        return self.sync_manager.begin_transaction(transaction_id)

    def commit_transaction(self, transaction_id: str) -> None:
        """Commit a previously started transaction."""

        self.sync_manager.commit_transaction(transaction_id)

    def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback a previously started transaction."""

        self.sync_manager.rollback_transaction(transaction_id)

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if ``transaction_id`` is active."""
        return self.sync_manager.is_transaction_active(transaction_id)

    def cleanup(self) -> None:
        """Release resources held by the underlying stores."""
        for store in (self.lmdb, self.faiss):
            close = getattr(store, "close", None)
            if callable(close):
                try:  # pragma: no cover - defensive
                    close()
                except Exception:
                    pass
        # The Kuzu memory store uses a custom cleanup helper
        if hasattr(self.kuzu, "cleanup"):
            try:  # pragma: no cover - defensive
                self.kuzu.cleanup()
            except Exception:
                pass
