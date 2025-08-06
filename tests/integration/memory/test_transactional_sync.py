import sys
import pytest

LMDBStore = pytest.importorskip("devsynth.application.memory.lmdb_store").LMDBStore
FAISSStore = pytest.importorskip("devsynth.application.memory.faiss_store").FAISSStore
from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.application.memory.kuzu_store import KuzuStore
ChromaDBStore = pytest.importorskip("devsynth.application.memory.chromadb_store").ChromaDBStore
ChromaDBAdapter = pytest.importorskip(
    "devsynth.adapters.memory.chroma_db_adapter"
).ChromaDBAdapter
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.sync_manager import SyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryVector, MemoryType

pytestmark = [
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("faiss"),
    pytest.mark.requires_resource("chromadb"),
]


@pytest.fixture(autouse=True)
def no_kuzu(monkeypatch):
    monkeypatch.delitem(sys.modules, "kuzu", raising=False)
    for cls in (KuzuMemoryStore, KuzuStore, LMDBStore, FAISSStore, ChromaDBStore):
        monkeypatch.setattr(cls, "__abstractmethods__", frozenset())


def _manager(lmdb, faiss, kuzu, chroma, chroma_vec):
    adapters = {
        "lmdb": lmdb,
        "faiss": faiss,
        "kuzu": kuzu,
        "chroma": chroma,
        "chroma_vec": chroma_vec,
    }
    manager = MemoryManager(adapters=adapters)
    manager.sync_manager = SyncManager(manager)
    return manager


@pytest.mark.medium
def test_transactional_sync_rollback(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("ENABLE_CHROMADB", "1")
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))

    lmdb_store = LMDBStore(str(tmp_path / "lmdb"))
    faiss_store = FAISSStore(str(tmp_path / "faiss"))
    kuzu_store = KuzuMemoryStore.create_ephemeral()
    assert kuzu_store._store._use_fallback
    chroma_path = tmp_path / "chroma"
    chroma_path.mkdir()
    chroma_store = ChromaDBStore(str(chroma_path))
    chroma_vec_path = tmp_path / "chroma_vec"
    chroma_vec_path.mkdir()
    chroma_vec = ChromaDBAdapter(str(chroma_vec_path))

    manager = _manager(lmdb_store, faiss_store, kuzu_store, chroma_store, chroma_vec)

    item = MemoryItem(id="x", content="hello", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="x", content="hello", embedding=[0.1] * 5, metadata={})

    lmdb_store.store(item)
    faiss_store.store_vector(vector)
    manager.synchronize("lmdb", "kuzu")
    manager.synchronize("faiss", "kuzu")

    def failing_store(_):
        raise RuntimeError("boom")

    monkeypatch.setattr(chroma_store, "store", failing_store)

    with pytest.raises(RuntimeError):
        manager.synchronize("kuzu", "chroma")

    assert chroma_store.retrieve("x") is None
    assert kuzu_store.retrieve("x") is not None
    assert lmdb_store.retrieve("x") is not None
    assert faiss_store.retrieve_vector("x") is not None

    kuzu_store.cleanup()
