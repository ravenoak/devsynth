import os
import sys
import types
from unittest.mock import patch

import pytest

from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.fixture
def no_kuzu(monkeypatch):
    """Ensure tests run without the real ``kuzu`` dependency."""
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")
    monkeypatch.delitem(sys.modules, "kuzu", raising=False)
    monkeypatch.setattr(KuzuMemoryStore, "__abstractmethods__", frozenset())
    monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())


@pytest.fixture
def fake_kuzu(monkeypatch):
    """Provide a minimal stub of the kuzu package."""

    class Database:
        def __init__(self, path):
            pass

    class Connection:
        def __init__(self, db):
            pass

        def execute(self, *args, **kwargs):
            return None

    fake = types.SimpleNamespace(Database=Database, Connection=Connection)
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")
    monkeypatch.setitem(sys.modules, "kuzu", fake)
    monkeypatch.setattr(KuzuMemoryStore, "__abstractmethods__", frozenset())
    monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())
    return fake


@pytest.fixture
def kuzu_store(no_kuzu):
    store = KuzuMemoryStore.create_ephemeral()
    try:
        yield store
    finally:
        store.cleanup()


@pytest.fixture
def kuzu_store_embedded(fake_kuzu):
    store = KuzuMemoryStore.create_ephemeral()
    try:
        yield store
    finally:
        store.cleanup()


@pytest.fixture(autouse=True)
def mock_embed():
    with (
        patch(
            "devsynth.adapters.kuzu_memory_store.embed", return_value=[[0.1, 0.2, 0.3]]
        ),
        patch(
            "devsynth.adapters.kuzu_memory_store.embedding_functions",
            types.SimpleNamespace(
                DefaultEmbeddingFunction=lambda: (lambda x: [0.0] * 5)
            ),
        ),
    ):
        yield


def test_kuzu_memory_vector_integration_succeeds(kuzu_store):
    config = {
        "memory_store_type": "kuzu",
        "memory_file_path": kuzu_store.persist_directory,
        "vector_store_enabled": True,
    }
    adapter = MemorySystemAdapter(config=config)
    memory_item = MemoryItem(
        id="item1",
        content="hello world",
        memory_type=MemoryType.LONG_TERM,
        metadata={},
    )
    item_id = adapter.memory_store.store(memory_item)
    results = adapter.vector_store.similarity_search([0.1, 0.2, 0.3], top_k=1)
    assert results
    assert results[0].id == item_id


def test_create_for_testing_with_kuzu(kuzu_store):
    adapter = MemorySystemAdapter.create_for_testing(
        storage_type="kuzu", memory_path=kuzu_store.persist_directory
    )
    assert adapter.storage_type == "kuzu"
    assert adapter.memory_store is not None
    assert adapter.context_manager is not None
    assert adapter.vector_store is not None


def test_ephemeral_store_cleanup(no_kuzu):
    store = KuzuMemoryStore.create_ephemeral()
    path = store.persist_directory
    assert os.path.exists(path)
    assert store._store._use_fallback
    store.cleanup()
    assert not os.path.exists(path)


def test_provider_fallback_on_empty_embedding(tmp_path, no_kuzu):
    with patch("devsynth.adapters.kuzu_memory_store.embed", return_value=[[]]):
        store = KuzuMemoryStore(str(tmp_path))
        assert store._store._use_fallback
        emb = store._get_embedding("hello")
        assert emb == store.embedder("hello")


def test_create_ephemeral_embedded_mode(kuzu_store_embedded):
    assert not kuzu_store_embedded._store._use_fallback
