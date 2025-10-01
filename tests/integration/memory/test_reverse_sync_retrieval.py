import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


pytestmark = [
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("faiss"),
    pytest.mark.requires_resource("kuzu"),
]


@pytest.mark.medium
def test_bidirectional_persistence_and_retrieval(tmp_path, monkeypatch):
    """Synchronizes data both ways between stores. ReqID: FR-60"""

    MultiStoreSyncManager = pytest.importorskip(
        "devsynth.adapters.memory.sync_manager"
    ).MultiStoreSyncManager
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))
    manager = MultiStoreSyncManager(str(tmp_path))

    item_a = MemoryItem(id="a", content="alpha", memory_type=MemoryType.CODE)
    vector_a = MemoryVector(
        id="a",
        content="alpha",
        embedding=[0.1] * manager.faiss.dimension,
        metadata={},
    )
    manager.lmdb.store(item_a)
    manager.faiss.store_vector(vector_a)
    manager.synchronize_all()
    assert manager.kuzu.retrieve("a") is not None
    assert manager.kuzu.vector.retrieve_vector("a") is not None

    item_b = MemoryItem(id="b", content="beta", memory_type=MemoryType.CODE)
    vector_b = MemoryVector(
        id="b",
        content="beta",
        embedding=[0.2] * manager.faiss.dimension,
        metadata={},
    )
    manager.kuzu.store(item_b)
    manager.kuzu.vector.store_vector(vector_b)
    manager.manager.synchronize("kuzu", "lmdb")
    manager.manager.synchronize("kuzu", "faiss")

    assert manager.lmdb.retrieve("b") is not None
    assert manager.faiss.retrieve_vector("b") is not None

    manager2 = MultiStoreSyncManager(str(tmp_path))
    assert manager2.lmdb.retrieve("a") is not None
    assert manager2.lmdb.retrieve("b") is not None
    assert manager2.faiss.retrieve_vector("a") is not None
    assert manager2.faiss.retrieve_vector("b") is not None
    manager2.synchronize_all()
    assert manager2.kuzu.retrieve("a") is not None
    assert manager2.kuzu.vector.retrieve_vector("a") is not None
    assert manager2.kuzu.retrieve("b") is not None
    assert manager2.kuzu.vector.retrieve_vector("b") is not None
