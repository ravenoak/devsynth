"""Tests for :class:`KuzuMemoryStore`."""
import tempfile
import shutil
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

from devsynth.domain.models.memory import MemoryItem, MemoryType

root = Path(__file__).resolve().parents[3]
spec_store = importlib.util.spec_from_file_location(
    "kuzu_store", root / "src/devsynth/application/memory/kuzu_store.py"
)
kuzu_store_mod = importlib.util.module_from_spec(spec_store)
spec_store.loader.exec_module(kuzu_store_mod)
fake_pkg = ModuleType("devsynth.application.memory")
fake_pkg.kuzu_store = kuzu_store_mod
fake_pkg.__path__ = []
sys.modules["devsynth.application.memory"] = fake_pkg
sys.modules["devsynth.application.memory.kuzu_store"] = kuzu_store_mod

spec_adapter = importlib.util.spec_from_file_location(
    "kuzu_memory_store", root / "src/devsynth/adapters/kuzu_memory_store.py"
)
kuzu_memory_store = importlib.util.module_from_spec(spec_adapter)
spec_adapter.loader.exec_module(kuzu_memory_store)
KuzuMemoryStore = kuzu_memory_store.KuzuMemoryStore


def test_store_and_search():
    temp_dir = tempfile.mkdtemp()
    store = KuzuMemoryStore(persist_directory=temp_dir, use_provider_system=True)
    with patch.object(store, "_get_embedding", return_value=[0.1, 0.2, 0.3]):
        item = MemoryItem(id="t1", content="hello world", memory_type=MemoryType.WORKING)
        store.store(item)
        results = store.search({"query": "hello", "top_k": 1})
    shutil.rmtree(temp_dir)
    assert len(results) == 1
    assert results[0].id == "t1"
