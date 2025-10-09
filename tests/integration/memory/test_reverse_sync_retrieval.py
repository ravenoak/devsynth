import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from tests.fixtures.resources import (
    backend_import_reason,
    skip_if_missing_backend,
)

pytestmark = [
    *skip_if_missing_backend("chromadb"),
    *skip_if_missing_backend("lmdb"),
    *skip_if_missing_backend("faiss"),
    *skip_if_missing_backend("kuzu"),
]


@pytest.mark.medium
def test_bidirectional_persistence_and_retrieval(tmp_path, monkeypatch):
    """Synchronizes data both ways between stores. ReqID: FR-60"""

    MultiStoreSyncManager = pytest.importorskip(
        "devsynth.adapters.memory.sync_manager",
        reason="Install the 'memory' Poetry extra to exercise the multi-store sync manager.",
    ).MultiStoreSyncManager
    ef = pytest.importorskip(
        "chromadb.utils.embedding_functions",
        reason=backend_import_reason("chromadb"),
    )
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
