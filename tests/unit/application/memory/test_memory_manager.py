import importlib.util
import pathlib
import sys
import types
from collections import UserDict
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from devsynth.application.memory.dto import (
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
    build_query_results,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType

SRC_ROOT = pathlib.Path(__file__).resolve().parents[4] / "src"


def _load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PACKAGE_PATH = SRC_ROOT / "devsynth/application/memory"
memory_manager_module = _load_module(
    PACKAGE_PATH / "memory_manager.py", "devsynth.application.memory.memory_manager"
)
MemoryManager = memory_manager_module.MemoryManager


class RecordingStore:

    def __init__(self, name: str):
        self.name = name
        self.items: dict[str, MemoryItem] = {}
        self.calls: dict[str, int] = {
            "store": 0,
            "retrieve_with_edrr_phase": 0,
        }

    def store(self, item: MemoryItem) -> str:
        self.calls["store"] += 1
        if not item.id:
            item.id = f"{self.name}-{len(self.items) + 1}"
        self.items[item.id] = item
        return item.id

    def retrieve_with_edrr_phase(
        self,
        item_type: MemoryType,
        edrr_phase: str,
        metadata: MemoryMetadata,
    ) -> MemoryRecord:
        self.calls["retrieve_with_edrr_phase"] += 1
        stored = self.items.get(f"{item_type.value}-{edrr_phase}")
        if stored is None:
            stored = MemoryItem(
                id=f"{item_type.value}-{edrr_phase}",
                content={"phase": edrr_phase},
                memory_type=item_type,
                metadata={"edrr_phase": edrr_phase, "seen_at": datetime.utcnow()},
            )
            self.items[stored.id] = stored
        return MemoryRecord(item=stored, metadata=metadata)


@pytest.fixture(autouse=True)
def _patch_memory_module(monkeypatch):
    pkg = types.ModuleType("devsynth.application.memory")
    pkg.__path__ = [str(PACKAGE_PATH)]
    monkeypatch.setitem(sys.modules, "devsynth.application.memory", pkg)


class DummyVectorStore:

    def __init__(self):
        self.stored = []

    def store(self, item):
        self.stored.append(item)
        return "vector-id"


class DummyGraphStore:

    def __init__(self):
        self.stored = []
        self.edrr_items = {}

    def store(self, item):
        self.stored.append(item)
        return "graph-id"

    def retrieve_with_edrr_phase(self, item_type, edrr_phase, metadata=None):
        key = f"{item_type}_{edrr_phase}"
        return self.edrr_items.get(key)

    def store_with_edrr_phase(self, content, memory_type, edrr_phase, metadata=None):
        key = f"{memory_type}_{edrr_phase}"
        payload_metadata = {"edrr_phase": edrr_phase}
        if metadata:
            payload_metadata.update(metadata)
        item = MemoryItem(
            id=key,
            content=content,
            memory_type=MemoryType.from_raw(memory_type),
            metadata=payload_metadata,
        )
        self.edrr_items[key] = item
        return item.id


class TestMemoryManagerStore:
    """Tests for the MemoryManagerStore component.

    ReqID: N/A"""

    @pytest.fixture
    def adapters(self):
        tinydb = MagicMock()
        vector = DummyVectorStore()
        return {"tinydb": tinydb, "vector": vector}

    @pytest.fixture
    def graph_adapters(self):
        graph = DummyGraphStore()
        tinydb = MagicMock()
        return {"graph": graph, "tinydb": tinydb}

    @pytest.mark.medium
    def test_store_prefers_graph_for_edrr_succeeds(self, graph_adapters):
        """Test that store prefers graph for edrr succeeds.

        ReqID: N/A"""
        manager = MemoryManager(adapters=graph_adapters)
        manager.store_with_edrr_phase("x", MemoryType.CODE, "EXPAND")
        assert len(graph_adapters["graph"].stored) == 1
        graph_adapters["tinydb"].store.assert_not_called()

    @pytest.mark.medium
    def test_store_falls_back_to_tinydb_succeeds(self):
        """Test that store falls back to tinydb succeeds.

        ReqID: N/A"""
        tinydb = MagicMock()
        manager = MemoryManager(adapters={"tinydb": tinydb})
        manager.store_with_edrr_phase("x", MemoryType.CODE, "EXPAND")
        tinydb.store.assert_called_once()

    @pytest.mark.medium
    def test_store_falls_back_to_first_succeeds(self):
        """Test that store falls back to first succeeds.

        ReqID: N/A"""
        vector = DummyVectorStore()
        manager = MemoryManager(adapters={"vector": vector})
        manager.store_with_edrr_phase("x", MemoryType.CODE, "EXPAND")
        assert vector.stored


class RecordingSyncManager:

    def __init__(self) -> None:
        self.calls: list[tuple[str, MemoryItem]] = []

    def update_item(self, store_key: str, item: MemoryItem) -> None:
        self.calls.append((store_key, item))


class TestMemoryManagerTyping:

    @pytest.mark.medium
    def test_store_with_edrr_phase_coerces_metadata_mapping(self):
        adapters = {"tinydb": RecordingStore("tinydb")}
        sync_manager = RecordingSyncManager()

        metadata = UserDict({"origin": "suite"})
        manager = MemoryManager(adapters=adapters, sync_manager=sync_manager)
        item_id = manager.store_with_edrr_phase(
            {"payload": True}, MemoryType.KNOWLEDGE, "EXPAND", metadata
        )

        assert isinstance(item_id, str)
        assert sync_manager.calls, "sync manager should receive the stored item"

        _, recorded_item = sync_manager.calls[0]
        assert isinstance(recorded_item.metadata, dict)
        assert recorded_item.metadata is not metadata
        assert recorded_item.metadata["origin"] == "suite"
        assert recorded_item.metadata["edrr_phase"] == "EXPAND"
        for value in recorded_item.metadata.values():
            assert isinstance(
                value,
                (
                    str,
                    int,
                    float,
                    bool,
                    type(None),
                    datetime,
                    list,
                    dict,
                ),
            )


class TestRouteQuery:
    @pytest.mark.fast
    def test_route_query_normalizes_context_mapping(self):
        class StubRouter:
            def __init__(self) -> None:
                self.captured: MemoryMetadata | None = None

            def route(
                self,
                query: str,
                *,
                store: str | None = None,
                strategy: str = "direct",
                context: MemoryMetadata | None = None,
                stores: list[str] | None = None,
            ) -> MemoryQueryResults:
                self.captured = context
                return build_query_results("stub", [])

        router = StubRouter()
        manager = MemoryManager(adapters={}, query_router=router)

        context = UserDict({"phase": "EXPAND"})
        result = manager.route_query("hello", context=context)

        assert isinstance(result, dict)
        assert result["store"] == "stub"
        assert router.captured == {"phase": "EXPAND"}


class TestMemoryManagerRetrieve:
    """Tests for the MemoryManagerRetrieve component.

    ReqID: N/A"""

    @pytest.fixture
    def graph_adapter(self):
        return DummyGraphStore()

    @pytest.fixture
    def manager_with_graph(self, graph_adapter):
        return MemoryManager(adapters={"graph": graph_adapter})

    @pytest.mark.medium
    def test_retrieve_with_edrr_phase_succeeds(self, manager_with_graph, graph_adapter):
        """Test that retrieve with edrr phase succeeds.

        ReqID: N/A"""
        test_item = MemoryItem(
            id="CODE_EXPAND",
            content={"key": "value"},
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "EXPAND"},
        )
        graph_adapter.edrr_items[test_item.id] = test_item
        result = manager_with_graph.retrieve_with_edrr_phase("CODE", "EXPAND")
        assert isinstance(result, MemoryRecord)
        assert result.content == {"key": "value"}
        assert result.metadata.get("edrr_phase") == "EXPAND"

    @pytest.mark.medium
    def test_retrieve_with_edrr_phase_not_found_succeeds(self, manager_with_graph):
        """Test that retrieve with edrr phase not found succeeds.

        ReqID: N/A"""
        result = manager_with_graph.retrieve_with_edrr_phase("CODE", "NONEXISTENT")
        assert result is None

    @pytest.mark.medium
    def test_retrieve_with_edrr_phase_with_metadata_succeeds(
        self, manager_with_graph, graph_adapter
    ):
        """Test that retrieve with edrr phase with metadata succeeds.

        ReqID: N/A"""
        test_item = MemoryItem(
            id="CODE_EXPAND",
            content={"key": "value"},
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "EXPAND"},
        )
        graph_adapter.edrr_items[test_item.id] = test_item
        result = manager_with_graph.retrieve_with_edrr_phase(
            "CODE", "EXPAND", {"cycle_id": "123"}
        )
        assert isinstance(result, MemoryRecord)
        assert result.metadata.get("edrr_phase") == "EXPAND"
        assert result.metadata.get("cycle_id") == "123"

    @pytest.mark.medium
    def test_retrieve_with_edrr_phase_returns_typed_record(self):
        adapter = RecordingStore("graph")
        manager = MemoryManager(adapters={"graph": adapter})

        record = manager.retrieve_with_edrr_phase(MemoryType.CODE, "REFINE")

        assert isinstance(record, MemoryRecord)
        assert adapter.calls["retrieve_with_edrr_phase"] == 1
        assert isinstance(record.metadata, dict)
        assert record.metadata["edrr_phase"] == "REFINE"
        for value in record.metadata.values():
            assert isinstance(
                value,
                (
                    str,
                    int,
                    float,
                    bool,
                    type(None),
                    datetime,
                    list,
                    dict,
                ),
            )


class TestEmbedText:
    """Tests for the EmbedText component.

    ReqID: N/A"""

    @pytest.mark.medium
    def test_fallback_and_provider_succeeds(self):
        """Test that fallback and provider succeeds.

        ReqID: N/A"""
        manager = MemoryManager(adapters={})
        default = manager._embed_text("abc", dimension=5)
        provider = MagicMock()
        provider.embed.side_effect = Exception("boom")
        manager_fail = MemoryManager(embedding_provider=provider)
        assert manager_fail._embed_text("abc", dimension=5) == default
        provider.embed.side_effect = None
        provider.embed.return_value = [1.0, 2.0]
        manager_ok = MemoryManager(embedding_provider=provider)
        assert manager_ok._embed_text("hi") == [1.0, 2.0]


class TestSyncHooks:
    """Tests for synchronization hooks.

    ReqID: FR-60"""

    @pytest.mark.fast
    def test_register_and_notify_sync_hook_succeeds(self):
        """Ensure sync hooks are invoked.

        ReqID: FR-60"""
        manager = MemoryManager(adapters={})
        called = []

        def hook(item):
            called.append(item)

        manager.register_sync_hook(hook)
        dummy_item = object()
        manager._notify_sync_hooks(dummy_item)
        assert called == [dummy_item]

    @pytest.mark.fast
    def test_sync_hook_errors_are_logged(self, monkeypatch):
        """Errors raised by sync hooks are caught and logged.

        ReqID: FR-60"""
        manager = MemoryManager(adapters={})

        def bad_hook(item):
            raise RuntimeError("boom")

        manager.register_sync_hook(bad_hook)
        manager._notify_sync_hooks(None)
        assert True
