import pytest

pytest.importorskip("faiss")
pytest.importorskip("lmdb")

from devsynth.adapters.memory.sync_manager import MultiStoreSyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


pytestmark = [
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("faiss"),
    pytest.mark.requires_resource("kuzu"),
]


@pytest.mark.medium
def test_multi_store_sync_and_persistence(tmp_path, monkeypatch):
    """LMDB and FAISS data should propagate to Kuzu and persist across runs."""

    # Avoid network calls by providing a trivial embedding function
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))

    manager = MultiStoreSyncManager(str(tmp_path))

    item = MemoryItem(id="alpha", content="persist", memory_type=MemoryType.CODE)
    vector = MemoryVector(
        id="alpha",
        content="persist",
        embedding=[0.2] * manager.faiss.dimension,
        metadata={},
    )

    manager.lmdb.store(item)
    manager.faiss.store_vector(vector)
    result = manager.synchronize_all()

    assert result.get("lmdb_to_kuzu", 0) >= 1
    assert "faiss_to_kuzu" in result
    assert manager.kuzu.retrieve("alpha") is not None
    assert manager.kuzu.vector.retrieve_vector("alpha") is not None

    # Recreate manager with same base path to confirm persistence
    manager.cleanup()
    manager2 = MultiStoreSyncManager(str(tmp_path))
    assert manager2.lmdb.retrieve("alpha") is not None
    assert manager2.faiss.retrieve_vector("alpha") is not None
    result2 = manager2.synchronize_all()
    assert result2.get("lmdb_to_kuzu", 0) >= 1
    assert "faiss_to_kuzu" in result2
    assert manager2.kuzu.retrieve("alpha") is not None
    assert manager2.kuzu.vector.retrieve_vector("alpha") is not None
    manager2.cleanup()


@pytest.mark.medium
def test_multi_store_transaction_persistence(tmp_path, monkeypatch):
    """Transactions should commit and rollback across all stores with persistence."""

    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))

    manager = MultiStoreSyncManager(str(tmp_path))

    item = MemoryItem(id="alpha", content="persist", memory_type=MemoryType.CODE)
    vector = MemoryVector(
        id="alpha",
        content="persist",
        embedding=[0.2] * manager.faiss.dimension,
        metadata={},
    )

    # Commit a transaction that adds data to LMDB and FAISS
    with manager.transaction():
        manager.lmdb.store(item)
        manager.faiss.store_vector(vector)

    # Propagate to Kuzu after transaction commit
    result = manager.synchronize_all()

    assert result.get("lmdb_to_kuzu", 0) >= 1
    assert "faiss_to_kuzu" in result
    assert manager.kuzu.retrieve("alpha") is not None
    assert manager.faiss.retrieve_vector("alpha") is not None

    # Start another transaction and roll it back
    tid = manager.begin_transaction()
    manager.lmdb.store(MemoryItem(id="beta", content="x", memory_type=MemoryType.CODE))
    manager.faiss.store_vector(
        MemoryVector(
            id="beta",
            content="x",
            embedding=[0.1] * manager.faiss.dimension,
            metadata={},
        )
    )
    manager.rollback_transaction(tid)

    result = manager.synchronize_all()

    assert result.get("lmdb_to_kuzu", 0) >= 1
    assert "faiss_to_kuzu" in result
    assert manager.lmdb.retrieve("beta") is None
    assert manager.kuzu.retrieve("beta") is None

    # Recreate manager to verify persistence
    manager.cleanup()
    manager2 = MultiStoreSyncManager(str(tmp_path))
    assert manager2.lmdb.retrieve("alpha") is not None
    assert manager2.lmdb.retrieve("beta") is None
    manager2.cleanup()
