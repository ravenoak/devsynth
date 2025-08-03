"""Tests for :class:`KuzuMemoryStore`."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType

ROOT = Path(__file__).resolve().parents[3]
KUZU_STORE_PATH = ROOT / "src/devsynth/application/memory/kuzu_store.py"
KUZU_ADAPTER_PATH = ROOT / "src/devsynth/adapters/kuzu_memory_store.py"


@pytest.fixture
def KuzuMemoryStoreClass(monkeypatch):
    """Load ``KuzuMemoryStore`` and its dependencies from source."""
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


def test_create_ephemeral_fallback(KuzuMemoryStoreClass, monkeypatch):
    monkeypatch.setitem(sys.modules, "kuzu", None)
    store = KuzuMemoryStoreClass.create_ephemeral()
    try:
        assert store._store._use_fallback
    finally:
        store.cleanup()


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
