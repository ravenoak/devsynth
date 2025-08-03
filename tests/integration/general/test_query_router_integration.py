import pytest

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.context_manager import InMemoryStore
from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


class TestQueryRouterIntegration:
    @pytest.fixture
    def manager(self):
        adapters = {
            "vector": VectorMemoryAdapter(),
            "tinydb": InMemoryStore(),
            "document": InMemoryStore(),
        }
        return MemoryManager(adapters=adapters)

    def _populate(self, manager: MemoryManager):
        vec = MemoryVector(
            id="v1",
            content="apple vector",
            embedding=manager._embed_text("apple vector"),
            metadata={"memory_type": MemoryType.CODE.value},
        )
        manager.adapters["vector"].store_vector(vec)
        manager.adapters["tinydb"].store(
            MemoryItem(id="t1", content="apple tinydb", memory_type=MemoryType.CODE)
        )
        manager.adapters["document"].store(
            MemoryItem(id="d1", content="apple document", memory_type=MemoryType.CODE)
        )

    def test_direct_query(self, manager):
        self._populate(manager)
        results = manager.route_query("apple", store="vector", strategy="direct")
        assert len(results) == 1
        assert results[0].content == "apple vector"
        assert results[0].metadata.get("source_store") == "vector"

    def test_cross_store_query(self, manager):
        self._populate(manager)
        results = manager.route_query("apple", strategy="cross")
        assert set(results.keys()) >= {"vector", "tinydb", "document"}
        for store, items in results.items():
            for item in items:
                assert item.metadata.get("source_store") == store

    @pytest.mark.medium
    def test_federated_query(self, manager):
        self._populate(manager)
        results = manager.route_query("apple", strategy="federated")
        assert len(results) == 3
        stores = {item.metadata.get("source_store") for item in results}
        assert stores == {"vector", "tinydb", "document"}
