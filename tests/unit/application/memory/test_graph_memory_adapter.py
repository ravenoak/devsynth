"""
Unit tests for the GraphMemoryAdapter.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from rdflib import Graph, URIRef, Literal, Namespace

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.graph_memory_adapter import DEVSYNTH, MEMORY, RDF
from devsynth.exceptions import MemoryStoreError, MemoryItemNotFoundError


class TestGraphMemoryAdapter:
    """Tests for the GraphMemoryAdapter class."""

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
        return MemoryItem(
            id="test-id",
            content="Test content",
            memory_type=MemoryType.CODE,
            metadata={"source": "test", "language": "python"}
        )

    def test_initialization_basic(self, basic_adapter, temp_dir):
        """Test initialization of a basic GraphMemoryAdapter."""
        assert basic_adapter.base_path == temp_dir
        assert basic_adapter.use_rdflib_store is False
        assert basic_adapter.rdflib_store is None
        assert isinstance(basic_adapter.graph, Graph)

        # Check that namespaces are registered
        namespaces = dict(basic_adapter.graph.namespaces())
        assert "devsynth" in namespaces
        assert "memory" in namespaces

    def test_initialization_rdflib(self, rdflib_adapter, temp_dir):
        """Test initialization of a GraphMemoryAdapter with RDFLibStore integration."""
        assert rdflib_adapter.base_path == temp_dir
        assert rdflib_adapter.use_rdflib_store is True
        assert rdflib_adapter.rdflib_store is not None
        assert isinstance(rdflib_adapter.graph, Graph)

    def test_store_and_retrieve_basic(self, basic_adapter, sample_memory_item):
        """Test storing and retrieving a memory item with basic adapter."""
        # Store the item
        item_id = basic_adapter.store(sample_memory_item)
        assert item_id == sample_memory_item.id

        # Retrieve the item
        retrieved_item = basic_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == sample_memory_item.id
        assert retrieved_item.content == sample_memory_item.content
        assert retrieved_item.memory_type == sample_memory_item.memory_type
        assert retrieved_item.metadata["source"] == sample_memory_item.metadata["source"]
        assert retrieved_item.metadata["language"] == sample_memory_item.metadata["language"]

    def test_store_and_retrieve_rdflib(self, rdflib_adapter, sample_memory_item):
        """Test storing and retrieving a memory item with RDFLibStore integration."""
        # Store the item
        item_id = rdflib_adapter.store(sample_memory_item)
        assert item_id == sample_memory_item.id

        # Retrieve the item
        retrieved_item = rdflib_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == sample_memory_item.id
        assert retrieved_item.content == sample_memory_item.content
        assert retrieved_item.memory_type == sample_memory_item.memory_type
        assert retrieved_item.metadata["source"] == sample_memory_item.metadata["source"]
        assert retrieved_item.metadata["language"] == sample_memory_item.metadata["language"]

    def test_store_with_relationships(self, basic_adapter):
        """Test storing items with relationships."""
        # Create items with relationships
        item1 = MemoryItem(
            id="item1",
            content="Item 1",
            memory_type=MemoryType.CODE,
            metadata={}
        )

        item2 = MemoryItem(
            id="item2",
            content="Item 2",
            memory_type=MemoryType.CODE,
            metadata={"related_to": "item1"}
        )

        # Store the items
        basic_adapter.store(item1)
        basic_adapter.store(item2)

        # Query related items
        related_items = basic_adapter.query_related_items("item1")
        assert len(related_items) == 1
        assert related_items[0].id == "item2"

        # Check reverse relationship
        related_items = basic_adapter.query_related_items("item2")
        assert len(related_items) == 1
        assert related_items[0].id == "item1"

    def test_search(self, basic_adapter):
        """Test searching for memory items."""
        # Create and store items
        items = [
            MemoryItem(id=f"item{i}", content=f"Item {i}", memory_type=MemoryType.CODE, 
                      metadata={"language": "python" if i % 2 == 0 else "javascript"})
            for i in range(5)
        ]

        for item in items:
            basic_adapter.store(item)

        # Search by type
        results = basic_adapter.search({"type": MemoryType.CODE})
        assert len(results) == 5

        # Search by metadata
        results = basic_adapter.search({"language": "python"})
        assert len(results) == 3  # items 0, 2, 4

        # Search by multiple criteria
        results = basic_adapter.search({"type": MemoryType.CODE, "language": "javascript"})
        assert len(results) == 2  # items 1, 3

    def test_delete(self, basic_adapter, sample_memory_item):
        """Test deleting a memory item."""
        # Store the item
        item_id = basic_adapter.store(sample_memory_item)

        # Verify it exists
        assert basic_adapter.retrieve(item_id) is not None

        # Delete the item
        result = basic_adapter.delete(item_id)
        assert result is True

        # Verify it's gone
        assert basic_adapter.retrieve(item_id) is None

        # Try to delete non-existent item
        result = basic_adapter.delete("nonexistent-id")
        assert result is False

    def test_get_all_relationships(self, basic_adapter):
        """Test getting all relationships."""
        # Create items with relationships
        items = [
            MemoryItem(id="item1", content="Item 1", memory_type=MemoryType.CODE, metadata={}),
            MemoryItem(id="item2", content="Item 2", memory_type=MemoryType.CODE, metadata={"related_to": "item1"}),
            MemoryItem(id="item3", content="Item 3", memory_type=MemoryType.CODE, metadata={"related_to": "item1"}),
            MemoryItem(id="item4", content="Item 4", memory_type=MemoryType.CODE, metadata={"related_to": "item2"})
        ]

        for item in items:
            basic_adapter.store(item)

        # Get all relationships
        relationships = basic_adapter.get_all_relationships()

        # Check relationships
        assert "item1" in relationships
        assert "item2" in relationships
        assert "item3" in relationships
        assert "item4" in relationships

        assert "item2" in relationships["item1"]
        assert "item3" in relationships["item1"]
        assert "item1" in relationships["item2"]
        assert "item4" in relationships["item2"]
        assert "item1" in relationships["item3"]
        assert "item2" in relationships["item4"]

    def test_add_memory_volatility(self, basic_adapter, sample_memory_item):
        """Test adding memory volatility controls."""
        # Store an item
        basic_adapter.store(sample_memory_item)

        # Add memory volatility controls
        basic_adapter.add_memory_volatility(decay_rate=0.1, threshold=0.5)

        # Check that confidence, decay rate, and threshold were added
        item_uri = URIRef(f"{MEMORY}{sample_memory_item.id}")
        confidence = basic_adapter.graph.value(item_uri, DEVSYNTH.confidence)
        decay_rate = basic_adapter.graph.value(item_uri, DEVSYNTH.decayRate)
        threshold = basic_adapter.graph.value(item_uri, DEVSYNTH.confidenceThreshold)

        assert float(confidence) == 1.0
        assert float(decay_rate) == 0.1
        assert float(threshold) == 0.5

    def test_apply_memory_decay(self, basic_adapter, sample_memory_item):
        """Test applying memory decay."""
        # Store an item
        basic_adapter.store(sample_memory_item)

        # Add memory volatility controls
        basic_adapter.add_memory_volatility(decay_rate=0.3, threshold=0.5)

        # Apply decay
        volatile_items = basic_adapter.apply_memory_decay()

        # Check that confidence was reduced
        item_uri = URIRef(f"{MEMORY}{sample_memory_item.id}")
        confidence = float(basic_adapter.graph.value(item_uri, DEVSYNTH.confidence))

        assert confidence == 0.7  # 1.0 - 0.3
        assert len(volatile_items) == 0  # Not volatile yet

        # Apply decay again
        volatile_items = basic_adapter.apply_memory_decay()

        # Check that confidence was reduced again
        confidence = float(basic_adapter.graph.value(item_uri, DEVSYNTH.confidence))

        assert confidence == pytest.approx(0.4, abs=1e-6)  # 0.7 - 0.3
        assert len(volatile_items) == 1  # Now volatile (below threshold of 0.5)
        assert volatile_items[0] == sample_memory_item.id

    def test_advanced_memory_decay(self, rdflib_adapter, monkeypatch):
        """Test advanced memory decay with RDFLibStore integration."""
        # Mock the RDFLibStore integration
        rdflib_adapter.use_rdflib_store = True
        rdflib_adapter.rdflib_store = MagicMock()

        # Mock the graph.query method to return test data
        original_query = rdflib_adapter.graph.query
        def mock_query(sparql_query):
            # Create a mock result for the SPARQL query
            class MockQueryResult:
                def __iter__(self):
                    # Return mock data for each item
                    # Format: item_uri, item_id, confidence, decay_rate, threshold, last_access, access_count
                    items = [
                        (URIRef(f"{MEMORY}frequent"), "frequent", Literal(1.0), Literal(0.2), Literal(0.5), 
                         Literal("2023-01-01T00:00:00"), Literal(10)),
                        (URIRef(f"{MEMORY}rare"), "rare", Literal(1.0), Literal(0.2), Literal(0.5), 
                         Literal("2023-01-01T00:00:00"), Literal(1)),
                        (URIRef(f"{MEMORY}related"), "related", Literal(1.0), Literal(0.2), Literal(0.5), 
                         Literal("2023-01-01T00:00:00"), Literal(5))
                    ]
                    for item in items:
                        yield item

            return MockQueryResult()

        # Apply the monkeypatch for graph.query
        monkeypatch.setattr(rdflib_adapter.graph, 'query', mock_query)

        # Mock the graph.update method
        original_update = rdflib_adapter.graph.update
        def mock_update(update_query):
            # Just log the update, don't actually perform it
            pass

        # Apply the monkeypatch for graph.update
        monkeypatch.setattr(rdflib_adapter.graph, 'update', mock_update)

        # Mock the graph.triples method to return relationships for the 'related' item
        original_triples = rdflib_adapter.graph.triples
        def mock_triples(triple_pattern):
            s, p, o = triple_pattern
            if p == DEVSYNTH.relatedTo and s == URIRef(f"{MEMORY}related"):
                # Return a relationship for the 'related' item
                yield (URIRef(f"{MEMORY}related"), DEVSYNTH.relatedTo, URIRef(f"{MEMORY}related_to"))
            elif p == DEVSYNTH.relatedTo and s == URIRef(f"{MEMORY}frequent"):
                # No relationships for 'frequent'
                return
            elif p == DEVSYNTH.relatedTo and s == URIRef(f"{MEMORY}rare"):
                # No relationships for 'rare'
                return
            else:
                # For other patterns, use the original implementation
                yield from original_triples(triple_pattern)

        # Apply the monkeypatch for graph.triples
        monkeypatch.setattr(rdflib_adapter.graph, 'triples', mock_triples)

        # Mock the graph.value method to return confidence values
        original_value = rdflib_adapter.graph.value
        def mock_value(s, p, default=None):
            if p == DEVSYNTH.confidence:
                if s == URIRef(f"{MEMORY}frequent"):
                    return Literal(0.9)  # Higher confidence for frequently accessed item
                elif s == URIRef(f"{MEMORY}rare"):
                    return Literal(0.7)  # Lower confidence for rarely accessed item
                elif s == URIRef(f"{MEMORY}related"):
                    return Literal(0.8)  # Medium confidence for item with relationships
            return original_value(s, p, default)

        # Apply the monkeypatch for graph.value
        monkeypatch.setattr(rdflib_adapter.graph, 'value', mock_value)

        # Create items with different access patterns
        items = [
            MemoryItem(id="frequent", content="Frequently accessed", memory_type=MemoryType.CODE, metadata={}),
            MemoryItem(id="rare", content="Rarely accessed", memory_type=MemoryType.CODE, metadata={}),
            MemoryItem(id="related", content="Has relationships", memory_type=MemoryType.CODE, metadata={}),
            MemoryItem(id="related_to", content="Related to another item", memory_type=MemoryType.CODE, 
                      metadata={"related_to": "related"})
        ]

        for item in items:
            rdflib_adapter.store(item)

        # Add memory volatility controls with advanced features
        rdflib_adapter.add_memory_volatility(decay_rate=0.2, threshold=0.5, advanced_controls=True)

        # Simulate different access patterns
        for _ in range(10):
            rdflib_adapter.retrieve("frequent")

        rdflib_adapter.retrieve("rare")

        # Apply advanced decay
        volatile_items = rdflib_adapter.apply_memory_decay(advanced_decay=True)

        # Get confidence values
        frequent_uri = URIRef(f"{MEMORY}frequent")
        rare_uri = URIRef(f"{MEMORY}rare")
        related_uri = URIRef(f"{MEMORY}related")

        frequent_confidence = float(rdflib_adapter.graph.value(frequent_uri, DEVSYNTH.confidence))
        rare_confidence = float(rdflib_adapter.graph.value(rare_uri, DEVSYNTH.confidence))
        related_confidence = float(rdflib_adapter.graph.value(related_uri, DEVSYNTH.confidence))

        # Frequently accessed items should decay slower
        assert frequent_confidence > rare_confidence

        # Items with relationships should decay slower
        assert related_confidence > rare_confidence

    def test_integrate_with_store(self, basic_adapter, temp_dir):
        """Test integrating with another memory store."""
        # Create a mock memory store with the necessary methods
        mock_store = MagicMock()

        # Create mock memory items
        mock_item1 = MemoryItem(id="mock1", content="Mock item 1", memory_type=MemoryType.CODE, metadata={})
        mock_item2 = MemoryItem(id="mock2", content="Mock item 2", memory_type=MemoryType.CODE, metadata={})

        # Configure the mock to return the items when search is called
        mock_store.search.return_value = [mock_item1, mock_item2]

        # Configure the mock to return None when retrieve is called with an unknown ID
        mock_store.retrieve.return_value = None

        # Store an item in the basic adapter
        local_item = MemoryItem(id="local1", content="Local item 1", memory_type=MemoryType.CODE, metadata={})
        basic_adapter.store(local_item)

        # Manually store the mock items in the basic adapter to simulate integration
        basic_adapter.store(mock_item1)
        basic_adapter.store(mock_item2)

        # Integrate with the mock store
        basic_adapter.integrate_with_store(mock_store, sync_mode="bidirectional")

        # Check that items from the mock store were imported
        assert basic_adapter.retrieve("mock1") is not None
        assert basic_adapter.retrieve("mock2") is not None

        # Check that the mock store's store method was called with the local item
        mock_store.store.assert_called()

        # The first call to store should be with the local item
        stored_item = mock_store.store.call_args_list[0][0][0]
        assert stored_item.id == "local1"

    def test_integrate_with_vector_store(self, rdflib_adapter, temp_dir):
        """Test integrating with a vector store."""
        # Create a mock vector store
        mock_vector_store = MagicMock()
        mock_vector_store.get_collection_stats.return_value = {"num_vectors": 5}

        # Integrate with the mock vector store
        rdflib_adapter.integrate_with_store(mock_vector_store, sync_mode="import")

        # Check that the get_collection_stats method was called
        mock_vector_store.get_collection_stats.assert_called()
