import os
import uuid

import pytest

from tests.fixtures.resources import backend_import_reason, skip_if_missing_backend

pytestmark = [*skip_if_missing_backend("chromadb"), pytest.mark.fast]


# Import dependencies directly - chromadb is available in the environment
try:
    import chromadb
except ImportError:
    pytest.skip("chromadb not available")

try:
    from devsynth.application.memory.chromadb_store import ChromaDBStore
except ImportError:
    pytest.skip("ChromaDBStore not available")
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

    # Patch the client creation in the ChromaDBStore __init__ method
    original_init = _TestableChromaDBStore.__init__

    def failing_init(self, file_path, **kwargs):
        # Create a failing client instead of the real one
        self.file_path = file_path
        self.collection_name = kwargs.get("collection_name", "devsynth_memory")
        self.versions_collection_name = kwargs.get("versions_collection_name", "devsynth_memory_versions")
        self._token_usage = 0
        self._cache = {}
        self._embedding_optimization_enabled = True
        self.client = FailingClient()
        self._use_fallback = False
        self._store = {}
        self._versions = {}
        self._fallback_file = os.path.join(file_path, "fallback_store.json")

        # Mock collection and versions collection
        self.collection = FailingClient()
        self.versions_collection = FailingClient()

        # Mock tokenizer
        self.tokenizer = None

    monkeypatch.setattr(_TestableChromaDBStore, "__init__", failing_init)

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
