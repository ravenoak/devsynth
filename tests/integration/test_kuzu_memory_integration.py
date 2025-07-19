import sys
import types
import tempfile
import shutil
from unittest.mock import patch

import pytest

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType

# Provide a dummy kuzu module if the dependency is not installed
sys.modules.setdefault("kuzu", types.ModuleType("kuzu"))


@pytest.fixture
def temp_dir():
    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        shutil.rmtree(path)


@pytest.fixture(autouse=True)
def mock_embed():
    with patch(
        "devsynth.adapters.kuzu_memory_store.embed", return_value=[[0.1, 0.2, 0.3]]
    ):
        yield


def test_kuzu_memory_vector_integration_succeeds(temp_dir):
    config = {
        "memory_store_type": "kuzu",
        "memory_file_path": temp_dir,
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
