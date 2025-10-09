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
def test_transaction_context_commit_and_rollback(tmp_path, monkeypatch):
    """MultiStoreSyncManager transaction wrapper commits and rolls back."""
    ef = pytest.importorskip(
        "chromadb.utils.embedding_functions",
        reason=backend_import_reason("chromadb"),
    )
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
