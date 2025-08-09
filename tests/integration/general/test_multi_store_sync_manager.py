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
    manager.synchronize_all()

    assert manager.kuzu.retrieve("alpha") is not None
    assert manager.kuzu.vector.retrieve_vector("alpha") is not None

    # Recreate manager with same base path to confirm persistence
    manager.cleanup()
    manager2 = MultiStoreSyncManager(str(tmp_path))
    assert manager2.lmdb.retrieve("alpha") is not None
    assert manager2.faiss.retrieve_vector("alpha") is not None
    manager2.synchronize_all()
    assert manager2.kuzu.retrieve("alpha") is not None
    assert manager2.kuzu.vector.retrieve_vector("alpha") is not None
    manager2.cleanup()
