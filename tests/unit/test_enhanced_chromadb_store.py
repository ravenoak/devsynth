"""
Unit tests for the enhanced ChromaDBStore class.
"""
import os
import json
import shutil
import tempfile
import unittest
import uuid
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch, MagicMock, call

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.application.memory.chromadb_store import ChromaDBStore


class TestEnhancedChromaDBStore(unittest.TestCase):
    """Test the enhanced features of the ChromaDBStore class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for ChromaDB
        self.temp_dir = tempfile.mkdtemp()

        # Ensure we're using a clean environment for each test
        os.environ["DEVSYNTH_NO_FILE_LOGGING"] = "1"

        # Generate unique collection names for this test
        test_id = str(uuid.uuid4())
        self.collection_name = f"test_collection_{test_id}"
        self.versions_collection_name = f"test_versions_{test_id}"

        # Create a new store for each test
        self.store = ChromaDBStore(self.temp_dir)

        # Override the collection names and create new collections
        self.store.collection_name = self.collection_name
        self.store.versions_collection_name = self.versions_collection_name

        # Create new collections with unique names
        self.store.collection = self.store.client.create_collection(name=self.collection_name)
        self.store.versions_collection = self.store.client.create_collection(name=self.versions_collection_name)

    def tearDown(self):
        """Clean up the test environment."""
        # Clear the cache to ensure test isolation
        self.store._cache = {}

        # Delete the collections we created
        try:
            self.store.client.delete_collection(name=self.collection_name)
            self.store.client.delete_collection(name=self.versions_collection_name)
        except Exception as e:
            print(f"Error deleting collections: {e}")

        # Remove the temporary directory
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error removing temporary directory: {e}")

    def test_caching(self):
        """Test that the caching layer reduces disk I/O operations."""
        # Create a memory item
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"}
        )

        # Store the item
        self.store.store(item)

        # Mock the _retrieve_from_db method to track calls
        with patch.object(self.store, '_retrieve_from_db', wraps=self.store._retrieve_from_db) as mock_retrieve:
            # Retrieve the item multiple times
            for _ in range(5):
                retrieved_item = self.store.retrieve(item.id)
                self.assertIsNotNone(retrieved_item)

            # Verify that _retrieve_from_db was called only once
            self.assertEqual(mock_retrieve.call_count, 1)

    def test_cache_invalidation(self):
        """Test that the cache is invalidated when an item is updated."""
        # Create a memory item
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"}
        )

        # Store the item
        self.store.store(item)

        # Retrieve the item to cache it
        retrieved_item = self.store.retrieve(item.id)

        # Update the item
        updated_item = MemoryItem(
            id="test-item",
            content="This is an updated test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "updated_metadata"}
        )
        self.store.store(updated_item)

        # Mock the _retrieve_from_db method to track calls
        with patch.object(self.store, '_retrieve_from_db', wraps=self.store._retrieve_from_db) as mock_retrieve:
            # Retrieve the item again
            retrieved_item = self.store.retrieve(item.id)

            # Verify that _retrieve_from_db was called
            mock_retrieve.assert_called_once()

            # Verify that the updated item is returned
            self.assertEqual(retrieved_item.content, "This is an updated test item")
            self.assertEqual(retrieved_item.metadata["test"], "updated_metadata")

    def test_versioning(self):
        """Test that versions are tracked when items are updated."""
        # Create a memory item
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1}
        )

        # Store the item
        self.store.store(item)

        # Update the item multiple times
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i}
            )
            self.store.store(updated_item)

        # Get all versions of the item
        versions = self.store.get_versions("test-item")

        # Verify that all versions are available
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].content, "Version 1")
        self.assertEqual(versions[1].content, "Version 2")
        self.assertEqual(versions[2].content, "Version 3")

    def test_retrieve_specific_version(self):
        """Test retrieving a specific version of an item."""
        # Create a memory item
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1}
        )

        # Store the item
        self.store.store(item)

        # Update the item multiple times
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i}
            )
            self.store.store(updated_item)

        # Retrieve a specific version
        version2 = self.store.retrieve_version("test-item", 2)

        # Verify that the correct version is returned
        self.assertEqual(version2.content, "Version 2")
        self.assertEqual(version2.metadata["version"], 2)

    def test_get_history(self):
        """Test retrieving the history of an item."""
        # Create a memory item
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1}
        )

        # Store the item
        self.store.store(item)

        # Update the item multiple times
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i}
            )
            self.store.store(updated_item)

        # Get the history of the item
        history = self.store.get_history("test-item")

        # Verify that the history contains all versions
        self.assertEqual(len(history), 3)

        # Verify that each history entry has the required fields
        for entry in history:
            self.assertIn("timestamp", entry)
            self.assertIn("version", entry)
            self.assertIn("content_summary", entry)

    def test_latest_version_by_default(self):
        """Test that the latest version is returned by default."""
        # Create a memory item
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1}
        )

        # Store the item
        self.store.store(item)

        # Update the item multiple times
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i}
            )
            self.store.store(updated_item)

        # Retrieve the item without specifying a version
        latest = self.store.retrieve("test-item")

        # Verify that the latest version is returned
        self.assertEqual(latest.content, "Version 3")
        self.assertEqual(latest.metadata["version"], 3)

    def test_optimized_embeddings(self):
        """Test that embeddings are optimized for similar content."""
        # Create and store similar items
        base_content = "This is a test item about Python programming"
        for i in range(5):
            item = MemoryItem(
                id=f"similar-item-{i}",
                content=f"{base_content} with slight variation {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"index": i}
            )
            self.store.store(item)

        # Verify that embeddings are optimized
        self.assertTrue(self.store.has_optimized_embeddings())

        # Verify the embedding storage efficiency
        efficiency = self.store.get_embedding_storage_efficiency()
        self.assertGreater(efficiency, 0.7)  # 70% efficiency


if __name__ == "__main__":
    unittest.main()
