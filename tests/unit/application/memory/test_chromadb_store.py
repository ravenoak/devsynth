import os
import os
import uuid

import pytest

from devsynth.application.memory.chromadb_store import ChromaDBStore
from devsynth.domain.models.memory import MemoryItem, MemoryType

chromadb = pytest.importorskip("chromadb")


class _TestableChromaDBStore(ChromaDBStore):
    def begin_transaction(self):
        return "tx"

    def commit_transaction(self, transaction_id):
        return True

    def rollback_transaction(self, transaction_id):
        return True

    def is_transaction_active(self, transaction_id):
        return False


@pytest.mark.requires_resource("chromadb")
@pytest.mark.fast
def test_store_and_retrieve_with_fallback(monkeypatch, tmp_path):
    """Store and retrieve items using fallback storage. ReqID: N/A"""
    if os.environ.get("DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE") != "1":
        pytest.skip("ChromaDB resource not available")

    class FailingClient:
        def get_collection(self, name):  # pragma: no cover - forced failure
            raise RuntimeError("fail")

        def create_collection(self, name):  # pragma: no cover - forced failure
            raise RuntimeError("fail")

    monkeypatch.setattr(chromadb, "EphemeralClient", lambda: FailingClient())
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    store = _TestableChromaDBStore(str(tmp_path))
    item = MemoryItem(
        id=str(uuid.uuid4()),
        content="hello",
        memory_type=MemoryType.WORKING,
        metadata={"note": "test"},
    )

    store.store(item)
    retrieved = store.retrieve(item.id)
    assert isinstance(retrieved, MemoryItem)
    assert isinstance(retrieved.metadata, dict)
    assert retrieved.content == "hello"

    assert store.delete(item.id) is True
    assert store.retrieve(item.id) is None
