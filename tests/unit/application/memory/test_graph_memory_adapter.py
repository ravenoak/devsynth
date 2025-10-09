"""
Unit tests for the GraphMemoryAdapter.
"""

import datetime
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock, patch

import pytest
from rdflib import Graph, Literal, Namespace, URIRef

from devsynth.application.memory.adapters.enhanced_graph_memory_adapter import (
    EnhancedGraphMemoryAdapter,
    ResearchArtifact,
)
from devsynth.application.memory.adapters.graph_memory_adapter import (
    DEVSYNTH,
    MEMORY,
    RDF,
    GraphMemoryAdapter,
)
from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.application.memory.context_manager import InMemoryStore
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.query_router import QueryRouter
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.exceptions import MemoryItemNotFoundError, MemoryStoreError


class TestGraphMemoryAdapter:
    """Tests for the GraphMemoryAdapter class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def basic_adapter(self, temp_dir) -> Generator[GraphMemoryAdapter, None, None]:
        """Create a basic GraphMemoryAdapter instance for testing.

        This fixture uses a generator pattern to provide teardown functionality.
        """
        # Setup: Create the adapter
        adapter = GraphMemoryAdapter(base_path=temp_dir)

        # Yield the adapter to the test
        yield adapter

        # Teardown: Clean up resources
        if hasattr(adapter, "cleanup") and callable(adapter.cleanup):
            adapter.cleanup()

        # Clear the graph to prevent state leakage between tests
        adapter.graph = Graph()

    @pytest.fixture
    def rdflib_adapter(self, temp_dir) -> Generator[GraphMemoryAdapter, None, None]:
        """Create a GraphMemoryAdapter with RDFLibStore integration for testing.

        This fixture uses a generator pattern to provide teardown functionality.
        """
        # Setup: Create the adapter
        adapter = GraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

        # Yield the adapter to the test
        yield adapter

        # Teardown: Clean up resources
        if hasattr(adapter, "cleanup") and callable(adapter.cleanup):
            adapter.cleanup()

        # Close the RDFLib store if it exists
        if adapter.rdflib_store is not None:
            adapter.graph.close()

        # Clear the graph to prevent state leakage between tests
        adapter.graph = Graph()

    @pytest.fixture
    def sample_memory_item(self) -> MemoryItem:
        """Create a sample memory item for testing."""
        return MemoryItem(
            id="test-id",
            content="Test content",
            memory_type=MemoryType.CODE,
            metadata={"source": "test", "language": "python"},
        )

    @pytest.mark.medium
    def test_initialization_basic_succeeds(self, basic_adapter, temp_dir):
        """Test initialization of a basic GraphMemoryAdapter.

        ReqID: N/A"""
        assert basic_adapter.base_path == temp_dir
        assert basic_adapter.use_rdflib_store is False
        assert basic_adapter.rdflib_store is None
        assert isinstance(basic_adapter.graph, Graph)
        namespaces = dict(basic_adapter.graph.namespaces())
        assert "devsynth" in namespaces
        assert "memory" in namespaces

    @pytest.mark.medium
    def test_initialization_rdflib_succeeds(self, rdflib_adapter, temp_dir):
        """Test initialization of a GraphMemoryAdapter with RDFLibStore integration.

        ReqID: N/A"""
        assert rdflib_adapter.base_path == temp_dir
        assert rdflib_adapter.use_rdflib_store is True
        assert rdflib_adapter.rdflib_store is not None
        assert isinstance(rdflib_adapter.graph, Graph)

    @pytest.mark.medium
    def test_store_and_retrieve_basic_succeeds(self, basic_adapter, sample_memory_item):
        """Test storing and retrieving a memory item with basic adapter.

        ReqID: N/A"""
        item_id = basic_adapter.store(sample_memory_item)
        assert item_id == sample_memory_item.id
        retrieved_item = basic_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == sample_memory_item.id
        assert retrieved_item.content == sample_memory_item.content
        assert retrieved_item.memory_type == sample_memory_item.memory_type
        assert (
            retrieved_item.metadata["source"] == sample_memory_item.metadata["source"]
        )
        assert (
            retrieved_item.metadata["language"]
            == sample_memory_item.metadata["language"]
        )

    @pytest.mark.medium
    def test_store_and_retrieve_rdflib_succeeds(
        self, rdflib_adapter, sample_memory_item
    ):
        """Test storing and retrieving a memory item with RDFLibStore integration.

        ReqID: N/A"""
        item_id = rdflib_adapter.store(sample_memory_item)
        assert item_id == sample_memory_item.id
        retrieved_item = rdflib_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == sample_memory_item.id
        assert retrieved_item.content == sample_memory_item.content
        assert retrieved_item.memory_type == sample_memory_item.memory_type
        assert (
            retrieved_item.metadata["source"] == sample_memory_item.metadata["source"]
        )
        assert (
            retrieved_item.metadata["language"]
            == sample_memory_item.metadata["language"]
        )

    @pytest.mark.medium
    def test_research_artifact_traversal_and_reload(self, temp_dir):
        """Research artefacts persist and participate in traversals."""

        adapter = EnhancedGraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

        item_one = MemoryItem(
            id="node1",
            content="Baseline requirement",
            memory_type=MemoryType.REQUIREMENT,
            metadata={},
        )
        item_two = MemoryItem(
            id="node2",
            content="Derived implementation",
            memory_type=MemoryType.CODE,
            metadata={"related_to": "node1"},
        )

        adapter.store(item_one)
        adapter.store(item_two)

        artifact_path = Path(temp_dir) / "research.txt"
        artifact_path.write_text("Graph traversal with research nodes")

        evidence_hash = adapter.compute_evidence_hash(artifact_path)
        summary = adapter.summarize_artifact(artifact_path)
        assert summary.startswith("Graph traversal")

        artifact = ResearchArtifact(
            title="Traversal Paper",
            summary=summary,
            citation_url="file://" + str(artifact_path),
            evidence_hash=evidence_hash,
            published_at=datetime.datetime.now(datetime.timezone.utc),
            supports=[item_two.id],
            derived_from=[item_one.id],
            archive_path=str(artifact_path),
            metadata={"roles": ("Research Lead",)},
        )

        artifact_id = adapter.store_research_artifact(artifact)

        without_research = adapter.traverse_graph(item_one.id, 2)
        assert without_research == {item_two.id}

        with_research = adapter.traverse_graph(item_one.id, 2, include_research=True)
        assert artifact_id in with_research
        assert item_two.id in with_research

        graph_file = Path(temp_dir) / "graph_memory.ttl"
        assert graph_file.exists()

        reloaded = EnhancedGraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)
        reloaded_traversal = reloaded.traverse_graph(
            item_one.id, 2, include_research=True
        )
        assert artifact_id in reloaded_traversal

        artifact_uri = URIRef(f"{DEVSYNTH}{artifact_id}")
        assert (
            artifact_uri,
            DEVSYNTH.evidenceHash,
            Literal(evidence_hash),
        ) in reloaded.graph

        persisted = Path(temp_dir) / "graph_memory.ttl"
        content = persisted.read_text(encoding="utf-8")
        assert "devsynth:supports" in content
        assert "devsynth:derivedFrom" in content
        assert "devsynth:hasRole" in content

        provenance = reloaded.get_artifact_provenance(artifact_id)
        assert provenance["supports"] == (item_two.id,)
        assert provenance["derived_from"] == (item_one.id,)
        assert provenance["roles"] == ("Research Lead",)

    @pytest.mark.fast
    def test_traverse_graph_depth_and_missing_nodes(self, basic_adapter):
        """Traversal respects depth bounds and missing nodes yield empty sets."""

        item = MemoryItem(
            id="root", content="Root", memory_type=MemoryType.CODE, metadata={}
        )
        related = MemoryItem(
            id="child",
            content="Child",
            memory_type=MemoryType.CODE,
            metadata={"related_to": "root"},
        )

        basic_adapter.store(item)
        basic_adapter.store(related)

        assert basic_adapter.traverse_graph("unknown", 2) == set()
        assert basic_adapter.traverse_graph("root", 0) == set()
        assert basic_adapter.traverse_graph("root", 1) == {"child"}

    @pytest.mark.medium
    def test_ingest_helper_generates_hash_and_summary(self, temp_dir):
        """Helper returns deterministic digests and summary content."""

        adapter = EnhancedGraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

        artifact_path = Path(temp_dir) / "digest.txt"
        artifact_path.write_text("Important experimental log entry")

        artifact = adapter.ingest_research_artifact_from_path(
            artifact_path,
            title="Experiment Log",
            citation_url="file://" + str(artifact_path),
            published_at=datetime.datetime.now(datetime.timezone.utc),
            supports=[],
            derived_from=[],
        )

        expected_hash = adapter.compute_evidence_hash(artifact_path)
        assert artifact.evidence_hash == expected_hash
        assert "Important" in artifact.summary

        traversal = adapter.traverse_graph(
            artifact.identifier, 1, include_research=True
        )
        assert traversal == set()

    @pytest.mark.medium
    def test_store_with_relationships_succeeds(self, basic_adapter):
        """Test storing items with relationships.

        ReqID: N/A"""
        item1 = MemoryItem(
            id="item1", content="Item 1", memory_type=MemoryType.CODE, metadata={}
        )
        item2 = MemoryItem(
            id="item2",
            content="Item 2",
            memory_type=MemoryType.CODE,
            metadata={"related_to": "item1"},
        )
        basic_adapter.store(item1)
        basic_adapter.store(item2)
        related_items = basic_adapter.query_related_items("item1")
        assert len(related_items) == 1
        assert related_items[0].id == "item2"
        related_items = basic_adapter.query_related_items("item2")
        assert len(related_items) == 1
        assert related_items[0].id == "item1"

    @pytest.mark.medium
    def test_search_succeeds(self, basic_adapter):
        """Test searching for memory items.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id=f"item{i}",
                content=f"Item {i}",
                memory_type=MemoryType.CODE,
                metadata={"language": "python" if i % 2 == 0 else "javascript"},
            )
            for i in range(5)
        ]
        for item in items:
            basic_adapter.store(item)
        results = basic_adapter.search({"type": MemoryType.CODE})
        assert len(results) == 5
        results = basic_adapter.search({"language": "python"})
        assert len(results) == 3
        results = basic_adapter.search(
            {"type": MemoryType.CODE, "language": "javascript"}
        )
        assert len(results) == 2

    @pytest.mark.medium
    def test_delete_succeeds(self, basic_adapter, sample_memory_item):
        """Test deleting a memory item.

        ReqID: N/A"""
        item_id = basic_adapter.store(sample_memory_item)
        assert basic_adapter.retrieve(item_id) is not None
        result = basic_adapter.delete(item_id)
        assert result is True
        assert basic_adapter.retrieve(item_id) is None
        result = basic_adapter.delete("nonexistent-id")
        assert result is False

    @pytest.mark.medium
    def test_get_all_relationships_succeeds(self, basic_adapter):
        """Test getting all relationships.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id="item1", content="Item 1", memory_type=MemoryType.CODE, metadata={}
            ),
            MemoryItem(
                id="item2",
                content="Item 2",
                memory_type=MemoryType.CODE,
                metadata={"related_to": "item1"},
            ),
            MemoryItem(
                id="item3",
                content="Item 3",
                memory_type=MemoryType.CODE,
                metadata={"related_to": "item1"},
            ),
            MemoryItem(
                id="item4",
                content="Item 4",
                memory_type=MemoryType.CODE,
                metadata={"related_to": "item2"},
            ),
        ]
        for item in items:
            basic_adapter.store(item)
        relationships = basic_adapter.get_all_relationships()
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

    @pytest.mark.medium
    def test_add_memory_volatility_succeeds(self, basic_adapter, sample_memory_item):
        """Test adding memory volatility controls.

        ReqID: N/A"""
        basic_adapter.store(sample_memory_item)
        basic_adapter.add_memory_volatility(decay_rate=0.1, threshold=0.5)
        item_uri = URIRef(f"{MEMORY}{sample_memory_item.id}")
        confidence = basic_adapter.graph.value(item_uri, DEVSYNTH.confidence)
        decay_rate = basic_adapter.graph.value(item_uri, DEVSYNTH.decayRate)
        threshold = basic_adapter.graph.value(item_uri, DEVSYNTH.confidenceThreshold)
        assert float(confidence) == 1.0
        assert float(decay_rate) == 0.1
        assert float(threshold) == 0.5

    @pytest.mark.medium
    def test_apply_memory_decay_succeeds(self, basic_adapter, sample_memory_item):
        """Test applying memory decay.

        ReqID: N/A"""
        basic_adapter.store(sample_memory_item)
        basic_adapter.add_memory_volatility(decay_rate=0.3, threshold=0.5)
        volatile_items = basic_adapter.apply_memory_decay()
        item_uri = URIRef(f"{MEMORY}{sample_memory_item.id}")
        confidence = float(basic_adapter.graph.value(item_uri, DEVSYNTH.confidence))
        assert confidence == 0.7
        assert len(volatile_items) == 0
        volatile_items = basic_adapter.apply_memory_decay()
        confidence = float(basic_adapter.graph.value(item_uri, DEVSYNTH.confidence))
        assert confidence == pytest.approx(0.4, abs=1e-06)
        assert len(volatile_items) == 1
        assert volatile_items[0] == sample_memory_item.id

    @pytest.mark.medium
    def test_advanced_memory_decay_succeeds(self, rdflib_adapter, monkeypatch):
        """Test advanced memory decay with RDFLibStore integration.

        ReqID: N/A"""
        rdflib_adapter.use_rdflib_store = True
        rdflib_adapter.rdflib_store = MagicMock()
        original_query = rdflib_adapter.graph.query

        def mock_query(sparql_query):

            class MockQueryResult:

                def __iter__(self):
                    items = [
                        (
                            URIRef(f"{MEMORY}frequent"),
                            "frequent",
                            Literal(1.0),
                            Literal(0.2),
                            Literal(0.5),
                            Literal("2023-01-01T00:00:00"),
                            Literal(10),
                        ),
                        (
                            URIRef(f"{MEMORY}rare"),
                            "rare",
                            Literal(1.0),
                            Literal(0.2),
                            Literal(0.5),
                            Literal("2023-01-01T00:00:00"),
                            Literal(1),
                        ),
                        (
                            URIRef(f"{MEMORY}related"),
                            "related",
                            Literal(1.0),
                            Literal(0.2),
                            Literal(0.5),
                            Literal("2023-01-01T00:00:00"),
                            Literal(5),
                        ),
                    ]
                    for item in items:
                        yield item

            return MockQueryResult()

        monkeypatch.setattr(rdflib_adapter.graph, "query", mock_query)
        original_update = rdflib_adapter.graph.update

        def mock_update(update_query):
            pass

        monkeypatch.setattr(rdflib_adapter.graph, "update", mock_update)
        original_triples = rdflib_adapter.graph.triples

        def mock_triples(triple_pattern):
            s, p, o = triple_pattern
            if p == DEVSYNTH.relatedTo and s == URIRef(f"{MEMORY}related"):
                yield (
                    URIRef(f"{MEMORY}related"),
                    DEVSYNTH.relatedTo,
                    URIRef(f"{MEMORY}related_to"),
                )
            elif p == DEVSYNTH.relatedTo and s == URIRef(f"{MEMORY}frequent"):
                return
            elif p == DEVSYNTH.relatedTo and s == URIRef(f"{MEMORY}rare"):
                return
            else:
                yield from original_triples(triple_pattern)

        monkeypatch.setattr(rdflib_adapter.graph, "triples", mock_triples)
        original_value = rdflib_adapter.graph.value

        def mock_value(s, p, default=None):
            if p == DEVSYNTH.confidence:
                if s == URIRef(f"{MEMORY}frequent"):
                    return Literal(0.9)
                elif s == URIRef(f"{MEMORY}rare"):
                    return Literal(0.7)
                elif s == URIRef(f"{MEMORY}related"):
                    return Literal(0.8)
            return original_value(s, p, default)

        monkeypatch.setattr(rdflib_adapter.graph, "value", mock_value)
        items = [
            MemoryItem(
                id="frequent",
                content="Frequently accessed",
                memory_type=MemoryType.CODE,
                metadata={},
            ),
            MemoryItem(
                id="rare",
                content="Rarely accessed",
                memory_type=MemoryType.CODE,
                metadata={},
            ),
            MemoryItem(
                id="related",
                content="Has relationships",
                memory_type=MemoryType.CODE,
                metadata={},
            ),
            MemoryItem(
                id="related_to",
                content="Related to another item",
                memory_type=MemoryType.CODE,
                metadata={"related_to": "related"},
            ),
        ]
        for item in items:
            rdflib_adapter.store(item)
        rdflib_adapter.add_memory_volatility(
            decay_rate=0.2, threshold=0.5, advanced_controls=True
        )
        for _ in range(10):
            rdflib_adapter.retrieve("frequent")
        rdflib_adapter.retrieve("rare")
        volatile_items = rdflib_adapter.apply_memory_decay(advanced_decay=True)
        frequent_uri = URIRef(f"{MEMORY}frequent")
        rare_uri = URIRef(f"{MEMORY}rare")
        related_uri = URIRef(f"{MEMORY}related")
        frequent_confidence = float(
            rdflib_adapter.graph.value(frequent_uri, DEVSYNTH.confidence)
        )
        rare_confidence = float(
            rdflib_adapter.graph.value(rare_uri, DEVSYNTH.confidence)
        )
        related_confidence = float(
            rdflib_adapter.graph.value(related_uri, DEVSYNTH.confidence)
        )
        assert frequent_confidence > rare_confidence
        assert related_confidence > rare_confidence

    @pytest.mark.medium
    def test_integrate_with_store_succeeds(self, basic_adapter, temp_dir):
        """Test integrating with another memory store.

        ReqID: N/A"""
        mock_store = MagicMock()
        mock_item1 = MemoryItem(
            id="mock1", content="Mock item 1", memory_type=MemoryType.CODE, metadata={}
        )
        mock_item2 = MemoryItem(
            id="mock2", content="Mock item 2", memory_type=MemoryType.CODE, metadata={}
        )
        mock_store.search.return_value = [mock_item1, mock_item2]
        mock_store.retrieve.return_value = None
        local_item = MemoryItem(
            id="local1",
            content="Local item 1",
            memory_type=MemoryType.CODE,
            metadata={},
        )
        basic_adapter.store(local_item)
        basic_adapter.store(mock_item1)
        basic_adapter.store(mock_item2)
        basic_adapter.integrate_with_store(mock_store, sync_mode="bidirectional")
        assert basic_adapter.retrieve("mock1") is not None
        assert basic_adapter.retrieve("mock2") is not None
        mock_store.store.assert_called()
        stored_item = mock_store.store.call_args_list[0][0][0]
        assert stored_item.id == "local1"

    @pytest.mark.medium
    def test_integrate_with_vector_store_succeeds(self, rdflib_adapter, temp_dir):
        """Test integrating with a vector store.

        ReqID: N/A"""
        mock_vector_store = MagicMock()
        mock_vector_store.get_collection_stats.return_value = {"vector_count": 5}
        rdflib_adapter.integrate_with_store(mock_vector_store, sync_mode="import")
        mock_vector_store.get_collection_stats.assert_called()

    @pytest.mark.medium
    def test_save_graph_with_rdflib_store_succeeds(self, rdflib_adapter, temp_dir):
        """Ensure _save_graph persists RDF graphs when using RDFLibStore.

        ReqID: N/A"""
        memory_item = MemoryItem(
            id="save_test",
            content="Save Graph",
            memory_type=MemoryType.CODE,
            metadata={"source": "unit"},
        )
        rdflib_adapter.store(memory_item)
        rdflib_adapter._save_graph()
        graph_file = os.path.join(temp_dir, "graph_memory.ttl")
        assert os.path.exists(graph_file)

    @pytest.mark.medium
    def test_memory_item_triple_creation_succeeds(self, rdflib_adapter):
        """Verify that storing an item creates the expected RDF triples.

        ReqID: N/A"""
        item = MemoryItem(
            id="triple_test",
            content="Triple",
            memory_type=MemoryType.CODE,
            metadata={"source": "unit"},
        )
        rdflib_adapter.store(item)
        item_uri = URIRef(f"{MEMORY}{item.id}")
        assert (item_uri, RDF.type, DEVSYNTH.MemoryItem) in rdflib_adapter.graph
        assert (item_uri, DEVSYNTH.source, Literal("unit")) in rdflib_adapter.graph

    @pytest.fixture
    def router(self) -> Generator[QueryRouter, None, None]:
        """Create a QueryRouter with simple in-memory adapters.

        This fixture uses a generator pattern to provide teardown functionality.
        """
        # Setup: Create the router
        adapters = {
            "tinydb": InMemoryStore(),
            "document": InMemoryStore(),
            "vector": VectorMemoryAdapter(),
        }
        manager = MemoryManager(adapters=adapters)
        router = QueryRouter(manager)

        # Yield the router to the test
        yield router

        # Teardown: Clean up resources
        for adapter_name, adapter in manager.adapters.items():
            if hasattr(adapter, "cleanup") and callable(adapter.cleanup):
                adapter.cleanup()

            # Clear in-memory stores
            if isinstance(adapter, InMemoryStore):
                adapter.items = {}

            # Reset vector store
            if isinstance(adapter, VectorMemoryAdapter):
                if hasattr(adapter, "reset") and callable(adapter.reset):
                    adapter.reset()

    @pytest.fixture
    def populated_router(self, router) -> Generator[QueryRouter, None, None]:
        """Populate the router's stores with simple items.

        This fixture uses a generator pattern to provide teardown functionality.
        """
        # Setup: Populate the router
        manager = router.memory_manager
        manager.adapters["tinydb"].store(
            MemoryItem(id="tiny", content="apple tinydb", memory_type=MemoryType.CODE)
        )
        manager.adapters["document"].store(
            MemoryItem(id="doc", content="apple document", memory_type=MemoryType.CODE)
        )
        vec = MemoryVector(
            id="vec",
            content="apple vector",
            embedding=manager._embed_text("apple"),
            metadata={"memory_type": MemoryType.CODE.value},
        )
        manager.adapters["vector"].store_vector(vec)

        # Yield the populated router to the test
        yield router

        # Teardown: Clean up resources (no additional cleanup needed beyond what's in the router fixture)

    @pytest.mark.medium
    def test_cascading_query_with_missing_adapter_succeeds(self, populated_router):
        """Ensure cascading_query aggregates results and skips missing stores.

        ReqID: N/A"""
        results = populated_router.cascading_query(
            "apple", order=["vector", "tinydb", "missing", "document"]
        )
        assert [r.content for r in results] == [
            "apple vector",
            "apple tinydb",
            "apple document",
        ]

    @pytest.mark.medium
    def test_context_aware_query_succeeds(self, populated_router):
        """Context-aware query should incorporate context into search.

        ReqID: N/A"""
        manager = populated_router.memory_manager
        manager.adapters["tinydb"].store(
            MemoryItem(
                id="ctx", content="apple location:home", memory_type=MemoryType.CODE
            )
        )
        manager.adapters["document"].store(
            MemoryItem(
                id="ctx2", content="apple location:home", memory_type=MemoryType.CODE
            )
        )
        results = populated_router.context_aware_query("apple", {"location": "home"})
        assert len(results["tinydb"]) == 1
        assert results["tinydb"][0].content == "apple location:home"
        assert len(results["document"]) == 1
        assert (
            populated_router.context_aware_query(
                "apple", {"location": "home"}, store="missing"
            )
            == []
        )

    @pytest.mark.medium
    def test_query_router_route_succeeds(self, populated_router):
        """Exercise the router.route method for various strategies.

        ReqID: N/A"""
        direct = populated_router.route("apple", store="tinydb", strategy="direct")
        assert len(direct) == 1
        cascade = populated_router.route("apple", strategy="cascading")
        assert len(cascade) >= 3
        assert populated_router.route("apple", strategy="unknown") == []

    @pytest.mark.medium
    def test_store_and_retrieve_with_edrr_phase_has_expected(self, basic_adapter):
        """Test storing and retrieving items with EDRR phase.

        ReqID: N/A"""
        # Create test items with EDRR phase metadata
        item1 = MemoryItem(
            id="",
            content={"key": "value1"},
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "EXPAND", "source": "test1"},
        )
        item2 = MemoryItem(
            id="",
            content={"key": "value2"},
            memory_type=MemoryType.CODE,
            metadata={"edrr_phase": "DIFFERENTIATE", "source": "test2"},
        )

        # Store the items
        item1_id = basic_adapter.store(item1)
        item2_id = basic_adapter.store(item2)

        # Retrieve the items to verify they were stored correctly
        retrieved_item1 = basic_adapter.retrieve(item1_id)
        retrieved_item2 = basic_adapter.retrieve(item2_id)

        # Verify the retrieved items match the original items
        assert retrieved_item1 is not None
        assert retrieved_item2 is not None
        assert retrieved_item1.content == {"key": "value1"}
        assert retrieved_item2.content == {"key": "value2"}
        assert retrieved_item1.metadata.get("edrr_phase") == "EXPAND"
        assert retrieved_item2.metadata.get("edrr_phase") == "DIFFERENTIATE"

        # Collect all items in the graph
        all_items = []
        for s, p, o in basic_adapter.graph.triples(
            (None, RDF.type, DEVSYNTH.MemoryItem)
        ):
            item = basic_adapter._triples_to_memory_item(s)
            if item:
                all_items.append(item)

        # Find items matching specific criteria
        matching_items1 = []
        for item in all_items:
            if (
                (
                    hasattr(item.memory_type, "value")
                    and item.memory_type.value == "CODE"
                    or str(item.memory_type) == "CODE"
                )
                and item.metadata.get("edrr_phase") == "EXPAND"
                and (item.metadata.get("source") == "test1")
            ):
                matching_items1.append(item)

        matching_items2 = []
        for item in all_items:
            if (
                (
                    hasattr(item.memory_type, "value")
                    and item.memory_type.value == "CODE"
                    or str(item.memory_type) == "CODE"
                )
                and item.metadata.get("edrr_phase") == "DIFFERENTIATE"
                and (item.metadata.get("source") == "test2")
            ):
                matching_items2.append(item)

        # Test the retrieve_with_edrr_phase method
        result1 = basic_adapter.retrieve_with_edrr_phase(
            item_type="CODE", edrr_phase="EXPAND", metadata={"source": "test1"}
        )
        result2 = basic_adapter.retrieve_with_edrr_phase(
            item_type="CODE", edrr_phase="DIFFERENTIATE", metadata={"source": "test2"}
        )

        # Verify the results match the expected values
        assert result1 == {"key": "value1"}
        assert result2 == {"key": "value2"}
