import uuid

import pytest

from tests.fixtures.resources import backend_import_reason, skip_if_missing_backend

pytestmark = [*skip_if_missing_backend("chromadb"), pytest.mark.fast]


chromadb = pytest.importorskip("chromadb", reason=backend_import_reason("chromadb"))
ChromaDBStore = pytest.importorskip(
    "devsynth.application.memory.chromadb_store",
    reason=backend_import_reason("chromadb"),
).ChromaDBStore
from devsynth.application.memory.dto import MemoryRecord
from devsynth.domain.models.memory import MemoryItem, MemoryType


class _TestableChromaDBStore(ChromaDBStore):
    def begin_transaction(self):
        return "tx"

    def commit_transaction(self, transaction_id):
        return True

    def rollback_transaction(self, transaction_id):
        return True

    def is_transaction_active(self, transaction_id):
        return False


def test_store_and_retrieve_with_fallback(monkeypatch, tmp_path):
    """Store and retrieve items using fallback storage. ReqID: N/A"""

    class FailingClient:
        def get_collection(self, name):  # pragma: no cover - forced failure
            raise RuntimeError("fail")

        def create_collection(self, name):  # pragma: no cover - forced failure
            raise RuntimeError("fail")

    monkeypatch.setattr(chromadb, "EphemeralClient", lambda: FailingClient())

    store = _TestableChromaDBStore(str(tmp_path))
    item = MemoryItem(
        id=str(uuid.uuid4()),
        content="hello",
        memory_type=MemoryType.WORKING,
        metadata={"note": "test"},
    )

    store.store(item)
    retrieved = store.retrieve(item.id)
    assert isinstance(retrieved, MemoryRecord)
    assert isinstance(retrieved.item.metadata, dict)
    assert isinstance(retrieved.metadata, dict)
    assert retrieved.item.content == "hello"

    assert store.delete(item.id) is True
    assert store.retrieve(item.id) is None
