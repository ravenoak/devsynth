import asyncio
import importlib.util
import pathlib
import sys
import types
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

import pytest

SRC_ROOT = pathlib.Path(__file__).resolve().parents[3] / "src"


def _load_module(path: pathlib.Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name}")
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    exec_module = getattr(loader, "exec_module", None)
    if exec_module is None:
        raise RuntimeError(f"Loader for {name} lacks exec_module")
    exec_module(module)
    return module


PACKAGE_PATH = SRC_ROOT / "devsynth/application/memory"
memory_manager_module = _load_module(
    PACKAGE_PATH / "memory_manager.py", "devsynth.application.memory.memory_manager"
)
vector_adapter_module = _load_module(
    PACKAGE_PATH / "adapters/vector_memory_adapter.py",
    "devsynth.application.memory.adapters.vector_memory_adapter",
)
dto_module = _load_module(PACKAGE_PATH / "dto.py", "devsynth.application.memory.dto")
MemoryManager = memory_manager_module.MemoryManager
VectorMemoryAdapter = vector_adapter_module.VectorMemoryAdapter
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


class InMemoryStore(MemoryStore):
    """Simple in-memory store for testing purposes."""

    def __init__(self) -> None:
        self.items: dict[str, MemoryItem] = {}
        self._active = False

    def store(self, item: MemoryItem) -> str:
        item_id = item.id or str(len(self.items))
        item.id = item_id
        self.items[item_id] = item
        return item_id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        return self.items.get(item_id)

    def search(self, query: Mapping[str, object] | Any) -> list[MemoryItem]:
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
    def manager(self, monkeypatch) -> Any:
        fake_pkg = types.ModuleType("devsynth.application.memory")
        fake_pkg.__path__ = [str(PACKAGE_PATH)]
        monkeypatch.setitem(sys.modules, "devsynth.application.memory", fake_pkg)
        adapters = {"vector": VectorMemoryAdapter(), "tinydb": InMemoryStore()}
        return MemoryManager(adapters=adapters)

    def _add_items(self, manager: Any) -> None:
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
        assert "vector" in results["by_store"] and "tinydb" in results["by_store"]
        assert len(results["by_store"]["vector"]["records"]) == 1
        assert len(results["by_store"]["tinydb"]["records"]) == 1

    @pytest.mark.medium
    def test_cross_store_query_returns_memory_records(self, manager):
        """Cross store queries normalize adapter payloads into DTOs."""

        self._add_items(manager)
        grouped = manager.sync_manager.cross_store_query("apple")

        assert grouped["query"] == "apple"
        vector_payload = grouped["by_store"]["vector"]
        tinydb_payload = grouped["by_store"]["tinydb"]

        assert vector_payload["store"] == "vector"
        assert tinydb_payload["store"] == "tinydb"

        assert all(
            record.__class__.__name__ == "MemoryRecord"
            for record in vector_payload["records"]
        )
        assert all(
            record.__class__.__name__ == "MemoryRecord"
            for record in tinydb_payload["records"]
        )

        combined = grouped.get("combined")
        assert combined is not None and all(
            record.__class__.__name__ == "MemoryRecord" for record in combined
        )
        assert {record.source for record in combined} == {"vector", "tinydb"}

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
        assert len(cached["by_store"]["tinydb"]["records"]) == 1
        assert manager.sync_manager.get_cache_size() == 1
        manager.sync_manager.clear_cache()
        refreshed = manager.sync_manager.cross_store_query("apple")
        assert len(refreshed["by_store"]["tinydb"]["records"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.medium
    async def test_cross_store_query_async_succeeds(self, manager):
        """Test that asynchronous cross-store query returns results."""
        self._add_items(manager)
        results = await manager.sync_manager.cross_store_query_async("apple")
        assert "vector" in results["by_store"] and "tinydb" in results["by_store"]


class TestSyncManagerConcurrentUpdates:
    """Tests for concurrent update scenarios."""

    @pytest.fixture
    def manager(self) -> Any:
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

        async def worker(itm: MemoryItem) -> None:
            manager.sync_manager.queue_update("a", itm)

        await asyncio.gather(*(worker(it) for it in items))
        await manager.sync_manager.wait_for_async()
        for it in items:
            assert manager.adapters["b"].retrieve(it.id) is not None
        assert manager.sync_manager.stats.synchronized == len(items)

    @pytest.mark.asyncio
    @pytest.mark.medium
    async def test_async_queue_normalizes_records_before_flush(self, manager):
        item = MemoryItem(id="", content="queued", memory_type=MemoryType.CODE)

        manager.sync_manager.queue_update("a", item)

        with manager.sync_manager._queue_lock:  # noqa: SLF001 - validating DTO payloads
            queued_snapshot = list(manager.sync_manager._queue)

        assert len(queued_snapshot) == 1
        entry = queued_snapshot[0]
        assert entry["store"] == "a"
        assert entry["record"].__class__.__name__ == "MemoryRecord"
        assert entry["record"].item.content == "queued"
        assert entry["record"].item.id

        await manager.sync_manager.wait_for_async()

        assert manager.sync_manager._queue == []
        replicated = manager.adapters["b"].retrieve(entry["record"].item.id)
        assert isinstance(replicated, MemoryItem)

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

        async def worker(itm: MemoryItem) -> None:
            manager.sync_manager.queue_update("a", itm)

        await asyncio.gather(worker(newer), worker(newest))
        await manager.sync_manager.wait_for_async()
        result = manager.adapters["b"].retrieve("x")
        assert result.content == "newest"
        assert len(manager.sync_manager.conflict_log) == 1
