import importlib.util
import pathlib
import sys
import types
import pytest

SRC_ROOT = pathlib.Path(__file__).resolve().parents[3] / "src"


def _load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Provide a minimal package so heavy optional dependencies are not imported
package_path = SRC_ROOT / "devsynth/application/memory"
dummy_pkg = types.ModuleType("devsynth.application.memory")
dummy_pkg.__path__ = [str(package_path)]
sys.modules.setdefault("devsynth.application.memory", dummy_pkg)

memory_manager_module = _load_module(
    package_path / "memory_manager.py", "devsynth.application.memory.memory_manager"
)
vector_adapter_module = _load_module(
    package_path / "adapters/vector_memory_adapter.py",
    "devsynth.application.memory.adapters.vector_memory_adapter",
)
context_module = _load_module(
    package_path / "context_manager.py", "devsynth.application.memory.context_manager"
)

MemoryManager = memory_manager_module.MemoryManager
VectorMemoryAdapter = vector_adapter_module.VectorMemoryAdapter
InMemoryStore = context_module.InMemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


class TestSyncManagerCrossStoreQuery:
    @pytest.fixture
    def manager(self):
        adapters = {
            "vector": VectorMemoryAdapter(),
            "tinydb": InMemoryStore(),
        }
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

    def test_cross_store_query_returns_results(self, manager):
        self._add_items(manager)
        results = manager.sync_manager.cross_store_query("apple")
        assert "vector" in results and "tinydb" in results
        assert len(results["vector"]) == 1
        assert len(results["tinydb"]) == 1

    def test_query_results_cached(self, manager):
        self._add_items(manager)
        manager.sync_manager.cross_store_query("apple")
        # Add additional matching item after first query
        new_item = MemoryItem(
            id="", content="apple second", memory_type=MemoryType.CODE, metadata={}
        )
        manager.adapters["tinydb"].store(new_item)
        cached = manager.sync_manager.cross_store_query("apple")
        # Should still return single result from cache
        assert len(cached["tinydb"]) == 1
        assert manager.sync_manager.get_cache_size() == 1
        manager.sync_manager.clear_cache()
        refreshed = manager.sync_manager.cross_store_query("apple")
        assert len(refreshed["tinydb"]) == 2
