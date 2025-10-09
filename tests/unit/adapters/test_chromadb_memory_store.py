import uuid

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType
from tests.fixtures.resources import (
    backend_import_reason,
    skip_if_missing_backend,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("chromadb")

chromadb = pytest.importorskip(
    "chromadb",
    reason=backend_import_reason("chromadb"),
)

chromadb_memory_store = pytest.importorskip(
    "devsynth.adapters.chromadb_memory_store",
    reason="Install the 'chromadb' or 'memory' extras to exercise the ChromaDB memory store.",
)


pytestmark = [
    *skip_if_missing_backend("chromadb"),
    pytest.mark.fast,
]


def test_store_and_retrieve_roundtrip(monkeypatch, tmp_path):
    """Store and retrieve using ChromaDBMemoryStore. ReqID: N/A"""

    class DummyEF:
        def __call__(self, texts):
            if isinstance(texts, str):
                return [0.0, 0.0, 0.0]
            return [[0.0, 0.0, 0.0] for _ in texts]

    monkeypatch.setattr(chromadb_memory_store, "ClientAPI", chromadb.Client)
    monkeypatch.setattr(
        chromadb_memory_store.embedding_functions,
        "DefaultEmbeddingFunction",
        lambda: DummyEF(),
    )
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    store = chromadb_memory_store.ChromaDBMemoryStore(
        persist_directory=str(tmp_path),
        use_provider_system=False,
    )

    item = MemoryItem(
        id=str(uuid.uuid4()),
        content="hello",
        memory_type=MemoryType.WORKING,
        metadata={"note": "test"},
    )

    store.store(item)
    retrieved = store.retrieve(item.id)
    assert retrieved.content == "hello"

    assert store.delete(item.id)
    with pytest.raises(RuntimeError):
        store.retrieve(item.id)
