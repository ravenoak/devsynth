import importlib
import shutil
import sys
import tempfile
import types
from unittest.mock import patch

import pytest

from tests.conftest import is_resource_available
from tests.fixtures.resources import (
    OPTIONAL_BACKEND_REQUIREMENTS,
    backend_import_reason,
    backend_skip_reason,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("kuzu")

_KUZU_EXTRAS = tuple(OPTIONAL_BACKEND_REQUIREMENTS["kuzu"]["extras"])

pytest.importorskip("kuzu", reason=backend_import_reason("kuzu", _KUZU_EXTRAS))

if not is_resource_available("kuzu"):
    pytest.skip(
        backend_skip_reason("kuzu", _KUZU_EXTRAS),
        allow_module_level=True,
    )

from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType

pytestmark = [pytest.mark.requires_resource("kuzu")]


@pytest.mark.medium
def test_memory_system_falls_back_when_kuzu_unavailable(monkeypatch):
    # Simulate kuzu not installed
    monkeypatch.setitem(sys.modules, "kuzu", None)
    import importlib

    import devsynth.application.memory.kuzu_store as kuzu_store

    importlib.reload(kuzu_store)
    import devsynth.adapters.kuzu_memory_store as km_store

    importlib.reload(km_store)
    monkeypatch.setattr(km_store, "embedding_functions", None)
    monkeypatch.setattr(km_store.KuzuMemoryStore, "__abstractmethods__", set())
    monkeypatch.setattr(
        km_store.KuzuMemoryStore, "begin_transaction", lambda self, tid: tid
    )
    monkeypatch.setattr(
        km_store.KuzuMemoryStore, "commit_transaction", lambda self, tid: True
    )
    monkeypatch.setattr(
        km_store.KuzuMemoryStore, "is_transaction_active", lambda self, tid: False
    )
    monkeypatch.setattr(
        km_store.KuzuMemoryStore, "rollback_transaction", lambda self, tid: None
    )
    import devsynth.adapters.memory.memory_adapter as mem_adapter

    monkeypatch.setattr(mem_adapter, "KuzuMemoryStore", km_store.KuzuMemoryStore)

    temp_dir = tempfile.mkdtemp()
    try:
        with patch(
            "devsynth.adapters.kuzu_memory_store.embed", return_value=[0.1, 0.2, 0.3]
        ):
            adapter = MemorySystemAdapter(
                config={
                    "memory_store_type": "kuzu",
                    "memory_file_path": temp_dir,
                    "vector_store_enabled": True,
                }
            )
        # Memory store should have fallen back
        assert adapter.memory_store._store._use_fallback is True
        assert isinstance(adapter.vector_store, KuzuAdapter)
        item = MemoryItem(id="t1", content="hi", memory_type=MemoryType.WORKING)
        adapter.memory_store.store(item)
        result = adapter.memory_store.retrieve("t1")
        assert result is not None
        assert result.content == "hi"
    finally:
        shutil.rmtree(temp_dir)
