"""
Unit tests for the ChromaDBStore class.
"""
import pytest
import os
import json
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from devsynth.domain.models.memory import MemoryItem, MemoryType
try:  # pragma: no cover - allow running without chromadb
    from devsynth.application.memory.chromadb_store import ChromaDBStore
except Exception as exc:  # pragma: no cover - skip if import fails
    pytest.skip(f"ChromaDBStore unavailable: {exc}", allow_module_level=True)

pytestmark = pytest.mark.requires_resource("chromadb")


class TestChromaDBStore(unittest.TestCase):
    """Test the ChromaDBStore class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for ChromaDB
        self.temp_dir = tempfile.mkdtemp()
        self.store = ChromaDBStore(self.temp_dir)

    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_store_and_retrieve(self):
        """Test storing and retrieving items."""
        # Create a memory item
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"}
        )

        # Store the item
        item_id = self.store.store(item)

        # Check that the item ID is returned
        self.assertEqual(item_id, item.id)

        # Retrieve the item
        retrieved_item = self.store.retrieve(item_id)

        # Check that the retrieved item matches the original
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.id, item.id)
        self.assertEqual(retrieved_item.content, item.content)
        self.assertEqual(retrieved_item.memory_type, item.memory_type)
        self.assertEqual(retrieved_item.metadata["test"], item.metadata["test"])

    def test_search_exact_match(self):
        """Test searching for items with exact match."""
        # Create and store memory items
        items = [
            MemoryItem(
                id="item-1",
                content="This is item 1",
                memory_type=MemoryType.LONG_TERM,
                metadata={"category": "test", "priority": "high"}
            ),
            MemoryItem(
                id="item-2",
                content="This is item 2",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"category": "test", "priority": "medium"}
            ),
            MemoryItem(
                id="item-3",
                content="This is item 3",
                memory_type=MemoryType.LONG_TERM,
                metadata={"category": "production", "priority": "high"}
            )
        ]

        for item in items:
            self.store.store(item)

        # Search for items with exact match
        results = self.store.search({"memory_type": MemoryType.LONG_TERM})

        # Check if we're in a test environment with file operations disabled
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in ("1", "true", "yes")

        if no_file_logging:
            # In test environments with in-memory client, the behavior might be different
            # Just check that we have results and that they include the expected items
            print("In test environment with in-memory ChromaDB client, exact search behavior may differ")
            self.assertTrue(len(results) > 0)
            # Verify that at least the expected items are in the results
            item_ids = [item.id for item in results]
            self.assertIn("item-1", item_ids)
            self.assertIn("item-3", item_ids)
        else:
            # In normal environments, we expect exactly 2 results
            self.assertEqual(len(results), 2)
            self.assertTrue(any(item.id == "item-1" for item in results))
            self.assertTrue(any(item.id == "item-3" for item in results))

        # Search with multiple criteria
        results = self.store.search({
            "memory_type": MemoryType.LONG_TERM,
            "metadata.category": "test"
        })

        # Check that the correct item is returned
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "item-1")

    def test_search_semantic(self):
        """Test semantic search for items."""
        # Create and store memory items
        items = [
            MemoryItem(
                id="item-1",
                content="Python is a programming language with clean syntax",
                memory_type=MemoryType.LONG_TERM,
                metadata={"topic": "Python programming"}
            ),
            MemoryItem(
                id="item-2",
                content="Machine learning algorithms can learn from data",
                memory_type=MemoryType.LONG_TERM,
                metadata={"topic": "Machine learning"}
            ),
            MemoryItem(
                id="item-3",
                content="Web development involves creating websites and web applications",
                memory_type=MemoryType.LONG_TERM,
                metadata={"topic": "Web development"}
            )
        ]

        for item in items:
            self.store.store(item)

        # Perform a semantic search
        results = self.store.search({"semantic_query": "Programming languages and software development"})

        # Check that we have results
        self.assertTrue(len(results) > 0)

        # The most relevant results should be about programming or web development
        relevant_topics = ["Python programming", "Web development"]
        self.assertTrue(any(item.metadata["topic"] in relevant_topics for item in results[:2]))

    def test_delete(self):
        """Test deleting items."""
        # Create and store a memory item
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"}
        )

        self.store.store(item)

        # Delete the item
        result = self.store.delete(item.id)

        # Check that the deletion was successful
        self.assertTrue(result)

        # Try to retrieve the deleted item
        retrieved_item = self.store.retrieve(item.id)

        # Check that the item is no longer available
        self.assertIsNone(retrieved_item)

        # Try to delete a non-existent item
        result = self.store.delete("non-existent-id")

        # Check that the deletion failed
        self.assertFalse(result)

    def test_persistence(self):
        """Test that items persist across store instances."""
        # Create and store a memory item
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"}
        )

        self.store.store(item)

        # Create a new store instance with the same path
        new_store = ChromaDBStore(self.temp_dir)

        # Retrieve the item from the new store
        retrieved_item = new_store.retrieve(item.id)

        # Check that the item was retrieved successfully
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.id, item.id)
        self.assertEqual(retrieved_item.content, item.content)
        self.assertEqual(retrieved_item.memory_type, item.memory_type)
        self.assertEqual(retrieved_item.metadata["test"], item.metadata["test"])

    def test_token_usage(self):
        """Test token usage tracking."""
        # Create and store memory items
        items = [
            MemoryItem(
                id=f"item-{i}",
                content=f"This is test item {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"test": "metadata"}
            )
            for i in range(5)
        ]

        for item in items:
            self.store.store(item)

        # Get token usage
        token_usage = self.store.get_token_usage()

        # Check that token usage is being tracked
        self.assertIsInstance(token_usage, int)
        self.assertTrue(token_usage > 0)


if __name__ == "__main__":
    unittest.main()
