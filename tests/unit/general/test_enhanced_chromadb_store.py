"""
Unit tests for the enhanced ChromaDBStore class.
"""

import os

import pytest

pytest.importorskip("chromadb")
chromadb_enabled = os.environ.get("ENABLE_CHROMADB", "false").lower() not in {
    "0",
    "false",
    "no",
}
if not chromadb_enabled:
    pytest.skip("ChromaDB feature not enabled", allow_module_level=True)
import json
import shutil
import tempfile
import unittest
import uuid
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, call, patch

from devsynth.application.memory.chromadb_store import ChromaDBStore
from devsynth.domain.models.memory import MemoryItem, MemoryType

pytestmark = pytest.mark.requires_resource("chromadb")


class TestEnhancedChromaDBStore(unittest.TestCase):
    """Test the enhanced features of the ChromaDBStore class.

    ReqID: N/A"""

    def setUp(self):
        """Set up the test environment."""
        self.temp_dir = tempfile.mkdtemp()
        os.environ["DEVSYNTH_NO_FILE_LOGGING"] = "1"
        test_id = str(uuid.uuid4())
        self.collection_name = f"test_collection_{test_id}"
        self.versions_collection_name = f"test_versions_{test_id}"
        self.store = ChromaDBStore(self.temp_dir)
        self.store.collection_name = self.collection_name
        self.store.versions_collection_name = self.versions_collection_name
        self.store.collection = self.store.client.create_collection(
            name=self.collection_name
        )
        self.store.versions_collection = self.store.client.create_collection(
            name=self.versions_collection_name
        )

    def tearDown(self):
        """Clean up the test environment."""
        self.store._cache = {}
        try:
            self.store.client.delete_collection(name=self.collection_name)
            self.store.client.delete_collection(name=self.versions_collection_name)
        except Exception as e:
            print(f"Error deleting collections: {e}")
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error removing temporary directory: {e}")

    @pytest.mark.fast
    def test_caching_succeeds(self):
        """Test that the caching layer reduces disk I/O operations.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"},
        )
        self.store.store(item)
        with patch.object(
            self.store, "_retrieve_from_db", wraps=self.store._retrieve_from_db
        ) as mock_retrieve:
            for _ in range(5):
                retrieved_item = self.store.retrieve(item.id)
                self.assertIsNotNone(retrieved_item)
            self.assertEqual(mock_retrieve.call_count, 1)

    @pytest.mark.fast
    def test_cache_invalidation_is_valid(self):
        """Test that the cache is invalidated when an item is updated.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "metadata"},
        )
        self.store.store(item)
        retrieved_item = self.store.retrieve(item.id)
        updated_item = MemoryItem(
            id="test-item",
            content="This is an updated test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "updated_metadata"},
        )
        self.store.store(updated_item)
        with patch.object(
            self.store, "_retrieve_from_db", wraps=self.store._retrieve_from_db
        ) as mock_retrieve:
            retrieved_item = self.store.retrieve(item.id)
            mock_retrieve.assert_called_once()
            self.assertEqual(retrieved_item.content, "This is an updated test item")
            self.assertEqual(retrieved_item.metadata["test"], "updated_metadata")

    @pytest.mark.fast
    def test_versioning_succeeds(self):
        """Test that versions are tracked when items are updated.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1},
        )
        self.store.store(item)
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i},
            )
            self.store.store(updated_item)
        versions = self.store.get_versions("test-item")
        self.assertEqual(len(versions), 3)
        self.assertEqual(versions[0].content, "Version 1")
        self.assertEqual(versions[1].content, "Version 2")
        self.assertEqual(versions[2].content, "Version 3")

    @pytest.mark.fast
    def test_retrieve_specific_version_succeeds(self):
        """Test retrieving a specific version of an item.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1},
        )
        self.store.store(item)
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i},
            )
            self.store.store(updated_item)
        version2 = self.store.retrieve_version("test-item", 2)
        self.assertEqual(version2.content, "Version 2")
        self.assertEqual(version2.metadata["version"], 2)

    @pytest.mark.fast
    def test_get_history_succeeds(self):
        """Test retrieving the history of an item.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1},
        )
        self.store.store(item)
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i},
            )
            self.store.store(updated_item)
        history = self.store.get_history("test-item")
        self.assertEqual(len(history), 3)
        for entry in history:
            self.assertIn("timestamp", entry)
            self.assertIn("version", entry)
            self.assertIn("content_summary", entry)

    @pytest.mark.fast
    def test_latest_version_by_default_returns_expected_result(self):
        """Test that the latest version is returned by default.

        ReqID: N/A"""
        item = MemoryItem(
            id="test-item",
            content="Version 1",
            memory_type=MemoryType.LONG_TERM,
            metadata={"version": 1},
        )
        self.store.store(item)
        for i in range(2, 4):
            updated_item = MemoryItem(
                id="test-item",
                content=f"Version {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"version": i},
            )
            self.store.store(updated_item)
        latest = self.store.retrieve("test-item")
        self.assertEqual(latest.content, "Version 3")
        self.assertEqual(latest.metadata["version"], 3)

    @pytest.mark.fast
    def test_optimized_embeddings_succeeds(self):
        """Test that embeddings are optimized for similar content.

        ReqID: N/A"""
        base_content = "This is a test item about Python programming"
        for i in range(5):
            item = MemoryItem(
                id=f"similar-item-{i}",
                content=f"{base_content} with slight variation {i}",
                memory_type=MemoryType.LONG_TERM,
                metadata={"index": i},
            )
            self.store.store(item)
        self.assertTrue(self.store.has_optimized_embeddings())
        efficiency = self.store.get_embedding_storage_efficiency()
        self.assertGreater(efficiency, 0.7)


if __name__ == "__main__":
    unittest.main()
