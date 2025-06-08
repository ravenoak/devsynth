import pytest

from devsynth.ports.memory_store import MemoryStore


class DummyStore(MemoryStore):
    def add(self, item):
        raise NotImplementedError

    def get(self, item_id):
        raise NotImplementedError

    def search(self, query, top_k=5):
        raise NotImplementedError

    def all(self):
        raise NotImplementedError

    def remove(self, item_id):
        raise NotImplementedError


def test_memory_store_abstract_methods():
    store = DummyStore()
    with pytest.raises(NotImplementedError):
        store.add({})
