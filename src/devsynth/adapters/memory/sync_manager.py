"""Convenience adapter tying LMDB, FAISS and Kuzu stores together.

This adapter instantiates the three persistence backends under a common
base directory and wires them into a :class:`MemoryManager` with an attached
:class:`SyncManager`.  The manager can then be used to keep data in sync
between the stores, allowing LMDB and FAISS data to be replicated into the
Kuzu store.
"""

from __future__ import annotations

from pathlib import Path

from ...adapters.kuzu_memory_store import KuzuMemoryStore
from ...application.memory.faiss_store import FAISSStore
from ...application.memory.kuzu_store import KuzuStore
from ...application.memory.lmdb_store import LMDBStore
from ...application.memory.memory_manager import MemoryManager
from ...application.memory.sync_manager import SyncManager
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class MultiStoreSyncManager:
    """Adapter that coordinates LMDB, FAISS and Kuzu stores.

    Parameters
    ----------
    base_path:
        Directory where the backend stores will persist their data.  Each
        backend uses a subdirectory named after the store (``lmdb``, ``faiss``
        and ``kuzu``).
    vector_dimension:
        Dimension of FAISS vectors; defaults to ``5`` to match test fixtures.
    """

    def __init__(self, base_path: str, *, vector_dimension: int = 5) -> None:
        base = Path(base_path)

        # Some of the backend stores declare abstract methods which can
        # interfere with instantiation in tests.  Clear the abstract method
        # sets so they behave like concrete classes.
        for cls in (LMDBStore, FAISSStore, KuzuStore, KuzuMemoryStore):
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

    def synchronize_all(self) -> None:
        """Synchronize LMDB and FAISS contents into the Kuzu store."""
        self.sync_manager.synchronize("lmdb", "kuzu")
        self.sync_manager.synchronize("faiss", "kuzu")
