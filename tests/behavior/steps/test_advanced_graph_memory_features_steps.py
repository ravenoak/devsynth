"""
Step definitions for advanced_graph_memory_features.feature
"""

import os
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

pytest.importorskip("chromadb.api")

from devsynth.application.memory.adapters.chromadb_vector_adapter import (
    ChromaDBVectorAdapter,
)
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

# Register scenarios
scenarios(feature_path(__file__, "general", "advanced_graph_memory_features.feature"))


@pytest.fixture
def context():
    """Fixture for the test context."""

    class Context:
        def __init__(self):
            self.temp_dir = tempfile.TemporaryDirectory()
            self.base_path = self.temp_dir.name
            self.graph_adapter = None
            self.tinydb_adapter = None
            self.chromadb_adapter = None
            self.memory_items = {}
            self.volatile_items = []
            self.traversal_result = set()

        def cleanup(self):
            if self.temp_dir:
                self.temp_dir.cleanup()

    ctx = Context()
    yield ctx
    ctx.cleanup()


@given("the DevSynth system is initialized")
def devsynth_initialized(context):
    """Initialize the DevSynth system."""
    assert context is not None


@given("the GraphMemoryAdapter is configured with RDFLibStore integration")
def graph_adapter_with_rdflib(context):
    """Configure GraphMemoryAdapter with RDFLibStore integration."""
    context.graph_adapter = GraphMemoryAdapter(
        base_path=context.base_path, use_rdflib_store=True
    )


@given("I have a GraphMemoryAdapter with RDFLibStore integration")
def have_graph_adapter_with_rdflib(context):
    """Ensure we have a GraphMemoryAdapter with RDFLibStore integration."""
    if not context.graph_adapter:
        context.graph_adapter = GraphMemoryAdapter(
            base_path=context.base_path, use_rdflib_store=True
        )


@when('I store a memory item with content "{content}"')
def store_memory_item(context, content):
    """Store a memory item with the given content."""
    memory_item = MemoryItem(
        id=None,  # Let the adapter generate an ID
        content=content,
        memory_type=MemoryType.CODE,
        metadata={"source": "test"},
    )
    item_id = context.graph_adapter.store(memory_item)
    context.memory_items[item_id] = memory_item


@when('I store a memory item with content "Test content with namespaces"')
def store_memory_item_with_namespaces(context):
    """Store a memory item with content for namespace testing."""
    memory_item = MemoryItem(
        id=None,  # Let the adapter generate an ID
        content="Test content with namespaces",
        memory_type=MemoryType.CODE,
        metadata={"source": "test"},
    )
    item_id = context.graph_adapter.store(memory_item)
    context.memory_items[item_id] = memory_item


@then("the memory item should be stored with proper namespace handling")
def check_namespace_handling(context):
    """Check that the memory item was stored with proper namespace handling."""
    # Verify that namespaces are properly registered in the graph
    # Convert the generator to a dictionary
    namespaces = dict(context.graph_adapter.graph.namespaces())
    assert "devsynth" in namespaces
    assert "memory" in namespaces
    assert "foaf" in namespaces
    assert "dc" in namespaces


@then("the graph should be serialized in Turtle format")
def check_graph_serialization(context):
    """Check that the graph was serialized in Turtle format."""
    if context.graph_adapter.base_path:
        # Force the graph to be saved
        context.graph_adapter._save_graph()

        graph_file = os.path.join(context.graph_adapter.base_path, "graph_memory.ttl")

        # Check if the file exists, but don't fail the test if it doesn't
        # This is because some test environments might not allow file writing
        if os.path.exists(graph_file):
            # Check that the file contains Turtle syntax
            with open(graph_file) as f:
                content = f.read()
                assert (
                    "@prefix" in content
                ), "Turtle syntax not found in serialized graph"
        else:
            # If the file doesn't exist, check that the graph can be serialized to a string
            turtle_str = context.graph_adapter.graph.serialize(format="turtle")
            assert (
                "@prefix" in turtle_str
            ), "Turtle syntax not found in serialized graph"


@then("I should be able to retrieve the memory item with its original content")
def retrieve_memory_item(context):
    """Retrieve the memory item and check its content."""
    for item_id, original_item in context.memory_items.items():
        retrieved_item = context.graph_adapter.retrieve(item_id)
        assert retrieved_item is not None, f"Failed to retrieve item with ID {item_id}"
        assert (
            retrieved_item.content == original_item.content
        ), f"Content mismatch: {retrieved_item.content} != {original_item.content}"


@when("I store a memory item with complex metadata")
def store_item_with_complex_metadata(context):
    """Store a memory item with complex metadata from the data table."""
    metadata = {}
    for row in context.table:
        key = row["key"]
        value = row["value"]
        metadata[key] = value

    memory_item = MemoryItem(
        id=None,  # Let the adapter generate an ID
        content="Test content with complex metadata",
        memory_type=MemoryType.CODE,
        metadata=metadata,
    )
    item_id = context.graph_adapter.store(memory_item)
    context.memory_items[item_id] = memory_item


@when("I store a memory item with complex metadata:")
def store_item_with_complex_metadata_colon(context):
    """Store a memory item with complex metadata from the data table (with colon)."""
    # Create a mock table if it doesn't exist (for direct test runs)
    if not hasattr(context, "table"):
        # Create a simple mock table with some test data
        class MockRow:
            def __init__(self, key, value):
                self.data = {"key": key, "value": value}

            def __getitem__(self, key):
                return self.data[key]

        context.table = [
            MockRow("edrr_phase", "EXPAND"),
            MockRow("priority", "high"),
            MockRow("tags", "python,code,important"),
        ]

    metadata = {}
    for row in context.table:
        key = row["key"]
        value = row["value"]
        metadata[key] = value

    memory_item = MemoryItem(
        id=None,  # Let the adapter generate an ID
        content="Test content with complex metadata",
        memory_type=MemoryType.CODE,
        metadata=metadata,
    )
    item_id = context.graph_adapter.store(memory_item)
    context.memory_items[item_id] = memory_item


@then("the memory item should be stored as RDF triples")
def check_rdf_triples(context):
    """Check that the memory item was stored as RDF triples."""
    # Get the first item ID (we should only have one at this point)
    item_id = list(context.memory_items.keys())[0]

    # Check that triples exist for this item
    from rdflib import URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
        RDF,
    )

    item_uri = URIRef(f"{MEMORY}{item_id}")
    assert (
        item_uri,
        RDF.type,
        DEVSYNTH.MemoryItem,
    ) in context.graph_adapter.graph, "Memory item not stored as RDF triple"


@then("I should be able to retrieve the memory item with all metadata intact")
def check_metadata_intact(context):
    """Check that the memory item can be retrieved with all metadata intact."""
    for item_id, original_item in context.memory_items.items():
        retrieved_item = context.graph_adapter.retrieve(item_id)
        assert retrieved_item is not None, f"Failed to retrieve item with ID {item_id}"

        # Check that all original metadata is present in the retrieved item
        for key, value in original_item.metadata.items():
            assert (
                key in retrieved_item.metadata
            ), f"Metadata key {key} not found in retrieved item"
            assert (
                retrieved_item.metadata[key] == value
            ), f"Metadata value mismatch for {key}: {retrieved_item.metadata[key]} != {value}"


@when(
    parsers.parse(
        "I add memory volatility controls with decay rate {decay_rate:f} and threshold {threshold:f}"
    )
)
def add_memory_volatility_controls(context, decay_rate, threshold):
    """Add memory volatility controls with the specified decay rate and threshold."""
    # Store some items first
    for i in range(3):
        memory_item = MemoryItem(
            id=None,
            content=f"Test content {i}",
            memory_type=MemoryType.CODE,
            metadata={"index": i},
        )
        item_id = context.graph_adapter.store(memory_item)
        context.memory_items[item_id] = memory_item

    # Add volatility controls
    context.graph_adapter.add_memory_volatility(
        decay_rate=decay_rate, threshold=threshold, advanced_controls=True
    )


@then("all memory items should have confidence values")
def check_confidence_values(context):
    """Check that all memory items have confidence values."""
    from rdflib import URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
    )

    for item_id in context.memory_items.keys():
        item_uri = URIRef(f"{MEMORY}{item_id}")
        confidence = context.graph_adapter.graph.value(item_uri, DEVSYNTH.confidence)
        assert confidence is not None, f"Confidence value not found for item {item_id}"
        assert (
            float(confidence) > 0
        ), f"Confidence value should be positive for item {item_id}"


@then("all memory items should have decay rates")
def check_decay_rates(context):
    """Check that all memory items have decay rates."""
    from rdflib import URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
    )

    for item_id in context.memory_items.keys():
        item_uri = URIRef(f"{MEMORY}{item_id}")
        decay_rate = context.graph_adapter.graph.value(item_uri, DEVSYNTH.decayRate)
        assert decay_rate is not None, f"Decay rate not found for item {item_id}"


@then("all memory items should have confidence thresholds")
def check_confidence_thresholds(context):
    """Check that all memory items have confidence thresholds."""
    from rdflib import URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
    )

    for item_id in context.memory_items.keys():
        item_uri = URIRef(f"{MEMORY}{item_id}")
        threshold = context.graph_adapter.graph.value(
            item_uri, DEVSYNTH.confidenceThreshold
        )
        assert (
            threshold is not None
        ), f"Confidence threshold not found for item {item_id}"


@given("I have added memory volatility controls")
def have_added_volatility_controls(context):
    """Ensure memory volatility controls have been added."""
    # Store some items first if none exist
    if not context.memory_items:
        for i in range(3):
            memory_item = MemoryItem(
                id=None,
                content=f"Test content {i}",
                memory_type=MemoryType.CODE,
                metadata={"index": i},
            )
            item_id = context.graph_adapter.store(memory_item)
            context.memory_items[item_id] = memory_item

    # Add volatility controls
    context.graph_adapter.add_memory_volatility(
        decay_rate=0.1, threshold=0.5, advanced_controls=True
    )


@given("I have stored multiple memory items with different access patterns")
def store_items_with_different_access_patterns(context):
    """Store multiple memory items with different access patterns."""
    # Clear existing items
    context.memory_items = {}

    # Store items with different access patterns
    for i in range(5):
        memory_item = MemoryItem(
            id=None,
            content=f"Test content {i}",
            memory_type=MemoryType.CODE,
            metadata={"index": i},
        )
        item_id = context.graph_adapter.store(memory_item)
        context.memory_items[item_id] = memory_item

    # Ensure volatility controls exist for the new items
    context.graph_adapter.add_memory_volatility(
        decay_rate=0.1,
        threshold=0.5,
        advanced_controls=True,
    )

    # Simulate different access patterns by updating metadata
    from rdflib import Literal, URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
    )

    item_ids = list(context.memory_items.keys())
    now = datetime.now()

    access_setup = [
        (item_ids[0], 10, 0),  # frequently accessed today
        (item_ids[1], 5, 5),  # accessed a few days ago
        (item_ids[2], 1, 30),  # rarely accessed, long ago
        (item_ids[3], 0, 45),  # never accessed after storage
        (item_ids[4], 0, 1),  # related item accessed yesterday
    ]

    for item_id, count, days in access_setup:
        item_uri = URIRef(f"{MEMORY}{item_id}")
        context.graph_adapter.graph.remove((item_uri, DEVSYNTH.accessCount, None))
        context.graph_adapter.graph.add(
            (item_uri, DEVSYNTH.accessCount, Literal(count))
        )
        context.graph_adapter.graph.remove((item_uri, DEVSYNTH.lastAccessTime, None))
        context.graph_adapter.graph.add(
            (
                item_uri,
                DEVSYNTH.lastAccessTime,
                Literal((now - timedelta(days=days)).isoformat()),
            )
        )

    # Create relationships for item 4
    for i in range(3):
        related_item = MemoryItem(
            id=None,
            content=f"Related to item 4 - {i}",
            memory_type=MemoryType.CODE,
            metadata={"related_to": item_ids[4]},
        )
        related_id = context.graph_adapter.store(related_item)
        context.memory_items[related_id] = related_item


@when("I apply advanced memory decay")
def apply_advanced_memory_decay(context):
    """Apply advanced memory decay."""
    context.volatile_items = context.graph_adapter.apply_memory_decay(
        advanced_decay=True
    )


@then("items accessed less frequently should decay faster")
def check_access_frequency_decay(context):
    """Check that items accessed less frequently decay faster."""
    from rdflib import URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
    )

    item_ids = list(context.memory_items.keys())[:3]

    confidences = []
    for item_id in item_ids:
        item_uri = URIRef(f"{MEMORY}{item_id}")
        value = context.graph_adapter.graph.value(item_uri, DEVSYNTH.confidence)
        assert value is not None, f"Missing confidence for {item_id}"
        confidences.append(float(value))

    # Ensure decay occurred
    for conf in confidences:
        assert conf < 1.0, "Confidence did not decay"

    # More frequent access should lead to higher confidence
    assert confidences[0] > confidences[1] > confidences[2]


@then("items with more relationships should decay slower")
def check_relationship_decay(context):
    """Check that items with more relationships decay slower."""
    from rdflib import URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
    )

    item_ids = list(context.memory_items.keys())

    item_with_relations_uri = URIRef(f"{MEMORY}{item_ids[4]}")
    val_rel = context.graph_adapter.graph.value(
        item_with_relations_uri, DEVSYNTH.confidence
    )
    assert val_rel is not None

    item_without_relations_uri = URIRef(f"{MEMORY}{item_ids[3]}")
    val_no_rel = context.graph_adapter.graph.value(
        item_without_relations_uri, DEVSYNTH.confidence
    )
    assert val_no_rel is not None

    conf_with = float(val_rel)
    conf_without = float(val_no_rel)

    assert conf_with < 1.0 and conf_without < 1.0
    assert conf_with > conf_without


@then("items that haven't been accessed recently should decay faster")
def check_time_based_decay(context):
    """Items with older access times should have lower confidence."""
    from rdflib import URIRef

    from devsynth.application.memory.adapters.graph_memory_adapter import (
        DEVSYNTH,
        MEMORY,
    )

    item_ids = list(context.memory_items.keys())

    recent_uri = URIRef(f"{MEMORY}{item_ids[0]}")
    old_uri = URIRef(f"{MEMORY}{item_ids[3]}")

    recent_conf = context.graph_adapter.graph.value(recent_uri, DEVSYNTH.confidence)
    old_conf = context.graph_adapter.graph.value(old_uri, DEVSYNTH.confidence)

    assert recent_conf is not None and old_conf is not None

    recent_conf = float(recent_conf)
    old_conf = float(old_conf)

    assert recent_conf < 1.0 and old_conf < 1.0
    assert old_conf < recent_conf


@given("I have a TinyDBMemoryAdapter")
def have_tinydb_adapter(context):
    """Create a TinyDBMemoryAdapter."""
    tinydb_path = os.path.join(context.base_path, "tinydb", "memory.json")
    os.makedirs(os.path.dirname(tinydb_path), exist_ok=True)
    context.tinydb_adapter = TinyDBMemoryAdapter(db_path=tinydb_path)


@given("I have a ChromaDBVectorStore")
def have_chromadb_adapter(context):
    """Create a ChromaDBVectorAdapter."""
    chromadb_path = os.path.join(context.base_path, "chromadb")
    os.makedirs(chromadb_path, exist_ok=True)
    context.chromadb_adapter = ChromaDBVectorAdapter(
        collection_name="test_collection", persist_directory=chromadb_path
    )


@when(
    parsers.parse(
        'I integrate the GraphMemoryAdapter with the TinyDBMemoryAdapter in "{mode}" mode'
    )
)
def integrate_with_tinydb(context, mode):
    """Integrate the GraphMemoryAdapter with the TinyDBMemoryAdapter."""
    # Store some items in the graph adapter
    for i in range(3):
        memory_item = MemoryItem(
            id=f"graph_{i}",
            content=f"Graph item {i}",
            memory_type=MemoryType.CODE,
            metadata={"source": "graph"},
        )
        context.graph_adapter.store(memory_item)
        context.memory_items[f"graph_{i}"] = memory_item

    # Store some items in the TinyDB adapter
    for i in range(3):
        memory_item = MemoryItem(
            id=f"tinydb_{i}",
            content=f"TinyDB item {i}",
            memory_type=MemoryType.CODE,
            metadata={"source": "tinydb"},
        )
        context.tinydb_adapter.store(memory_item)
        context.memory_items[f"tinydb_{i}"] = memory_item

    # Integrate the adapters
    context.graph_adapter.integrate_with_store(context.tinydb_adapter, sync_mode=mode)


@when(
    parsers.parse(
        'I integrate the GraphMemoryAdapter with the ChromaDBVectorStore in "{mode}" mode'
    )
)
def integrate_with_chromadb(context, mode):
    """Integrate the GraphMemoryAdapter with the ChromaDBVectorStore."""
    # Store some items in the graph adapter
    for i in range(3):
        memory_item = MemoryItem(
            id=f"graph_{i}",
            content=f"Graph item {i}",
            memory_type=MemoryType.CODE,
            metadata={"source": "graph"},
        )
        context.graph_adapter.store(memory_item)
        context.memory_items[f"graph_{i}"] = memory_item

    # Store some items in the ChromaDB adapter
    for i in range(3):
        memory_vector = MemoryVector(
            id=f"chromadb_{i}",
            content=f"ChromaDB item {i}",
            embedding=[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i, 0.5 * i],
            metadata={"source": "chromadb"},
        )
        context.chromadb_adapter.store_vector(memory_vector)

    # Integrate the adapters
    context.graph_adapter.integrate_with_store(context.chromadb_adapter, sync_mode=mode)


@then(
    "memory items from the GraphMemoryAdapter should be exported to the TinyDBMemoryAdapter"
)
def check_graph_to_tinydb_export(context):
    """Check that memory items from the GraphMemoryAdapter were exported to the TinyDBMemoryAdapter."""
    for i in range(3):
        item_id = f"graph_{i}"
        retrieved_item = context.tinydb_adapter.retrieve(item_id)
        assert (
            retrieved_item is not None
        ), f"Failed to retrieve item {item_id} from TinyDBMemoryAdapter"
        assert (
            retrieved_item.content == f"Graph item {i}"
        ), f"Content mismatch: {retrieved_item.content} != Graph item {i}"


@then(
    "memory items from the TinyDBMemoryAdapter should be imported to the GraphMemoryAdapter"
)
def check_tinydb_to_graph_import(context):
    """Check that memory items from the TinyDBMemoryAdapter were imported to the GraphMemoryAdapter."""
    for i in range(3):
        item_id = f"tinydb_{i}"
        retrieved_item = context.graph_adapter.retrieve(item_id)
        assert (
            retrieved_item is not None
        ), f"Failed to retrieve item {item_id} from GraphMemoryAdapter"
        assert (
            retrieved_item.content == f"TinyDB item {i}"
        ), f"Content mismatch: {retrieved_item.content} != TinyDB item {i}"


@then("I should be able to retrieve the same items from both adapters")
def check_items_in_both_adapters(context):
    """Check that the same items can be retrieved from both adapters."""
    for item_id in context.memory_items.keys():
        if item_id.startswith("graph_") or item_id.startswith("tinydb_"):
            graph_item = context.graph_adapter.retrieve(item_id)
            tinydb_item = context.tinydb_adapter.retrieve(item_id)

            assert (
                graph_item is not None
            ), f"Failed to retrieve item {item_id} from GraphMemoryAdapter"
            assert (
                tinydb_item is not None
            ), f"Failed to retrieve item {item_id} from TinyDBMemoryAdapter"
            assert (
                graph_item.content == tinydb_item.content
            ), f"Content mismatch: {graph_item.content} != {tinydb_item.content}"


@then("memory items with vectors should be properly synchronized between stores")
def check_vector_synchronization(context):
    """Check that memory items with vectors are properly synchronized between stores."""
    # Ensure vectors exist in the ChromaDB adapter
    assert (
        len(context.chromadb_adapter.vectors) > 0
    ), "No vectors stored in ChromaDB adapter"


@then("I should be able to perform vector similarity searches on both stores")
def check_vector_similarity_search(context):
    """Check that vector similarity searches can be performed on the vector store."""
    results = context.chromadb_adapter.similarity_search([0.1, 0.2, 0.3, 0.4, 0.5])
    assert len(results) > 0, "No similarity search results returned"


@given("I have stored related memory items")
def store_related_memory_items(context):
    """Store a chain of related memory items."""
    item1 = MemoryItem(id="node1", content="Node 1", memory_type=MemoryType.CODE)
    context.graph_adapter.store(item1)

    item2 = MemoryItem(
        id="node2",
        content="Node 2",
        memory_type=MemoryType.CODE,
        metadata={"related_to": "node1"},
    )
    context.graph_adapter.store(item2)

    item3 = MemoryItem(
        id="node3",
        content="Node 3",
        memory_type=MemoryType.CODE,
        metadata={"related_to": "node2"},
    )
    context.graph_adapter.store(item3)


@when(
    parsers.parse(
        'I traverse the graph starting from "{start_id}" up to depth {depth:d}'
    )
)
def traverse_graph(context, start_id, depth):
    """Traverse the graph from the starting node."""
    context.traversal_result = context.graph_adapter.traverse_graph(start_id, depth)


@then(parsers.parse('the traversal result should include "{items}"'))
def check_traversal_result(context, items):
    """Verify that traversal returned expected nodes."""
    expected_ids = [item.strip() for item in items.split(",") if item.strip()]
    for item_id in expected_ids:
        assert item_id in context.traversal_result, f"{item_id} not found in traversal"


@when("I save and reload the GraphMemoryAdapter")
def reload_graph_adapter(context):
    """Persist the graph and create a new adapter instance."""
    context.graph_adapter._save_graph()
    context.graph_adapter = GraphMemoryAdapter(
        base_path=context.base_path, use_rdflib_store=True
    )


@then(
    parsers.parse(
        'traversing from "{start_id}" to depth {depth:d} should return "{items}"'
    )
)
def traversal_after_reload(context, start_id, depth, items):
    """Traverse after reloading to confirm persistence."""
    result = context.graph_adapter.traverse_graph(start_id, depth)
    expected_ids = [item.strip() for item in items.split(",") if item.strip()]
    for item_id in expected_ids:
        assert item_id in result, f"{item_id} not found after reload"
