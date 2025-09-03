import pytest

from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.context_manager import (
    InMemoryStore,
    SimpleContextManager,
)
from devsynth.application.memory.kuzu_store import KuzuStore

pytestmark = [
    pytest.mark.memory_intensive,
    pytest.mark.isolation,
]


@pytest.mark.medium
def test_create_for_testing_defaults_to_memory():
    adapter = MemorySystemAdapter.create_for_testing()
    assert adapter.storage_type == "memory"
    assert isinstance(adapter.memory_store, InMemoryStore)
    assert isinstance(adapter.context_manager, SimpleContextManager)
    assert adapter.vector_store is None


@pytest.mark.medium
def test_create_for_testing_file_does_not_create_path(tmp_path):
    adapter = MemorySystemAdapter.create_for_testing(
        storage_type="file", memory_path=tmp_path
    )
    assert adapter.storage_type == "file"
    assert adapter.memory_path == str(tmp_path)
    assert not (tmp_path / "memory.json").exists()


@pytest.mark.medium
def test_create_for_testing_kuzu_avoids_attribute_error(monkeypatch):
    monkeypatch.setattr(KuzuMemoryStore, "__abstractmethods__", frozenset())
    monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())
    adapter = MemorySystemAdapter.create_for_testing(storage_type="kuzu")
    assert adapter.storage_type == "kuzu"
