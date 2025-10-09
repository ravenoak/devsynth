import sys

import pytest

from devsynth.application.memory import sync_manager as sm_mod
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.sync_manager import SyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from tests.fixtures.resources import skip_if_missing_backend

pytestmark = [
    *skip_if_missing_backend("lmdb"),
    *skip_if_missing_backend("faiss"),
]


@pytest.fixture(autouse=True)
def no_kuzu(monkeypatch):
    monkeypatch.delitem(sys.modules, "kuzu", raising=False)


def _manager(lmdb, faiss, kuzu):
    adapters = {"lmdb": lmdb, "faiss": faiss, "kuzu": kuzu}
    manager = MemoryManager(adapters=adapters)
    manager.sync_manager = SyncManager(manager)
    return manager


@pytest.mark.medium
def test_synchronize_core_commit(tmp_path, monkeypatch):
    """Synchronize core stores atomically on commit. ReqID: FR-60"""

    LMDBStore = pytest.importorskip(
        "devsynth.application.memory.lmdb_store",
        reason="Install the 'memory' or 'tests' extras to enable LMDB-backed tests.",
    ).LMDBStore
    FAISSStore = pytest.importorskip(
        "devsynth.application.memory.faiss_store",
        reason="Install the 'retrieval' or 'memory' extras to enable FAISS-backed tests.",
    ).FAISSStore
    KuzuMemoryStore = pytest.importorskip(
        "devsynth.adapters.kuzu_memory_store",
        reason="Install the 'retrieval' or 'memory' extras to enable Kuzu-backed tests.",
    ).KuzuMemoryStore
    KuzuStore = pytest.importorskip(
        "devsynth.application.memory.kuzu_store",
        reason="Install the 'retrieval' or 'memory' extras to enable Kuzu-backed tests.",
    ).KuzuStore

    for cls in (KuzuMemoryStore, KuzuStore, LMDBStore, FAISSStore):
        monkeypatch.setattr(cls, "__abstractmethods__", frozenset())

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    lmdb = LMDBStore(str(tmp_path / "lmdb"))
    faiss = FAISSStore(str(tmp_path / "faiss"))
    kuzu = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
    manager = _manager(lmdb, faiss, kuzu)

    item = MemoryItem(id="1", content="hello", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="1", content="hello", embedding=[0.1] * 5, metadata={})

    lmdb.store(item)
    faiss.store_vector(vector)

    result = manager.sync_manager.synchronize_core()
    assert result["lmdb_to_kuzu"] == 1
    assert result["faiss_to_kuzu"] == 1

    assert kuzu.retrieve("1") is not None
    assert kuzu.retrieve_vector("1") is not None

    kuzu.cleanup()


@pytest.mark.medium
def test_synchronize_core_rollback(tmp_path, monkeypatch):
    """Roll back all stores when core sync commit fails. ReqID: FR-60"""

    LMDBStore = pytest.importorskip(
        "devsynth.application.memory.lmdb_store",
        reason="Install the 'memory' or 'tests' extras to enable LMDB-backed tests.",
    ).LMDBStore
    FAISSStore = pytest.importorskip(
        "devsynth.application.memory.faiss_store",
        reason="Install the 'retrieval' or 'memory' extras to enable FAISS-backed tests.",
    ).FAISSStore
    KuzuMemoryStore = pytest.importorskip(
        "devsynth.adapters.kuzu_memory_store",
        reason="Install the 'retrieval' or 'memory' extras to enable Kuzu-backed tests.",
    ).KuzuMemoryStore
    KuzuStore = pytest.importorskip(
        "devsynth.application.memory.kuzu_store",
        reason="Install the 'retrieval' or 'memory' extras to enable Kuzu-backed tests.",
    ).KuzuStore

    for cls in (KuzuMemoryStore, KuzuStore, LMDBStore, FAISSStore):
        monkeypatch.setattr(cls, "__abstractmethods__", frozenset())

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    lmdb = LMDBStore(str(tmp_path / "lmdb"))
    faiss = FAISSStore(str(tmp_path / "faiss"))
    kuzu = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
    manager = _manager(lmdb, faiss, kuzu)

    item = MemoryItem(id="2", content="boom", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="2", content="boom", embedding=[0.2] * 5, metadata={})

    lmdb.store(item)
    faiss.store_vector(vector)

    def fail_exit(self, exc_type, exc_val, exc_tb):  # pragma: no cover - test
        raise RuntimeError("commit failure")

    monkeypatch.setattr(sm_mod.LMDBTransactionContext, "__exit__", fail_exit)

    with pytest.raises(RuntimeError):
        manager.sync_manager.synchronize_core()

    assert lmdb.retrieve("2") is not None
    assert faiss.retrieve_vector("2") is not None
    assert kuzu.retrieve("2") is None
    assert kuzu.retrieve_vector("2") is None

    kuzu.cleanup()
