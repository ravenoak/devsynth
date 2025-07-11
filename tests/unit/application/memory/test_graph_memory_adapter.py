"""
Unit tests for the GraphMemoryAdapter.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from rdflib import Graph, URIRef, Literal, Namespace
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.application.memory.context_manager import InMemoryStore
from devsynth.application.memory.adapters.vector_memory_adapter import VectorMemoryAdapter
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.query_router import QueryRouter
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.graph_memory_adapter import DEVSYNTH, MEMORY, RDF
from devsynth.exceptions import MemoryStoreError, MemoryItemNotFoundError


class TestGraphMemoryAdapter:
    """Tests for the GraphMemoryAdapter class.

ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def basic_adapter(self, temp_dir):
        """Create a basic GraphMemoryAdapter instance for testing."""
        return GraphMemoryAdapter(base_path=temp_dir)

    @pytest.fixture
    def rdflib_adapter(self, temp_dir):
        """Create a GraphMemoryAdapter with RDFLibStore integration for testing."""
        return GraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

    @pytest.fixture
    def sample_memory_item(self):
        """Create a sample memory item for testing."""
        return MemoryItem(id='test-id', content='Test content', memory_type
            =MemoryType.CODE, metadata={'source': 'test', 'language': 'python'}
            )

    def test_initialization_basic_succeeds(self, basic_adapter, temp_dir):
        """Test initialization of a basic GraphMemoryAdapter.

ReqID: N/A"""
        assert basic_adapter.base_path == temp_dir
        assert basic_adapter.use_rdflib_store is False
        assert basic_adapter.rdflib_store is None
        assert isinstance(basic_adapter.graph, Graph)
        namespaces = dict(basic_adapter.graph.namespaces())
        assert 'devsynth' in namespaces
        assert 'memory' in namespaces

    def test_initialization_rdflib_succeeds(self, rdflib_adapter, temp_dir):
        """Test initialization of a GraphMemoryAdapter with RDFLibStore integration.

ReqID: N/A"""
        assert rdflib_adapter.base_path == temp_dir
        assert rdflib_adapter.use_rdflib_store is True
        assert rdflib_adapter.rdflib_store is not None
        assert isinstance(rdflib_adapter.graph, Graph)

    def test_store_and_retrieve_basic_succeeds(self, basic_adapter,
        sample_memory_item):
        """Test storing and retrieving a memory item with basic adapter.

ReqID: N/A"""
        item_id = basic_adapter.store(sample_memory_item)
        assert item_id == sample_memory_item.id
        retrieved_item = basic_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == sample_memory_item.id
        assert retrieved_item.content == sample_memory_item.content
        assert retrieved_item.memory_type == sample_memory_item.memory_type
        assert retrieved_item.metadata['source'
            ] == sample_memory_item.metadata['source']
        assert retrieved_item.metadata['language'
            ] == sample_memory_item.metadata['language']

    def test_store_and_retrieve_rdflib_succeeds(self, rdflib_adapter,
        sample_memory_item):
        """Test storing and retrieving a memory item with RDFLibStore integration.

ReqID: N/A"""
        item_id = rdflib_adapter.store(sample_memory_item)
        assert item_id == sample_memory_item.id
        retrieved_item = rdflib_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == sample_memory_item.id
        assert retrieved_item.content == sample_memory_item.content
        assert retrieved_item.memory_type == sample_memory_item.memory_type
        assert retrieved_item.metadata['source'
            ] == sample_memory_item.metadata['source']
        assert retrieved_item.metadata['language'
            ] == sample_memory_item.metadata['language']

    def test_store_with_relationships_succeeds(self, basic_adapter):
        """Test storing items with relationships.

ReqID: N/A"""
        item1 = MemoryItem(id='item1', content='Item 1', memory_type=
            MemoryType.CODE, metadata={})
        item2 = MemoryItem(id='item2', content='Item 2', memory_type=
            MemoryType.CODE, metadata={'related_to': 'item1'})
        basic_adapter.store(item1)
        basic_adapter.store(item2)
        related_items = basic_adapter.query_related_items('item1')
        assert len(related_items) == 1
        assert related_items[0].id == 'item2'
        related_items = basic_adapter.query_related_items('item2')
        assert len(related_items) == 1
        assert related_items[0].id == 'item1'

    def test_search_succeeds(self, basic_adapter):
        """Test searching for memory items.

ReqID: N/A"""
        items = [MemoryItem(id=f'item{i}', content=f'Item {i}', memory_type
            =MemoryType.CODE, metadata={'language': 'python' if i % 2 == 0 else
            'javascript'}) for i in range(5)]
        for item in items:
            basic_adapter.store(item)
        results = basic_adapter.search({'type': MemoryType.CODE})
        assert len(results) == 5
        results = basic_adapter.search({'language': 'python'})
        assert len(results) == 3
        results = basic_adapter.search({'type': MemoryType.CODE, 'language':
            'javascript'})
        assert len(results) == 2

    def test_delete_succeeds(self, basic_adapter, sample_memory_item):
        """Test deleting a memory item.

ReqID: N/A"""
        item_id = basic_adapter.store(sample_memory_item)
        assert basic_adapter.retrieve(item_id) is not None
        result = basic_adapter.delete(item_id)
        assert result is True
        assert basic_adapter.retrieve(item_id) is None
        result = basic_adapter.delete('nonexistent-id')
        assert result is False

    def test_get_all_relationships_succeeds(self, basic_adapter):
        """Test getting all relationships.

ReqID: N/A"""
        items = [MemoryItem(id='item1', content='Item 1', memory_type=
            MemoryType.CODE, metadata={}), MemoryItem(id='item2', content=
            'Item 2', memory_type=MemoryType.CODE, metadata={'related_to':
            'item1'}), MemoryItem(id='item3', content='Item 3', memory_type
            =MemoryType.CODE, metadata={'related_to': 'item1'}), MemoryItem
            (id='item4', content='Item 4', memory_type=MemoryType.CODE,
            metadata={'related_to': 'item2'})]
        for item in items:
            basic_adapter.store(item)
        relationships = basic_adapter.get_all_relationships()
        assert 'item1' in relationships
        assert 'item2' in relationships
        assert 'item3' in relationships
        assert 'item4' in relationships
        assert 'item2' in relationships['item1']
        assert 'item3' in relationships['item1']
        assert 'item1' in relationships['item2']
        assert 'item4' in relationships['item2']
        assert 'item1' in relationships['item3']
        assert 'item2' in relationships['item4']

    def test_add_memory_volatility_succeeds(self, basic_adapter,
        sample_memory_item):
        """Test adding memory volatility controls.

ReqID: N/A"""
        basic_adapter.store(sample_memory_item)
        basic_adapter.add_memory_volatility(decay_rate=0.1, threshold=0.5)
        item_uri = URIRef(f'{MEMORY}{sample_memory_item.id}')
        confidence = basic_adapter.graph.value(item_uri, DEVSYNTH.confidence)
        decay_rate = basic_adapter.graph.value(item_uri, DEVSYNTH.decayRate)
        threshold = basic_adapter.graph.value(item_uri, DEVSYNTH.
            confidenceThreshold)
        assert float(confidence) == 1.0
        assert float(decay_rate) == 0.1
        assert float(threshold) == 0.5

    def test_apply_memory_decay_succeeds(self, basic_adapter,
        sample_memory_item):
        """Test applying memory decay.

ReqID: N/A"""
        basic_adapter.store(sample_memory_item)
        basic_adapter.add_memory_volatility(decay_rate=0.3, threshold=0.5)
        volatile_items = basic_adapter.apply_memory_decay()
        item_uri = URIRef(f'{MEMORY}{sample_memory_item.id}')
        confidence = float(basic_adapter.graph.value(item_uri, DEVSYNTH.
            confidence))
        assert confidence == 0.7
        assert len(volatile_items) == 0
        volatile_items = basic_adapter.apply_memory_decay()
        confidence = float(basic_adapter.graph.value(item_uri, DEVSYNTH.
            confidence))
        assert confidence == pytest.approx(0.4, abs=1e-06)
        assert len(volatile_items) == 1
        assert volatile_items[0] == sample_memory_item.id

    def test_advanced_memory_decay_succeeds(self, rdflib_adapter, monkeypatch):
        """Test advanced memory decay with RDFLibStore integration.

ReqID: N/A"""
        rdflib_adapter.use_rdflib_store = True
        rdflib_adapter.rdflib_store = MagicMock()
        original_query = rdflib_adapter.graph.query

        def mock_query(sparql_query):


            class MockQueryResult:

                def __iter__(self):
                    items = [(URIRef(f'{MEMORY}frequent'), 'frequent',
                        Literal(1.0), Literal(0.2), Literal(0.5), Literal(
                        '2023-01-01T00:00:00'), Literal(10)), (URIRef(
                        f'{MEMORY}rare'), 'rare', Literal(1.0), Literal(0.2
                        ), Literal(0.5), Literal('2023-01-01T00:00:00'),
                        Literal(1)), (URIRef(f'{MEMORY}related'), 'related',
                        Literal(1.0), Literal(0.2), Literal(0.5), Literal(
                        '2023-01-01T00:00:00'), Literal(5))]
                    for item in items:
                        yield item
            return MockQueryResult()
        monkeypatch.setattr(rdflib_adapter.graph, 'query', mock_query)
        original_update = rdflib_adapter.graph.update

        def mock_update(update_query):
            pass
        monkeypatch.setattr(rdflib_adapter.graph, 'update', mock_update)
        original_triples = rdflib_adapter.graph.triples

        def mock_triples(triple_pattern):
            s, p, o = triple_pattern
            if p == DEVSYNTH.relatedTo and s == URIRef(f'{MEMORY}related'):
                yield URIRef(f'{MEMORY}related'), DEVSYNTH.relatedTo, URIRef(
                    f'{MEMORY}related_to')
            elif p == DEVSYNTH.relatedTo and s == URIRef(f'{MEMORY}frequent'):
                return
            elif p == DEVSYNTH.relatedTo and s == URIRef(f'{MEMORY}rare'):
                return
            else:
                yield from original_triples(triple_pattern)
        monkeypatch.setattr(rdflib_adapter.graph, 'triples', mock_triples)
        original_value = rdflib_adapter.graph.value

        def mock_value(s, p, default=None):
            if p == DEVSYNTH.confidence:
                if s == URIRef(f'{MEMORY}frequent'):
                    return Literal(0.9)
                elif s == URIRef(f'{MEMORY}rare'):
                    return Literal(0.7)
                elif s == URIRef(f'{MEMORY}related'):
                    return Literal(0.8)
            return original_value(s, p, default)
        monkeypatch.setattr(rdflib_adapter.graph, 'value', mock_value)
        items = [MemoryItem(id='frequent', content='Frequently accessed',
            memory_type=MemoryType.CODE, metadata={}), MemoryItem(id='rare',
            content='Rarely accessed', memory_type=MemoryType.CODE,
            metadata={}), MemoryItem(id='related', content=
            'Has relationships', memory_type=MemoryType.CODE, metadata={}),
            MemoryItem(id='related_to', content='Related to another item',
            memory_type=MemoryType.CODE, metadata={'related_to': 'related'})]
        for item in items:
            rdflib_adapter.store(item)
        rdflib_adapter.add_memory_volatility(decay_rate=0.2, threshold=0.5,
            advanced_controls=True)
        for _ in range(10):
            rdflib_adapter.retrieve('frequent')
        rdflib_adapter.retrieve('rare')
        volatile_items = rdflib_adapter.apply_memory_decay(advanced_decay=True)
        frequent_uri = URIRef(f'{MEMORY}frequent')
        rare_uri = URIRef(f'{MEMORY}rare')
        related_uri = URIRef(f'{MEMORY}related')
        frequent_confidence = float(rdflib_adapter.graph.value(frequent_uri,
            DEVSYNTH.confidence))
        rare_confidence = float(rdflib_adapter.graph.value(rare_uri,
            DEVSYNTH.confidence))
        related_confidence = float(rdflib_adapter.graph.value(related_uri,
            DEVSYNTH.confidence))
        assert frequent_confidence > rare_confidence
        assert related_confidence > rare_confidence

    def test_integrate_with_store_succeeds(self, basic_adapter, temp_dir):
        """Test integrating with another memory store.

ReqID: N/A"""
        mock_store = MagicMock()
        mock_item1 = MemoryItem(id='mock1', content='Mock item 1',
            memory_type=MemoryType.CODE, metadata={})
        mock_item2 = MemoryItem(id='mock2', content='Mock item 2',
            memory_type=MemoryType.CODE, metadata={})
        mock_store.search.return_value = [mock_item1, mock_item2]
        mock_store.retrieve.return_value = None
        local_item = MemoryItem(id='local1', content='Local item 1',
            memory_type=MemoryType.CODE, metadata={})
        basic_adapter.store(local_item)
        basic_adapter.store(mock_item1)
        basic_adapter.store(mock_item2)
        basic_adapter.integrate_with_store(mock_store, sync_mode=
            'bidirectional')
        assert basic_adapter.retrieve('mock1') is not None
        assert basic_adapter.retrieve('mock2') is not None
        mock_store.store.assert_called()
        stored_item = mock_store.store.call_args_list[0][0][0]
        assert stored_item.id == 'local1'

    def test_integrate_with_vector_store_succeeds(self, rdflib_adapter,
        temp_dir):
        """Test integrating with a vector store.

ReqID: N/A"""
        mock_vector_store = MagicMock()
        mock_vector_store.get_collection_stats.return_value = {'num_vectors': 5
            }
        rdflib_adapter.integrate_with_store(mock_vector_store, sync_mode=
            'import')
        mock_vector_store.get_collection_stats.assert_called()

    def test_save_graph_with_rdflib_store_succeeds(self, rdflib_adapter,
        temp_dir):
        """Ensure _save_graph persists RDF graphs when using RDFLibStore.

ReqID: N/A"""
        memory_item = MemoryItem(id='save_test', content='Save Graph',
            memory_type=MemoryType.CODE, metadata={'source': 'unit'})
        rdflib_adapter.store(memory_item)
        rdflib_adapter._save_graph()
        graph_file = os.path.join(temp_dir, 'graph_memory.ttl')
        assert os.path.exists(graph_file)

    def test_memory_item_triple_creation_succeeds(self, rdflib_adapter):
        """Verify that storing an item creates the expected RDF triples.

ReqID: N/A"""
        item = MemoryItem(id='triple_test', content='Triple', memory_type=
            MemoryType.CODE, metadata={'source': 'unit'})
        rdflib_adapter.store(item)
        item_uri = URIRef(f'{MEMORY}{item.id}')
        assert (item_uri, RDF.type, DEVSYNTH.MemoryItem
            ) in rdflib_adapter.graph
        assert (item_uri, DEVSYNTH.source, Literal('unit')
            ) in rdflib_adapter.graph

    @pytest.fixture
    def router(self):
        """Create a QueryRouter with simple in-memory adapters."""
        adapters = {'tinydb': InMemoryStore(), 'document': InMemoryStore(),
            'vector': VectorMemoryAdapter()}
        manager = MemoryManager(adapters=adapters)
        return QueryRouter(manager)

    @pytest.fixture
    def populated_router(self, router):
        """Populate the router's stores with simple items."""
        manager = router.memory_manager
        manager.adapters['tinydb'].store(MemoryItem(id='tiny', content=
            'apple tinydb', memory_type=MemoryType.CODE))
        manager.adapters['document'].store(MemoryItem(id='doc', content=
            'apple document', memory_type=MemoryType.CODE))
        vec = MemoryVector(id='vec', content='apple vector', embedding=
            manager._embed_text('apple'), metadata={'memory_type':
            MemoryType.CODE.value})
        manager.adapters['vector'].store_vector(vec)
        return router

    def test_cascading_query_with_missing_adapter_succeeds(self,
        populated_router):
        """Ensure cascading_query aggregates results and skips missing stores.

ReqID: N/A"""
        results = populated_router.cascading_query('apple', order=['vector',
            'tinydb', 'missing', 'document'])
        assert [r.content for r in results] == ['apple vector',
            'apple tinydb', 'apple document']

    def test_context_aware_query_succeeds(self, populated_router):
        """Context-aware query should incorporate context into search.

ReqID: N/A"""
        manager = populated_router.memory_manager
        manager.adapters['tinydb'].store(MemoryItem(id='ctx', content=
            'apple location:home', memory_type=MemoryType.CODE))
        manager.adapters['document'].store(MemoryItem(id='ctx2', content=
            'apple location:home', memory_type=MemoryType.CODE))
        results = populated_router.context_aware_query('apple', {'location':
            'home'})
        assert len(results['tinydb']) == 1
        assert results['tinydb'][0].content == 'apple location:home'
        assert len(results['document']) == 1
        assert populated_router.context_aware_query('apple', {'location':
            'home'}, store='missing') == []

    def test_query_router_route_succeeds(self, populated_router):
        """Exercise the router.route method for various strategies.

ReqID: N/A"""
        direct = populated_router.route('apple', store='tinydb', strategy=
            'direct')
        assert len(direct) == 1
        cascade = populated_router.route('apple', strategy='cascading')
        assert len(cascade) >= 3
        assert populated_router.route('apple', strategy='unknown') == []

    def test_store_and_retrieve_with_edrr_phase_has_expected(self,
        basic_adapter):
        """Test storing and retrieving items with EDRR phase.

ReqID: N/A"""
        item1 = MemoryItem(id='', content={'key': 'value1'}, memory_type=
            MemoryType.CODE, metadata={'edrr_phase': 'EXPAND', 'source':
            'test1'})
        item2 = MemoryItem(id='', content={'key': 'value2'}, memory_type=
            MemoryType.CODE, metadata={'edrr_phase': 'DIFFERENTIATE',
            'source': 'test2'})
        item1_id = basic_adapter.store(item1)
        item2_id = basic_adapter.store(item2)
        print(f'\nStored item1 with ID: {item1_id}')
        print(f'Stored item2 with ID: {item2_id}')
        retrieved_item1 = basic_adapter.retrieve(item1_id)
        retrieved_item2 = basic_adapter.retrieve(item2_id)
        print(
            f'Retrieved item1: {retrieved_item1.id}, Type: {retrieved_item1.memory_type}, Metadata: {retrieved_item1.metadata}, Content: {retrieved_item1.content}'
            )
        print(
            f'Retrieved item2: {retrieved_item2.id}, Type: {retrieved_item2.memory_type}, Metadata: {retrieved_item2.metadata}, Content: {retrieved_item2.content}'
            )
        all_items = []
        for s, p, o in basic_adapter.graph.triples((None, RDF.type,
            DEVSYNTH.MemoryItem)):
            item = basic_adapter._triples_to_memory_item(s)
            if item:
                all_items.append(item)
                print(
                    f'Item in store: {item.id}, Type: {item.memory_type}, Metadata: {item.metadata}, Content: {item.content}'
                    )
        matching_items1 = []
        for item in all_items:
            if (hasattr(item.memory_type, 'value') and item.memory_type.
                value == 'CODE' or str(item.memory_type) == 'CODE'
                ) and item.metadata.get('edrr_phase'
                ) == 'EXPAND' and item.metadata.get('source') == 'test1':
                matching_items1.append(item)
                print(
                    f'Manually found matching item1: {item.id}, Type: {item.memory_type}, Metadata: {item.metadata}, Content: {item.content}'
                    )
        matching_items2 = []
        for item in all_items:
            if (hasattr(item.memory_type, 'value') and item.memory_type.
                value == 'CODE' or str(item.memory_type) == 'CODE'
                ) and item.metadata.get('edrr_phase'
                ) == 'DIFFERENTIATE' and item.metadata.get('source'
                ) == 'test2':
                matching_items2.append(item)
                print(
                    f'Manually found matching item2: {item.id}, Type: {item.memory_type}, Metadata: {item.metadata}, Content: {item.content}'
                    )
        result1 = basic_adapter.retrieve_with_edrr_phase(item_type='CODE',
            edrr_phase='EXPAND', metadata={'source': 'test1'})
        result2 = basic_adapter.retrieve_with_edrr_phase(item_type='CODE',
            edrr_phase='DIFFERENTIATE', metadata={'source': 'test2'})
        print(f'Result1 from retrieve_with_edrr_phase: {result1}')
        print(f'Result2 from retrieve_with_edrr_phase: {result2}')
        print(
            f"Expected result1: {{'key': 'value1'}}, Actual result1: {result1}"
            )
        print(
            f"Expected result2: {{'key': 'value2'}}, Actual result2: {result2}"
            )
        if result1 == {'key': 'value1'}:
            print('result1 matches expected value')
        else:
            print('result1 does NOT match expected value')
        if result2 == {'key': 'value2'}:
            print('result2 matches expected value')
        else:
            print('result2 does NOT match expected value')
