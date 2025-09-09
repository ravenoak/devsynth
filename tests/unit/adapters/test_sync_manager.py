import asyncio
import importlib.util
import pathlib
import sys
import types
from datetime import datetime, timedelta

import pytest

SRC_ROOT = pathlib.Path(__file__).resolve().parents[3] / "src"


def _load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PACKAGE_PATH = SRC_ROOT / "devsynth/application/memory"
memory_manager_module = _load_module(
    PACKAGE_PATH / "memory_manager.py", "devsynth.application.memory.memory_manager"
)
vector_adapter_module = _load_module(
    PACKAGE_PATH / "adapters/vector_memory_adapter.py",
    "devsynth.application.memory.adapters.vector_memory_adapter",
)
MemoryManager = memory_manager_module.MemoryManager
VectorMemoryAdapter = vector_adapter_module.VectorMemoryAdapter
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


class InMemoryStore(MemoryStore):
    """Simple in-memory store for testing purposes."""

    def __init__(self) -> None:
        self.items = {}
        self._active = False

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
        self._active = True

    def commit_transaction(self, transaction_id: str | None = None):
        self._active = False

    def rollback_transaction(self, transaction_id: str | None = None):
        self._active = False

    def is_transaction_active(self) -> bool:
        return self._active


class TestSyncManagerCrossStoreQuery:
    """Tests for the SyncManagerCrossStoreQuery component.

    ReqID: N/A"""

    @pytest.fixture
    def manager(self, monkeypatch):
        fake_pkg = types.ModuleType("devsynth.application.memory")
        fake_pkg.__path__ = [str(PACKAGE_PATH)]
        monkeypatch.setitem(sys.modules, "devsynth.application.memory", fake_pkg)
        adapters = {"vector": VectorMemoryAdapter(), "tinydb": InMemoryStore()}
        return MemoryManager(adapters=adapters)

    def _add_items(self, manager: MemoryManager):
        vec = MemoryVector(
            id="",
            content="apple",
            embedding=manager._embed_text("apple"),
            metadata={"memory_type": MemoryType.CODE.value},
        )
        manager.adapters["vector"].store_vector(vec)
        item = MemoryItem(
            id="", content="apple", memory_type=MemoryType.CODE, metadata={}
        )
        manager.adapters["tinydb"].store(item)

    @pytest.mark.medium
    def test_cross_store_query_returns_results_succeeds(self, manager):
        """Test that cross store query returns results succeeds.

        ReqID: N/A"""
        self._add_items(manager)
        results = manager.sync_manager.cross_store_query("apple")
        assert "vector" in results and "tinydb" in results
        assert len(results["vector"]) == 1
        assert len(results["tinydb"]) == 1

    @pytest.mark.medium
    def test_query_results_cached_succeeds(self, manager):
        """Test that query results cached succeeds.

        ReqID: N/A"""
        self._add_items(manager)
        manager.sync_manager.cross_store_query("apple")
        new_item = MemoryItem(
            id="", content="apple second", memory_type=MemoryType.CODE, metadata={}
        )
        manager.adapters["tinydb"].store(new_item)
        cached = manager.sync_manager.cross_store_query("apple")
        assert len(cached["tinydb"]) == 1
        assert manager.sync_manager.get_cache_size() == 1
        manager.sync_manager.clear_cache()
        refreshed = manager.sync_manager.cross_store_query("apple")
        assert len(refreshed["tinydb"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.medium
    async def test_cross_store_query_async_succeeds(self, manager):
        """Test that asynchronous cross-store query returns results."""
        self._add_items(manager)
        results = await manager.sync_manager.cross_store_query_async("apple")
        assert "vector" in results and "tinydb" in results


class TestSyncManagerConcurrentUpdates:
    """Tests for concurrent update scenarios."""

    @pytest.fixture
    def manager(self):
        adapters = {"a": InMemoryStore(), "b": InMemoryStore()}
        manager = MemoryManager(adapters=adapters)
        manager.sync_manager = memory_manager_module.SyncManager(
            manager, async_mode=True
        )
        return manager

    @pytest.mark.asyncio
    @pytest.mark.medium
    async def test_queue_updates_from_multiple_tasks_succeeds(self, manager):
        items = [
            MemoryItem(id=str(i), content=str(i), memory_type=MemoryType.CODE)
            for i in range(5)
        ]

        async def worker(itm):
            manager.sync_manager.queue_update("a", itm)

        await asyncio.gather(*(worker(it) for it in items))
        await manager.sync_manager.wait_for_async()
        for it in items:
            assert manager.adapters["b"].retrieve(it.id) is not None
        assert manager.sync_manager.stats["synchronized"] == len(items)

    @pytest.mark.asyncio
    @pytest.mark.medium
    async def test_conflict_resolution_with_concurrent_updates(self, manager):
        base_time = datetime.now()
        original = MemoryItem(
            id="x", content="orig", memory_type=MemoryType.CODE, created_at=base_time
        )
        manager.adapters["a"].store(original)
        newer = MemoryItem(
            id="x",
            content="newer",
            memory_type=MemoryType.CODE,
            created_at=base_time + timedelta(seconds=1),
        )
        newest = MemoryItem(
            id="x",
            content="newest",
            memory_type=MemoryType.CODE,
            created_at=base_time + timedelta(seconds=2),
        )

        async def worker(itm):
            manager.sync_manager.queue_update("a", itm)

        await asyncio.gather(worker(newer), worker(newest))
        await manager.sync_manager.wait_for_async()
        result = manager.adapters["b"].retrieve("x")
        assert result.content == "newest"
        assert len(manager.sync_manager.conflict_log) == 1
