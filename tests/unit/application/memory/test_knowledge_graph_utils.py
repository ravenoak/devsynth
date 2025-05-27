import os
import json
import uuid
import pytest
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from rdflib import URIRef, Literal, Namespace

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.application.memory.rdflib_store import RDFLibStore
from devsynth.application.memory.knowledge_graph_utils import MEMORY
from devsynth.application.memory.knowledge_graph_utils import (
    find_related_items,
    find_items_by_relationship,
    get_item_relationships,
    create_relationship,
    delete_relationship,
    query_graph_pattern,
    get_subgraph
)
from devsynth.exceptions import MemoryStoreError

class TestKnowledgeGraphUtils:
    """Tests for the knowledge graph utility functions."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a RDFLibStore instance for testing."""
        store = RDFLibStore(temp_dir)
        yield store
        # Clean up
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
                created_at=datetime.now()
            ),
            MemoryItem(
                id="",
                content="Method definition for authenticate",
                memory_type=MemoryType.CODE_ANALYSIS,
                metadata={"file": "user.py", "type": "method", "name": "authenticate", "class": "User"},
                created_at=datetime.now()
            ),
            MemoryItem(
                id="",
                content="Function definition for hash_password",
                memory_type=MemoryType.CODE_ANALYSIS,
                metadata={"file": "utils.py", "type": "function", "name": "hash_password"},
                created_at=datetime.now()
            ),
            MemoryItem(
                id="",
                content="Test case for User authentication",
                memory_type=MemoryType.EPISODIC,
                metadata={"file": "test_user.py", "type": "test", "name": "test_user_authentication"},
                created_at=datetime.now()
            )
        ]

        item_ids = []
        for item in items:
            item_id = store.store(item)
            item_ids.append(item_id)

        # Create relationships between items
        create_relationship(store, item_ids[0], item_ids[1], "has_method")
        create_relationship(store, item_ids[1], item_ids[2], "calls")
        create_relationship(store, item_ids[3], item_ids[0], "tests")

        return item_ids

    def test_find_related_items(self, store, sample_items):
        """Test finding items related to a given item."""
        # Find items related to the User class
        related_items = find_related_items(store, sample_items[0])

        # Should find the authenticate method and the test case
        assert len(related_items) == 2
        assert any(item.metadata.get("name") == "authenticate" for item in related_items)
        assert any(item.metadata.get("name") == "test_user_authentication" for item in related_items)

        # Find items related to the authenticate method
        related_items = find_related_items(store, sample_items[1])

        # Should find the User class and the hash_password function
        assert len(related_items) == 2
        assert any(item.metadata.get("name") == "User" for item in related_items)
        assert any(item.metadata.get("name") == "hash_password" for item in related_items)

    def test_find_items_by_relationship(self, store, sample_items):
        """Test finding items by a specific relationship."""
        # Find items that have a "calls" relationship
        related_items = find_items_by_relationship(store, "calls")

        # Should find the authenticate method and hash_password function
        assert len(related_items) == 2
        assert related_items[0][0].metadata.get("name") == "authenticate"
        assert related_items[1][0].metadata.get("name") == "hash_password"

        # Find items that have a "tests" relationship
        related_items = find_items_by_relationship(store, "tests")

        # Should find the test case and User class
        assert len(related_items) == 2
        assert any(item.metadata.get("name") == "test_user_authentication" for item in related_items[0])
        assert any(item.metadata.get("name") == "User" for item in related_items[1])

    def test_get_item_relationships(self, store, sample_items):
        """Test getting all relationships for an item."""
        # Get relationships for the User class
        relationships = get_item_relationships(store, sample_items[0])

        # Should have two relationships: has_method and tests
        assert len(relationships) == 2
        assert any(rel["relationship"] == "has_method" for rel in relationships)
        assert any(rel["relationship"] == "tests" for rel in relationships)

        # Get relationships for the authenticate method
        relationships = get_item_relationships(store, sample_items[1])

        # Should have two relationships: has_method and calls
        assert len(relationships) == 2
        assert any(rel["relationship"] == "has_method" for rel in relationships)
        assert any(rel["relationship"] == "calls" for rel in relationships)

    def test_create_and_delete_relationship(self, store, sample_items):
        """Test creating and deleting a relationship between items."""
        # Create a new relationship
        create_relationship(store, sample_items[0], sample_items[3], "documented_by")

        # Verify the relationship exists
        relationships = get_item_relationships(store, sample_items[0])
        assert any(rel["relationship"] == "documented_by" for rel in relationships)

        # Delete the relationship
        delete_relationship(store, sample_items[0], sample_items[3], "documented_by")

        # Verify the relationship no longer exists
        relationships = get_item_relationships(store, sample_items[0])
        assert not any(rel["relationship"] == "documented_by" for rel in relationships)

    def test_query_graph_pattern(self, store, sample_items):
        """Test querying the graph with a specific pattern."""
        # Create a simple query to test the function
        results = query_graph_pattern(store, """
            ?item a <http://devsynth.org/ontology/memory#MemoryItem> .
        """)

        # Should find all memory items
        assert len(results) > 0

        # Create a more specific query
        results = query_graph_pattern(store, """
            ?item a <http://devsynth.org/ontology/memory#MemoryItem> .
            ?item <http://devsynth.org/ontology/memory#memoryType> ?type .
            FILTER(?type = "code_analysis")
        """)

        # Should find code analysis items
        assert len(results) > 0

        # Test with a relationship query
        create_relationship(store, sample_items[0], sample_items[1], "test_relationship")

        results = query_graph_pattern(store, """
            ?source <http://devsynth.org/ontology/memory#test_relationship> ?target .
        """)

        # Should find the test relationship
        assert len(results) == 1

    def test_get_subgraph(self, store, sample_items):
        """Test getting a subgraph centered on a specific item."""
        # Get subgraph centered on the authenticate method
        subgraph = get_subgraph(store, sample_items[1], depth=2)

        # Should include all items since they're all connected within 2 steps
        assert len(subgraph["nodes"]) == 4
        assert len(subgraph["edges"]) == 3

        # Get subgraph with depth 1
        subgraph = get_subgraph(store, sample_items[1], depth=1)

        # Should include only directly connected items
        assert len(subgraph["nodes"]) == 3  # authenticate, User, and hash_password
        assert len(subgraph["edges"]) == 2  # has_method and calls
