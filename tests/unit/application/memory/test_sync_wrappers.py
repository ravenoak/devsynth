import pytest
from devsynth.application.memory.context_manager import InMemoryStore
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType


def _manager():
    adapters = {"a": InMemoryStore(), "b": InMemoryStore()}
    return MemoryManager(adapters=adapters)


def test_cross_store_query_and_update_wrappers():
    manager = _manager()
    item_a = MemoryItem(id="x", content="foo", memory_type=MemoryType.CODE)
    manager.adapters["a"].store(item_a)
    item_b = MemoryItem(id="y", content="foo", memory_type=MemoryType.CODE)
    manager.adapters["b"].store(item_b)

    results = manager.cross_store_query("foo")
    assert set(results.keys()) == {"a", "b"}

    new_item = MemoryItem(id="z", content="bar", memory_type=MemoryType.CODE)
    assert manager.update_item("a", new_item) is True
    manager.queue_update("a", new_item)
    manager.flush_updates()
    assert manager.adapters["b"].retrieve("z") is not None

    stats = manager.get_sync_stats()
    assert stats["synchronized"] >= 1
