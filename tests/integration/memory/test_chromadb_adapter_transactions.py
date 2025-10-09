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

ChromaDBAdapter = pytest.importorskip(
    "devsynth.adapters.memory.chroma_db_adapter",
    reason="Install the 'chromadb' or 'memory' extras to use the ChromaDB adapter.",
).ChromaDBAdapter
from devsynth.domain.models.memory import MemoryVector

pytestmark = [
    *skip_if_missing_backend("chromadb"),
]


@pytest.mark.medium
def test_chromadb_transaction_commit_and_rollback(tmp_path, monkeypatch):
    """Vectors added within a transaction should rollback correctly. ReqID: FR-60"""
    ef = pytest.importorskip(
        "chromadb.utils.embedding_functions",
        reason=backend_import_reason("chromadb"),
    )
    # Avoid network calls by supplying a no-op embedding function
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))

    adapter = ChromaDBAdapter(str(tmp_path))

    base_vec = MemoryVector(id="v1", content="base", embedding=[0.1] * 5, metadata={})
    adapter.store_vector(base_vec)

    tx = adapter.begin_transaction()
    assert adapter.is_transaction_active(tx)
    temp_vec = MemoryVector(id="v2", content="temp", embedding=[0.2] * 5, metadata={})
    adapter.store_vector(temp_vec)
    adapter.rollback_transaction(tx)
    assert not adapter.is_transaction_active(tx)
    assert adapter.retrieve_vector("v2") is None
    assert adapter.retrieve_vector("v1") is not None

    tx2 = adapter.begin_transaction()
    assert adapter.is_transaction_active(tx2)
    persist_vec = MemoryVector(
        id="v3", content="keep", embedding=[0.3] * 5, metadata={}
    )
    adapter.store_vector(persist_vec)
    adapter.prepare_commit(tx2)
    adapter.commit_transaction(tx2)
    assert not adapter.is_transaction_active(tx2)
    assert adapter.retrieve_vector("v3") is not None
