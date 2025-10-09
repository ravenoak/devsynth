import pytest

from tests.fixtures.resources import (
    skip_if_missing_backend,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("faiss")

FAISSStore = pytest.importorskip(
    "devsynth.application.memory.faiss_store",
    reason="Install the 'retrieval' or 'memory' extras to use the FAISS store.",
).FAISSStore
from devsynth.domain.models.memory import MemoryVector

pytestmark = [
    *skip_if_missing_backend("faiss"),
]


@pytest.mark.medium
def test_faiss_transaction_commit_and_rollback(tmp_path):
    """FAISSStore transactions should commit and rollback correctly."""
    store = FAISSStore(str(tmp_path))

    vec = MemoryVector(
        id="v1", content="hello", embedding=[0.1] * store.dimension, metadata={}
    )
    with store.transaction():
        store.store_vector(vec)
    assert store.retrieve_vector("v1") is not None

    vec2 = MemoryVector(
        id="v2", content="boom", embedding=[0.2] * store.dimension, metadata={}
    )
    with pytest.raises(RuntimeError):
        with store.transaction():
            store.store_vector(vec2)
            raise RuntimeError("boom")
    assert store.retrieve_vector("v2") is None

    # Verify persistence after reopening the store
    reopened = FAISSStore(str(tmp_path))
    assert reopened.retrieve_vector("v1") is not None
