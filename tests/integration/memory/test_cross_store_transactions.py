import sys

import pytest

LMDBStore = pytest.importorskip("devsynth.application.memory.lmdb_store").LMDBStore
FAISSStore = pytest.importorskip("devsynth.application.memory.faiss_store").FAISSStore
from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.sync_manager import SyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

pytestmark = [
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("faiss"),
]


@pytest.fixture(autouse=True)
def no_kuzu(monkeypatch):
    monkeypatch.delitem(sys.modules, "kuzu", raising=False)
    for cls in (KuzuMemoryStore, KuzuStore, LMDBStore, FAISSStore):
        monkeypatch.setattr(cls, "__abstractmethods__", frozenset())


def _manager(lmdb, faiss, kuzu):
    adapters = {"lmdb": lmdb, "faiss": faiss, "kuzu": kuzu}
    manager = MemoryManager(adapters=adapters)
    manager.sync_manager = SyncManager(manager)
    return manager


@pytest.mark.medium
def test_cross_store_transaction_commit(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    lmdb = LMDBStore(str(tmp_path / "lmdb"))
    faiss = FAISSStore(str(tmp_path / "faiss"))
    kuzu = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
    manager = _manager(lmdb, faiss, kuzu)

    item = MemoryItem(id="1", content="hello", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="1", content="hello", embedding=[0.1] * 5, metadata={})

    with manager.sync_manager.transaction(["lmdb", "faiss", "kuzu"]):
        lmdb.store(item)
        faiss.store_vector(vector)
        kuzu.store(item)

    assert lmdb.retrieve("1") is not None
    assert faiss.retrieve_vector("1") is not None
    assert kuzu.retrieve("1") is not None
    assert kuzu.retrieve_vector("1") is not None

    kuzu.cleanup()


@pytest.mark.medium
def test_cross_store_transaction_rollback(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    lmdb = LMDBStore(str(tmp_path / "lmdb"))
    faiss = FAISSStore(str(tmp_path / "faiss"))
    kuzu = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
    manager = _manager(lmdb, faiss, kuzu)

    item = MemoryItem(id="2", content="world", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="2", content="world", embedding=[0.2] * 5, metadata={})

    with pytest.raises(RuntimeError):
        with manager.sync_manager.transaction(["lmdb", "faiss", "kuzu"]):
            lmdb.store(item)
            faiss.store_vector(vector)
            kuzu.store(item)
            raise RuntimeError("boom")

    assert lmdb.retrieve("2") is None
    assert faiss.retrieve_vector("2") is None
    assert kuzu.retrieve("2") is None
    assert kuzu.retrieve_vector("2") is None

    kuzu.cleanup()
