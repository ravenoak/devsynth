"""Tests for :class:`KuzuMemoryStore`."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError

ROOT = Path(__file__).resolve().parents[3]
KUZU_STORE_PATH = ROOT / "src/devsynth/application/memory/kuzu_store.py"
KUZU_ADAPTER_PATH = ROOT / "src/devsynth/adapters/kuzu_memory_store.py"


@pytest.fixture
def KuzuMemoryStoreClass(monkeypatch):
    """Load ``KuzuMemoryStore`` and its dependencies from source."""
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")

    # Mock settings module with all required attributes - must be done before any imports
    fake_settings = ModuleType("devsynth.config.settings")

    # Create a proper settings object
    class FakeSettings:
        def __init__(self):
            self.kuzu_db_path = None
            self.kuzu_embedded = True

    fake_settings.get_settings = lambda reload=False, **kwargs: FakeSettings()
    fake_settings.ensure_path_exists = lambda path, create=True: path
    fake_settings.kuzu_embedded = True
    fake_settings.DEFAULT_KUZU_EMBEDDED = True
    fake_settings.get_llm_settings = lambda reload=False, **kwargs: {}

    # Set the module in sys.modules before importing anything that might use it
    monkeypatch.setitem(sys.modules, "devsynth.config.settings", fake_settings)

    # Also set it in the parent namespace to be safe
    import devsynth.config

    devsynth.config.settings = fake_settings

    fake_pkg = ModuleType("devsynth.application.memory")
    fake_pkg.__path__ = [str(KUZU_STORE_PATH.parent)]
    monkeypatch.setitem(sys.modules, "devsynth.application.memory", fake_pkg)
    spec_store = importlib.util.spec_from_file_location(
        "devsynth.application.memory.kuzu_store", KUZU_STORE_PATH
    )
    kuzu_store_mod = importlib.util.module_from_spec(spec_store)
    spec_store.loader.exec_module(kuzu_store_mod)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.memory.kuzu_store", kuzu_store_mod
    )
    monkeypatch.setattr(kuzu_store_mod.KuzuStore, "__abstractmethods__", frozenset())
    spec_adapter = importlib.util.spec_from_file_location(
        "devsynth.adapters.kuzu_memory_store", KUZU_ADAPTER_PATH
    )
    kuzu_memory_store = importlib.util.module_from_spec(spec_adapter)
    spec_adapter.loader.exec_module(kuzu_memory_store)
    monkeypatch.setattr(
        kuzu_memory_store.KuzuMemoryStore, "__abstractmethods__", frozenset()
    )
    return kuzu_memory_store.KuzuMemoryStore


@pytest.mark.medium
def test_store_and_search_succeeds(tmp_path, KuzuMemoryStoreClass, monkeypatch):
    """Test that store and search succeeds.

    ReqID: N/A"""
    store = KuzuMemoryStoreClass(
        persist_directory=str(tmp_path), use_provider_system=True
    )
    with patch.object(store, "_get_embedding", return_value=[0.1, 0.2, 0.3]):
        item = MemoryItem(
            id="t1", content="hello world", memory_type=MemoryType.WORKING
        )
        store.store(item)
        results = store.search({"query": "hello", "top_k": 1})
    assert len(results) == 1
    assert results[0].id == "t1"


@pytest.mark.medium
def test_create_ephemeral_fallback(KuzuMemoryStoreClass, monkeypatch):
    monkeypatch.setitem(sys.modules, "kuzu", None)
    store = KuzuMemoryStoreClass.create_ephemeral()
    try:
        assert store._store._use_fallback
    finally:
        store.cleanup()


@pytest.mark.medium
def test_create_ephemeral_embedded(KuzuMemoryStoreClass, monkeypatch):
    class Database:
        def __init__(self, path):
            pass

    class Connection:
        def __init__(self, db):
            pass

        def execute(self, *args, **kwargs):
            return None

    fake = ModuleType("kuzu")
    fake.Database = Database
    fake.Connection = Connection
    monkeypatch.setitem(sys.modules, "kuzu", fake)
    store = KuzuMemoryStoreClass.create_ephemeral()
    try:
        assert not store._store._use_fallback
    finally:
        store.cleanup()


@pytest.mark.medium
def test_store_failure_raises_memory_store_error(tmp_path, KuzuMemoryStoreClass):
    store = KuzuMemoryStoreClass(
        persist_directory=str(tmp_path), use_provider_system=False
    )
    item = MemoryItem(id="fail", content="oops", memory_type=MemoryType.WORKING)
    with (
        patch.object(store.vector, "store_vector", side_effect=OSError("disk failure")),
        patch.object(
            store.vector, "delete_vector", side_effect=OSError("cleanup error")
        ) as del_mock,
        patch.object(
            store._store, "delete", side_effect=OSError("cleanup error")
        ) as store_del_mock,
    ):
        with pytest.raises(MemoryStoreError):
            store.store(item)
        assert del_mock.called
        assert store_del_mock.called


@pytest.mark.medium
def test_delete_returns_false_on_error(tmp_path, KuzuMemoryStoreClass):
    store = KuzuMemoryStoreClass(
        persist_directory=str(tmp_path), use_provider_system=False
    )
    item = MemoryItem(id="t1", content="hi", memory_type=MemoryType.WORKING)
    store.store(item)
    with (
        patch.object(store.vector, "delete_vector", return_value=True) as vec_del,
        patch.object(store._store, "delete", side_effect=OSError("fail")) as store_del,
    ):
        assert not store.delete(item.id)
        vec_del.assert_called_once_with(item.id)
        store_del.assert_called_once_with(item.id)
