import importlib
import sys
import types
import tempfile
import shutil
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType
from unittest.mock import patch


def test_memory_system_falls_back_when_kuzu_unavailable(monkeypatch):
    # Simulate kuzu not installed
    monkeypatch.setitem(sys.modules, "kuzu", None)
    import importlib
    import devsynth.application.memory.kuzu_store as kuzu_store
    importlib.reload(kuzu_store)
    import devsynth.adapters.kuzu_memory_store as km_store
    importlib.reload(km_store)
    monkeypatch.setattr(km_store, "embedding_functions", None)

    temp_dir = tempfile.mkdtemp()
    try:
        with patch("devsynth.adapters.kuzu_memory_store.embed", return_value=[0.1, 0.2, 0.3]):
            adapter = MemorySystemAdapter(
                config={
                    "memory_store_type": "kuzu",
                    "memory_file_path": temp_dir,
                    "vector_store_enabled": True,
                }
            )
        # Memory store should have fallen back
        assert adapter.memory_store._store._use_fallback is True
        item = MemoryItem(id="t1", content="hi", memory_type=MemoryType.WORKING)
        adapter.memory_store.store(item)
        result = adapter.memory_store.retrieve("t1")
        assert result is not None
        assert result.content == "hi"
    finally:
        shutil.rmtree(temp_dir)

