import pytest

pytest.importorskip("chromadb")

MultiStoreSyncManager = pytest.importorskip(
    "devsynth.adapters.memory.sync_manager"
).MultiStoreSyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

pytestmark = [
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("faiss"),
    pytest.mark.requires_resource("kuzu"),
]


def test_multi_store_persistence(tmp_path, monkeypatch):
    """LMDB, FAISS and Kuzu stores should persist across adapter instances."""
    # Avoid network calls by providing a trivial embedding function
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))
    manager = MultiStoreSyncManager(str(tmp_path))

    item = MemoryItem(id="p1", content="persist", memory_type=MemoryType.CODE)
    vector = MemoryVector(
        id="p1",
        content="persist",
        embedding=[0.2] * manager.faiss.dimension,
        metadata={},
    )

    manager.lmdb.store(item)
    manager.faiss.store_vector(vector)
    manager.synchronize_all()

    assert manager.kuzu.retrieve("p1") is not None
    assert manager.kuzu.vector.retrieve_vector("p1") is not None

    # Recreate manager with the same base path to ensure data persisted
    manager2 = MultiStoreSyncManager(str(tmp_path))
    assert manager2.lmdb.retrieve("p1") is not None
    assert manager2.faiss.retrieve_vector("p1") is not None

    manager2.synchronize_all()
    assert manager2.kuzu.retrieve("p1") is not None
    assert manager2.kuzu.vector.retrieve_vector("p1") is not None
