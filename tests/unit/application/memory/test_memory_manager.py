import importlib.util
import pathlib
import types
from unittest.mock import MagicMock, patch
import pytest
SRC_ROOT = pathlib.Path(__file__).resolve().parents[4] / 'src'


def _load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


package_path = SRC_ROOT / 'devsynth/application/memory'
dummy_pkg = types.ModuleType('devsynth.application.memory')
dummy_pkg.__path__ = [str(package_path)]
import sys
sys.modules.setdefault('devsynth.application.memory', dummy_pkg)
memory_manager_module = _load_module(package_path / 'memory_manager.py',
    'devsynth.application.memory.memory_manager')
MemoryManager = memory_manager_module.MemoryManager
from devsynth.domain.models.memory import MemoryType, MemoryItem


class DummyVectorStore:

    def __init__(self):
        self.stored = []

    def store(self, item):
        self.stored.append(item)
        return 'vector-id'


class DummyGraphStore:

    def __init__(self):
        self.stored = []
        self.edrr_items = {}

    def store(self, item):
        self.stored.append(item)
        return 'graph-id'

    def retrieve_with_edrr_phase(self, item_type, edrr_phase, metadata=None):
        key = f'{item_type}_{edrr_phase}'
        return self.edrr_items.get(key)

    def store_with_edrr_phase(self, content, memory_type, edrr_phase,
        metadata=None):
        key = f'{memory_type}_{edrr_phase}'
        self.edrr_items[key] = content
        return 'graph-edrr-id'


class TestMemoryManagerStore:
    """Tests for the MemoryManagerStore component.

ReqID: N/A"""

    @pytest.fixture
    def adapters(self):
        tinydb = MagicMock()
        vector = DummyVectorStore()
        return {'tinydb': tinydb, 'vector': vector}

    @pytest.fixture
    def graph_adapters(self):
        graph = DummyGraphStore()
        tinydb = MagicMock()
        return {'graph': graph, 'tinydb': tinydb}

    def test_store_prefers_graph_for_edrr_succeeds(self, graph_adapters):
        """Test that store prefers graph for edrr succeeds.

ReqID: N/A"""
        manager = MemoryManager(adapters=graph_adapters)
        manager.store_with_edrr_phase('x', MemoryType.CODE, 'EXPAND')
        assert len(graph_adapters['graph'].stored) == 1
        graph_adapters['tinydb'].store.assert_not_called()

    def test_store_falls_back_to_tinydb_succeeds(self):
        """Test that store falls back to tinydb succeeds.

ReqID: N/A"""
        tinydb = MagicMock()
        manager = MemoryManager(adapters={'tinydb': tinydb})
        manager.store_with_edrr_phase('x', MemoryType.CODE, 'EXPAND')
        tinydb.store.assert_called_once()

    def test_store_falls_back_to_first_succeeds(self):
        """Test that store falls back to first succeeds.

ReqID: N/A"""
        vector = DummyVectorStore()
        manager = MemoryManager(adapters={'vector': vector})
        manager.store_with_edrr_phase('x', MemoryType.CODE, 'EXPAND')
        assert vector.stored


class TestMemoryManagerRetrieve:
    """Tests for the MemoryManagerRetrieve component.

ReqID: N/A"""

    @pytest.fixture
    def graph_adapter(self):
        return DummyGraphStore()

    @pytest.fixture
    def manager_with_graph(self, graph_adapter):
        return MemoryManager(adapters={'graph': graph_adapter})

    def test_retrieve_with_edrr_phase_succeeds(self, manager_with_graph,
        graph_adapter):
        """Test that retrieve with edrr phase succeeds.

ReqID: N/A"""
        test_content = {'key': 'value'}
        graph_adapter.edrr_items['CODE_EXPAND'] = test_content
        result = manager_with_graph.retrieve_with_edrr_phase('CODE', 'EXPAND')
        assert result == test_content

    def test_retrieve_with_edrr_phase_not_found_succeeds(self,
        manager_with_graph):
        """Test that retrieve with edrr phase not found succeeds.

ReqID: N/A"""
        result = manager_with_graph.retrieve_with_edrr_phase('CODE',
            'NONEXISTENT')
        assert result == {}

    def test_retrieve_with_edrr_phase_with_metadata_succeeds(self,
        manager_with_graph, graph_adapter):
        """Test that retrieve with edrr phase with metadata succeeds.

ReqID: N/A"""
        test_content = {'key': 'value'}
        graph_adapter.edrr_items['CODE_EXPAND'] = test_content
        result = manager_with_graph.retrieve_with_edrr_phase('CODE',
            'EXPAND', {'cycle_id': '123'})
        assert result == test_content


class TestEmbedText:
    """Tests for the EmbedText component.

ReqID: N/A"""

    def test_fallback_and_provider_succeeds(self):
        """Test that fallback and provider succeeds.

ReqID: N/A"""
        manager = MemoryManager()
        default = manager._embed_text('abc', dimension=5)
        provider = MagicMock()
        provider.embed.side_effect = Exception('boom')
        manager_fail = MemoryManager(embedding_provider=provider)
        assert manager_fail._embed_text('abc', dimension=5) == default
        provider.embed.side_effect = None
        provider.embed.return_value = [1.0, 2.0]
        manager_ok = MemoryManager(embedding_provider=provider)
        assert manager_ok._embed_text('hi') == [1.0, 2.0]
