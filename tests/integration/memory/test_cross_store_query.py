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


@pytest.mark.medium
def test_cross_store_query_returns_results(tmp_path, monkeypatch):
    """Cross-store queries should return results from all stores. ReqID: FR-60"""
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))
    manager = MultiStoreSyncManager(str(tmp_path))

    item = MemoryItem(id="q1", content="alpha", memory_type=MemoryType.CODE)
    vector = MemoryVector(
        id="q1",
        content="alpha",
        embedding=[0.1] * manager.faiss.dimension,
        metadata={},
    )

    manager.lmdb.store(item)
    manager.faiss.store_vector(vector)
    manager.synchronize_all()

    results = manager.cross_store_query("alpha")
    assert any(m.id == "q1" for m in results.get("lmdb", []))
    assert any(m.id == "q1" for m in results.get("kuzu", []))
    assert any(v.id == "q1" for v in results.get("faiss", []))
