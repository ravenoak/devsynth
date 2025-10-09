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
def test_multi_store_persistence(tmp_path, monkeypatch):
    """LMDB, FAISS and Kuzu stores should persist across adapter instances. ReqID: FR-37"""
    # Avoid network calls by providing a trivial embedding function
    ef = pytest.importorskip(
        "chromadb.utils.embedding_functions",
        reason=backend_import_reason("chromadb"),
    )
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
