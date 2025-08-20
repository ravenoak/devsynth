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


def test_transaction_context_commit_and_rollback(tmp_path, monkeypatch):
    """MultiStoreSyncManager transaction wrapper commits and rolls back."""
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))
    manager = MultiStoreSyncManager(str(tmp_path))

    item = MemoryItem(id="1", content="hello", memory_type=MemoryType.CODE)
    vector = MemoryVector(
        id="1",
        content="hello",
        embedding=[0.1] * manager.faiss.dimension,
        metadata={},
    )
    with manager.transaction():
        manager.lmdb.store(item)
        manager.faiss.store_vector(vector)
        manager.kuzu.store(item)
        manager.kuzu.vector.store_vector(vector)

    assert manager.lmdb.retrieve("1") is not None
    assert manager.faiss.retrieve_vector("1") is not None
    assert manager.kuzu.retrieve("1") is not None
    assert manager.kuzu.vector.retrieve_vector("1") is not None

    with pytest.raises(RuntimeError):
        with manager.transaction():
            bad_item = MemoryItem(id="2", content="bad", memory_type=MemoryType.CODE)
            bad_vec = MemoryVector(
                id="2",
                content="bad",
                embedding=[0.2] * manager.faiss.dimension,
                metadata={},
            )
            manager.lmdb.store(bad_item)
            manager.faiss.store_vector(bad_vec)
            manager.kuzu.store(bad_item)
            manager.kuzu.vector.store_vector(bad_vec)
            raise RuntimeError("boom")

    assert manager.lmdb.retrieve("2") is None
    assert manager.faiss.retrieve_vector("2") is None
    assert manager.kuzu.retrieve("2") is None
    assert manager.kuzu.vector.retrieve_vector("2") is None

    manager.cleanup()
