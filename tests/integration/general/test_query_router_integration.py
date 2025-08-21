import pytest

from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


class InMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self.items = {}

    def store(self, item: MemoryItem) -> str:
        item_id = item.id or str(len(self.items))
        item.id = item_id
        self.items[item_id] = item
        return item_id

    def retrieve(self, item_id: str):
        return self.items.get(item_id)

    def search(self, query: dict):
        return list(self.items.values())

    def delete(self, item_id: str) -> bool:
        return self.items.pop(item_id, None) is not None

    def begin_transaction(self, transaction_id: str | None = None):
        pass

    def commit_transaction(self, transaction_id: str | None = None):
        pass

    def rollback_transaction(self, transaction_id: str | None = None):
        pass

    def is_transaction_active(self, transaction_id: str) -> bool:
        return False


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

    @pytest.mark.medium
    def test_direct_query(self, manager):
        self._populate(manager)
        results = manager.route_query("apple", store="vector", strategy="direct")
        assert len(results) == 1
        assert results[0].content == "apple vector"
        assert results[0].metadata.get("source_store") == "vector"

    @pytest.mark.medium
    def test_cross_store_query(self, manager):
        self._populate(manager)
        results = manager.route_query("apple", strategy="cross")
        assert set(results.keys()) >= {"vector", "tinydb", "document"}
        for store, items in results.items():
            for item in items:
                assert item.metadata.get("source_store") == store

    @pytest.mark.medium
    def test_cross_store_query_subset(self, manager):
        self._populate(manager)
        results = manager.route_query(
            "apple", strategy="cross", stores=["vector", "tinydb"]
        )
        assert set(results.keys()) == {"vector", "tinydb"}

    @pytest.mark.medium
    def test_federated_query(self, manager):
        self._populate(manager)
        results = manager.route_query("apple", strategy="federated")
        assert len(results) == 3
        stores = {item.metadata.get("source_store") for item in results}
        assert stores == {"vector", "tinydb", "document"}
