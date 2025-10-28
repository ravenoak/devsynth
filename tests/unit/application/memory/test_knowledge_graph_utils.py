import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pytest
from rdflib import Literal, Namespace, URIRef

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

try:
    from devsynth.application.memory.context_manager import InMemoryStore
    from devsynth.application.memory.knowledge_graph_utils import (
        MEMORY,
        create_relationship,
        delete_relationship,
        find_items_by_relationship,
        find_related_items,
        get_item_relationships,
        get_subgraph,
        query_graph_pattern,
    )
    from devsynth.application.memory.memory_manager import MemoryManager
    from devsynth.application.memory.rdflib_store import RDFLibStore
except Exception as exc:
    pytest.skip(f"Memory utilities unavailable: {exc}", allow_module_level=True)
from devsynth.exceptions import MemoryStoreError


class TestKnowledgeGraphUtils:
    """Tests for the knowledge graph utility functions.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a RDFLibStore instance for testing."""
        store = RDFLibStore(temp_dir)
        yield store
        if os.path.exists(os.path.join(temp_dir, "memory.ttl")):
            os.remove(os.path.join(temp_dir, "memory.ttl"))

    @pytest.fixture
    def sample_items(self, store):
        """Create and store sample memory items for testing."""
        items = [
            MemoryItem(
                id="",
                content="Class definition for User",
                memory_type=MemoryType.CODE_ANALYSIS,
                metadata={"file": "user.py", "type": "class", "name": "User"},
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Method definition for authenticate",
                memory_type=MemoryType.CODE_ANALYSIS,
                metadata={
                    "file": "user.py",
                    "type": "method",
                    "name": "authenticate",
                    "class": "User",
                },
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Function definition for hash_password",
                memory_type=MemoryType.CODE_ANALYSIS,
                metadata={
                    "file": "utils.py",
                    "type": "function",
                    "name": "hash_password",
                },
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Test case for User authentication",
                memory_type=MemoryType.EPISODIC,
                metadata={
                    "file": "test_user.py",
                    "type": "test",
                    "name": "test_user_authentication",
                },
                created_at=datetime.now(),
            ),
        ]
        item_ids = []
        for item in items:
            item_id = store.store(item)
            item_ids.append(item_id)
        create_relationship(store, item_ids[0], item_ids[1], "has_method")
        create_relationship(store, item_ids[1], item_ids[2], "calls")
        create_relationship(store, item_ids[3], item_ids[0], "tests")
        return item_ids

    @pytest.mark.medium
    def test_find_related_items_succeeds(self, store, sample_items):
        """Test finding items related to a given item.

        ReqID: N/A"""
        related_items = find_related_items(store, sample_items[0])
        assert len(related_items) == 2
        assert any(
            item.metadata.get("name") == "authenticate" for item in related_items
        )
        assert any(
                item.metadata.get("name") == "test_user_authentication"
                for item in related_items
        )
        related_items = find_related_items(store, sample_items[1])
        assert len(related_items) == 2
        assert any(item.metadata.get("name") == "User" for item in related_items)
        assert any(
            item.metadata.get("name") == "hash_password" for item in related_items
        )

    @pytest.mark.medium
    def test_find_items_by_relationship_succeeds(self, store, sample_items):
        """Test finding items by a specific relationship.

        ReqID: N/A"""
        related_items = find_items_by_relationship(store, "calls")
        assert len(related_items) == 2
        assert related_items[0][0].metadata.get("name") == "authenticate"
        assert related_items[1][0].metadata.get("name") == "hash_password"
        related_items = find_items_by_relationship(store, "tests")
        assert len(related_items) == 2
        assert any(
                item.metadata.get("name") == "test_user_authentication"
                for item in related_items[0]
        )
        assert any(item.metadata.get("name") == "User" for item in related_items[1])

    @pytest.mark.medium
    def test_get_item_relationships_succeeds(self, store, sample_items):
        """Test getting all relationships for an item.

        ReqID: N/A"""
        relationships = get_item_relationships(store, sample_items[0])
        assert len(relationships) == 2
        assert any(rel["relationship"] == "has_method" for rel in relationships)
        assert any(rel["relationship"] == "tests" for rel in relationships)
        relationships = get_item_relationships(store, sample_items[1])
        assert len(relationships) == 2
        assert any(rel["relationship"] == "has_method" for rel in relationships)
        assert any(rel["relationship"] == "calls" for rel in relationships)

    @pytest.mark.medium
    def test_create_and_delete_relationship_succeeds(self, store, sample_items):
        """Test creating and deleting a relationship between items.

        ReqID: N/A"""
        create_relationship(store, sample_items[0], sample_items[3], "documented_by")
        relationships = get_item_relationships(store, sample_items[0])
        assert any(rel["relationship"] == "documented_by" for rel in relationships)
        delete_relationship(store, sample_items[0], sample_items[3], "documented_by")
        relationships = get_item_relationships(store, sample_items[0])
        assert not any(
            rel["relationship"] == "documented_by" for rel in relationships
        )

    @pytest.mark.medium
    def test_query_graph_pattern_succeeds(self, store, sample_items):
        """Test querying the graph with a specific pattern.

        ReqID: N/A"""
        results = query_graph_pattern(
            store,
            "\n            ?item a <https://github.com/ravenoak/devsynth/ontology/memory#MemoryItem> .\n        ",
        )
        assert len(results) > 0
        results = query_graph_pattern(
            store,
            '\n            ?item a <https://github.com/ravenoak/devsynth/ontology/memory#MemoryItem> .\n            ?item <https://github.com/ravenoak/devsynth/ontology/memory#memoryType> ?type .\n            FILTER(?type = "code_analysis")\n        ',
        )
        assert len(results) > 0
        create_relationship(
            store, sample_items[0], sample_items[1], "test_relationship"
        )
        results = query_graph_pattern(
            store,
            "\n            ?source <https://github.com/ravenoak/devsynth/ontology/memory#test_relationship> ?target .\n        ",
        )
        assert len(results) == 1

    @pytest.mark.medium
    def test_get_subgraph_succeeds(self, store, sample_items):
        """Test getting a subgraph centered on a specific item.

        ReqID: N/A"""
        subgraph = get_subgraph(store, sample_items[1], depth=2)
        assert len(subgraph["nodes"]) == 4
        assert len(subgraph["edges"]) == 3
        subgraph = get_subgraph(store, sample_items[1], depth=1)
        assert len(subgraph["nodes"]) == 3
        assert len(subgraph["edges"]) == 2

    @pytest.fixture
    def sync_manager(self):
        """Provide a simple SyncManager with two in-memory stores."""
        adapters = {"s1": InMemoryStore(), "s2": InMemoryStore()}
        manager = MemoryManager(adapters=adapters)
        return (manager.sync_manager, adapters)

    @pytest.mark.medium
    def test_synchronize_basic_succeeds(self, sync_manager):
        """Test that synchronize basic succeeds.

        ReqID: N/A"""
        sm, adapters = sync_manager
        adapters["s1"].store(
            MemoryItem(id="a", content="A", memory_type=MemoryType.CODE)
        )
        result = sm.synchronize("s1", "s2")
        assert result == {"s1_to_s2": 1}
        assert adapters["s2"].retrieve("a") is not None

    @pytest.mark.medium
    def test_synchronize_missing_adapter_succeeds(self, sync_manager):
        """Test that synchronize missing adapter succeeds.

        ReqID: N/A"""
        sm, _ = sync_manager
        assert sm.synchronize("missing", "s2") == {"missing_to_s2": 0}

    @pytest.mark.medium
    def test_synchronize_bidirectional_succeeds(self, sync_manager):
        """Test that synchronize bidirectional succeeds.

        ReqID: N/A"""
        sm, adapters = sync_manager
        adapters["s1"].store(
            MemoryItem(id="a", content="A", memory_type=MemoryType.CODE)
        )
        result = sm.synchronize("s1", "s2", bidirectional=True)
        assert result["s1_to_s2"] == 1
        assert result["s2_to_s1"] == 1
        assert adapters["s2"].retrieve("a") is not None

    @pytest.mark.medium
    def test_update_and_queue_succeeds(self, sync_manager):
        """Test that update and queue succeeds.

        ReqID: N/A"""
        sm, adapters = sync_manager
        item = MemoryItem(id="u", content="U", memory_type=MemoryType.CODE)
        assert sm.update_item("s1", item) is True
        assert adapters["s2"].retrieve("u") is not None
        assert sm.update_item("missing", item) is False
        item_q = MemoryItem(id="q", content="Q", memory_type=MemoryType.CODE)
        sm.queue_update("s1", item_q)
        sm.flush_queue()
        assert adapters["s2"].retrieve("q") is not None
