import pytest

pytest.importorskip("chromadb")

from devsynth.application.memory.adapters.chromadb_vector_adapter import (
    ChromaDBVectorAdapter,
)
from devsynth.domain.models.memory import MemoryVector

pytestmark = [
    pytest.mark.requires_resource("chromadb"),
    pytest.mark.memory_intensive,
]


def test_transaction_commit_and_rollback(tmp_path, monkeypatch):
    """ChromaDB adapter should commit and rollback vector operations."""
    monkeypatch.setenv("ENABLE_CHROMADB", "1")
    adapter = ChromaDBVectorAdapter(
        collection_name="txn", persist_directory=str(tmp_path)
    )
    vec = MemoryVector(
        id="v1", content="hello", embedding=[0.1, 0.2, 0.3, 0.4, 0.5], metadata={}
    )

    tid = adapter.begin_transaction()
    adapter.store_vector(vec)
    assert adapter.is_transaction_active(tid)
    adapter.commit_transaction(tid)
    assert adapter.retrieve_vector("v1") is not None

    # Re-instantiate to verify persistence across sessions
    adapter2 = ChromaDBVectorAdapter(
        collection_name="txn", persist_directory=str(tmp_path)
    )
    assert adapter2.retrieve_vector("v1") is not None

    tid = adapter2.begin_transaction()
    adapter2.delete_vector("v1")
    adapter2.rollback_transaction(tid)
    assert adapter2.retrieve_vector("v1") is not None
    assert not adapter2.is_transaction_active(tid)

    # Ensure data remains after reopening once more
    adapter3 = ChromaDBVectorAdapter(
        collection_name="txn", persist_directory=str(tmp_path)
    )
    assert adapter3.retrieve_vector("v1") is not None
