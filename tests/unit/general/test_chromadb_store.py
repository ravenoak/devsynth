"""
Unit tests for the ChromaDBStore class.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType

try:
    from devsynth.application.memory.chromadb_store import ChromaDBStore
except Exception as exc:
    pytest.skip(f"ChromaDBStore unavailable: {exc}", allow_module_level=True)
pytestmark = pytest.mark.requires_resource("chromadb")


class TestChromaDBStore(unittest.TestCase):
    """Test the ChromaDBStore class.

    ReqID: N/A"""

    def setUp(self):
        """Set up the test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = ChromaDBStore(self.temp_dir)

    def tearDown(self):
        """Clean up the test environment."""
        shutil.rmtree(self.temp_dir)

    def test_store_and_retrieve_succeeds(self):
        """Test storing and retrieving items.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"},
        )
        item_id = self.store.store(item)
        self.assertEqual(item_id, item.id)
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.id, item.id)
        self.assertEqual(retrieved_item.content, item.content)
        self.assertEqual(retrieved_item.memory_type, item.memory_type)
        self.assertEqual(retrieved_item.metadata["test"], item.metadata["test"])

    def test_search_exact_match_matches_expected(self):
        """Test searching for items with exact match.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id="item-1",
                content="This is item 1",
                memory_type=MemoryType.LONG_TERM,
                metadata={"category": "test", "priority": "high"},
            ),
            MemoryItem(
                id="item-2",
                content="This is item 2",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"category": "test", "priority": "medium"},
            ),
            MemoryItem(
                id="item-3",
                content="This is item 3",
                memory_type=MemoryType.LONG_TERM,
                metadata={"category": "production", "priority": "high"},
            ),
        ]
        for item in items:
            self.store.store(item)
        results = self.store.search({"memory_type": MemoryType.LONG_TERM})
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if no_file_logging:
            print(
                "In test environment with in-memory ChromaDB client, exact search behavior may differ"
            )
            self.assertTrue(len(results) > 0)
            item_ids = [item.id for item in results]
            self.assertIn("item-1", item_ids)
            self.assertIn("item-3", item_ids)
        else:
            self.assertEqual(len(results), 2)
            self.assertTrue(any(item.id == "item-1" for item in results))
            self.assertTrue(any(item.id == "item-3" for item in results))
        results = self.store.search(
            {"memory_type": MemoryType.LONG_TERM, "metadata.category": "test"}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "item-1")

    def test_search_semantic_succeeds(self):
        """Test semantic search for items.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id="item-1",
                content="Python is a programming language with clean syntax",
                memory_type=MemoryType.LONG_TERM,
                metadata={"topic": "Python programming"},
            ),
            MemoryItem(
                id="item-2",
                content="Machine learning algorithms can learn from data",
                memory_type=MemoryType.LONG_TERM,
                metadata={"topic": "Machine learning"},
            ),
            MemoryItem(
                id="item-3",
                content="Web development involves creating websites and web applications",
                memory_type=MemoryType.LONG_TERM,
                metadata={"topic": "Web development"},
            ),
        ]
        for item in items:
            self.store.store(item)
        results = self.store.search(
            {"semantic_query": "Programming languages and software development"}
        )
        self.assertTrue(len(results) > 0)
        relevant_topics = ["Python programming", "Web development"]
        self.assertTrue(
            any(item.metadata["topic"] in relevant_topics for item in results[:2])
        )

    def test_delete_succeeds(self):
        """Test deleting items.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"},
        )
        self.store.store(item)
        result = self.store.delete(item.id)
        self.assertTrue(result)
        retrieved_item = self.store.retrieve(item.id)
        self.assertIsNone(retrieved_item)
        result = self.store.delete("non-existent-id")
        self.assertFalse(result)

    def test_persistence_succeeds(self):
        """Test that items persist across store instances.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"},
        )
        self.store.store(item)
        new_store = ChromaDBStore(self.temp_dir)
        retrieved_item = new_store.retrieve(item.id)
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.id, item.id)
        self.assertEqual(retrieved_item.content, item.content)
        self.assertEqual(retrieved_item.memory_type, item.memory_type)
        self.assertEqual(retrieved_item.metadata["test"], item.metadata["test"])

    def test_token_usage_succeeds(self):
        """Test token usage tracking.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id=f"item-{i}",
                content=f"This is test item {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"test": "metadata"},
            )
            for i in range(5)
        ]
        for item in items:
            self.store.store(item)
        token_usage = self.store.get_token_usage()
        self.assertIsInstance(token_usage, int)
        self.assertTrue(token_usage > 0)


if __name__ == "__main__":
    unittest.main()
