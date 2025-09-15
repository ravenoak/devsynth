"""Fast in-memory and temp-file tests for memory modules.

ReqID: N/A
"""

import pytest

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.adapters.enhanced_graph_memory_adapter import (
    EnhancedGraphMemoryAdapter,
)
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.context_manager import (
    InMemoryStore,
    SimpleContextManager,
)
from devsynth.application.memory.fallback import FallbackStore
from devsynth.application.memory.json_file_store import JSONFileStore
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.recovery import MemorySnapshot
from devsynth.application.memory.sync_manager import DummyTransactionContext
from devsynth.domain.models.memory import MemoryItem, MemoryType


class _DummyStore:
    """Minimal in-memory store for fallback testing."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.items: dict[str, MemoryItem] = {}

    def store(self, item: MemoryItem) -> str:
        if self.fail:
            raise RuntimeError("fail")
        self.items[item.id] = item
        return item.id


@pytest.mark.fast
def test_graph_memory_adapter_in_memory_round_trip() -> None:
    """GraphMemoryAdapter stores and retrieves items in-memory.

    ReqID: N/A"""
    adapter = GraphMemoryAdapter()
    item = MemoryItem(id="a", content="c", memory_type=MemoryType.CODE)
    item_id = adapter.store(item)
    retrieved = adapter.retrieve(item_id)
    assert retrieved is not None
    assert retrieved.content == "c"


@pytest.mark.fast
def test_enhanced_graph_memory_adapter_edrr_round_trip() -> None:
    """Enhanced adapter persists EDRR metadata in-memory.

    ReqID: N/A"""
    adapter = EnhancedGraphMemoryAdapter()
    item_id = adapter.store_with_edrr_phase("x", MemoryType.CODE, "EXPAND")
    item = adapter.retrieve(item_id)
    assert item is not None
    assert item.metadata.get("edrr_phase") == "EXPAND"


@pytest.mark.fast
def test_memory_manager_sync_hooks_fire() -> None:
    """MemoryManager invokes registered sync hooks.

    ReqID: N/A"""
    manager = MemoryManager(adapters={})
    calls: list[MemoryItem | None] = []
    manager.register_sync_hook(lambda item: calls.append(item))
    manager._notify_sync_hooks(None)
    assert calls == [None]


@pytest.mark.fast
def test_dummy_transaction_context_commit_and_rollback() -> None:
    """DummyTransactionContext commits and rolls back.

    ReqID: N/A"""

    class Adapter:
        def begin_transaction(self):  # pragma: no cover - minimal implementation
            return None

        def commit_transaction(self, transaction_id: str) -> None:
            self.committed = True

        def rollback_transaction(self, transaction_id: str) -> None:
            self.rolled_back = True

    adapter1 = Adapter()
    ctx1 = DummyTransactionContext(adapter1, transaction_id="1")
    with ctx1:
        pass
    assert ctx1.committed is True

    adapter2 = Adapter()
    ctx2 = DummyTransactionContext(adapter2, transaction_id="2")
    with pytest.raises(RuntimeError):
        with ctx2:
            raise RuntimeError("boom")
    assert ctx2.rolled_back is True


@pytest.mark.fast
def test_memory_system_adapter_in_memory_components() -> None:
    """MemorySystemAdapter accepts preconfigured in-memory components.

    ReqID: N/A"""
    store = InMemoryStore()
    ctx_mgr = SimpleContextManager()
    adapter = MemorySystemAdapter(
        memory_store=store, context_manager=ctx_mgr, create_paths=False
    )
    assert adapter.memory_store is store
    assert adapter.context_manager is ctx_mgr


@pytest.mark.fast
def test_fallback_store_falls_back_on_failure() -> None:
    """FallbackStore uses backup store when primary fails.

    ReqID: N/A"""
    primary = _DummyStore(fail=True)
    backup = _DummyStore()
    fallback = FallbackStore(primary_store=primary, fallback_stores=[backup])
    item = MemoryItem(id="1", content="c", memory_type=MemoryType.CODE)
    item_id = fallback.store(item)
    assert item_id == "1"
    assert backup.items["1"].content == "c"


@pytest.mark.fast
def test_json_file_store_round_trip(tmp_path, monkeypatch) -> None:
    """JSONFileStore stores and retrieves from a temporary directory.

    ReqID: N/A"""
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "0")
    store = JSONFileStore(str(tmp_path))
    item = MemoryItem(id="x", content="y", memory_type=MemoryType.CODE)
    store.store(item)
    retrieved = store.retrieve("x")
    assert retrieved is not None
    assert retrieved.content == "y"


@pytest.mark.fast
def test_memory_snapshot_save_and_load(tmp_path, monkeypatch) -> None:
    """MemorySnapshot saves to and loads from a temporary file.

    ReqID: N/A"""
    monkeypatch.setattr(
        MemoryItem,
        "to_dict",
        lambda self: {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "metadata": self.metadata,
        },
        raising=False,
    )
    monkeypatch.setattr(
        MemoryItem,
        "from_dict",
        classmethod(
            lambda cls, data: MemoryItem(
                id=data["id"],
                content=data["content"],
                memory_type=MemoryType(data["memory_type"]),
                metadata=data.get("metadata"),
            )
        ),
        raising=False,
    )
    item = MemoryItem(id="1", content="v", memory_type=MemoryType.CODE)
    snapshot = MemorySnapshot(store_id="s", items=[item])
    path = snapshot.save(str(tmp_path))
    loaded = MemorySnapshot.load(path)
    restored = loaded.get_item("1")
    assert restored is not None
    assert restored.content == "v"
