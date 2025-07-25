import sys
import types
from unittest.mock import patch

import pytest

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType

# Provide a dummy kuzu module if the dependency is not installed
sys.modules.setdefault("kuzu", types.ModuleType("kuzu"))



@pytest.fixture
def kuzu_store(ephemeral_kuzu_store):
    return ephemeral_kuzu_store


@pytest.fixture(autouse=True)
def mock_embed():
    with patch(
        "devsynth.adapters.kuzu_memory_store.embed", return_value=[[0.1, 0.2, 0.3]]
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
