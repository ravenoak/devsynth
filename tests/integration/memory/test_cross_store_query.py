import pytest

from tests.fixtures.resources import (
    backend_import_reason,
    skip_if_missing_backend,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("chromadb")

pytest.importorskip(
    "chromadb",
    reason=backend_import_reason("chromadb"),
)

MultiStoreSyncManager = pytest.importorskip(
    "devsynth.adapters.memory.sync_manager",
    reason="Install the 'memory' Poetry extra to exercise the multi-store sync manager.",
).MultiStoreSyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

pytestmark = [
    *skip_if_missing_backend("chromadb"),
    *skip_if_missing_backend("lmdb"),
    *skip_if_missing_backend("faiss"),
    *skip_if_missing_backend("kuzu"),
]


@pytest.mark.medium
def test_cross_store_query_returns_results(tmp_path, monkeypatch):
    """Cross-store queries should return results from all stores. ReqID: FR-60"""
    ef = pytest.importorskip(
        "chromadb.utils.embedding_functions",
        reason=backend_import_reason("chromadb"),
    )
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
