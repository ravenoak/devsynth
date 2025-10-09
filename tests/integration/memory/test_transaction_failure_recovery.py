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
def test_commit_failure_triggers_rollback(tmp_path, monkeypatch):
    """Commit failures should roll back all stores. ReqID: FR-60"""

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

    item = MemoryItem(id="3", content="fail", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="3", content="fail", embedding=[0.3] * 5, metadata={})

    def fail_exit(self, exc_type, exc_val, exc_tb):
        raise RuntimeError("commit failure")

    monkeypatch.setattr(sm_mod.LMDBTransactionContext, "__exit__", fail_exit)

    with pytest.raises(RuntimeError):
        with manager.sync_manager.transaction(["lmdb", "faiss", "kuzu"]):
            lmdb.store(item)
            faiss.store_vector(vector)
            kuzu.store(item)

    assert lmdb.retrieve("3") is None
    assert faiss.retrieve_vector("3") is None
    assert kuzu.retrieve("3") is None
    assert kuzu.retrieve_vector("3") is None
    kuzu.cleanup()
