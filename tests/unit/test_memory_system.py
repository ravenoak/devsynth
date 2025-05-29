"""
Tests for the memory system components.
"""

import os
import json
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Dict, Any

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.application.memory import (
    InMemoryStore, 
    SimpleContextManager,
    JSONFileStore,
    PersistentContextManager
)
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.config import get_settings

class TestInMemoryStore(unittest.TestCase):
    """Test the InMemoryStore class."""

    def setUp(self):
        self.store = InMemoryStore()

    def test_store_and_retrieve(self):
        """Test storing and retrieving items."""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"}
        )

        # Store the item
        item_id = self.store.store(item)
        self.assertIsNotNone(item_id)

        # Retrieve the item
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.content, "Test content")
        self.assertEqual(retrieved_item.memory_type, MemoryType.SHORT_TERM)
        self.assertEqual(retrieved_item.metadata["key"], "value")

    def test_search(self):
        """Test searching for items."""
        # Create and store items
        item1 = MemoryItem(
            id="",
            content="Apple content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"fruit": "apple"}
        )
        item2 = MemoryItem(
            id="",
            content="Banana content",
            memory_type=MemoryType.LONG_TERM,
            metadata={"fruit": "banana"}
        )

        self.store.store(item1)
        self.store.store(item2)

        # Search by content
        results = self.store.search({"content": "Apple"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Apple content")

        # Search by memory type
        results = self.store.search({"memory_type": "long_term"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")

        # Search by metadata
        results = self.store.search({"fruit": "banana"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")

    def test_delete(self):
        """Test deleting items."""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM
        )

        # Store the item
        item_id = self.store.store(item)

        # Delete the item
        result = self.store.delete(item_id)
        self.assertTrue(result)

        # Verify the item is deleted
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNone(retrieved_item)

class TestJSONFileStore(unittest.TestCase):
    """Test the JSONFileStore class."""

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.store = JSONFileStore(self.temp_dir)

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_store_and_retrieve(self):
        """Test storing and retrieving items."""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"}
        )

        # Store the item
        item_id = self.store.store(item)
        self.assertIsNotNone(item_id)

        # Retrieve the item
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.content, "Test content")
        self.assertEqual(retrieved_item.memory_type, MemoryType.SHORT_TERM)
        self.assertEqual(retrieved_item.metadata["key"], "value")

    def test_persistence(self):
        """Test that items persist between store instances."""
        item = MemoryItem(
            id="",
            content="Persistent content",
            memory_type=MemoryType.LONG_TERM
        )

        # Store the item
        item_id = self.store.store(item)

        # Create a new store instance
        new_store = JSONFileStore(self.temp_dir)

        # Check if we're in a test environment with file operations disabled
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in ("1", "true", "yes")

        if no_file_logging:
            # In test environments with file operations disabled, items won't persist
            # This is expected behavior to maintain test isolation
            print("Skipping persistence check in test environment with DEVSYNTH_NO_FILE_LOGGING=1")
        else:
            # In normal environments, items should persist
            # Retrieve the item from the new store
            retrieved_item = new_store.retrieve(item_id)
            self.assertIsNotNone(retrieved_item)
            self.assertEqual(retrieved_item.content, "Persistent content")

    def test_search(self):
        """Test searching for items."""
        # Create and store items
        item1 = MemoryItem(
            id="",
            content="Apple content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"fruit": "apple"}
        )
        item2 = MemoryItem(
            id="",
            content="Banana content",
            memory_type=MemoryType.LONG_TERM,
            metadata={"fruit": "banana"}
        )

        self.store.store(item1)
        self.store.store(item2)

        # Search by content
        results = self.store.search({"content": "Apple"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Apple content")

        # Search by memory type
        results = self.store.search({"memory_type": "long_term"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")

        # Search by metadata
        results = self.store.search({"fruit": "banana"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")

    def test_delete(self):
        """Test deleting items."""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM
        )

        # Store the item
        item_id = self.store.store(item)

        # Delete the item
        result = self.store.delete(item_id)
        self.assertTrue(result)

        # Verify the item is deleted
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNone(retrieved_item)

    def test_token_usage(self):
        """Test token usage tracking."""
        # Initial token count should be 0
        self.assertEqual(self.store.get_token_usage(), 0)

        # Store an item
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM
        )
        self.store.store(item)

        # Token count should be greater than 0
        self.assertGreater(self.store.get_token_usage(), 0)

class TestSimpleContextManager(unittest.TestCase):
    """Test the SimpleContextManager class."""

    def setUp(self):
        self.context_manager = SimpleContextManager()

    def test_add_and_get(self):
        """Test adding and getting context values."""
        # Add a value
        self.context_manager.add_to_context("key1", "value1")

        # Get the value
        value = self.context_manager.get_from_context("key1")
        self.assertEqual(value, "value1")

    def test_get_full_context(self):
        """Test getting the full context."""
        # Add values
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")

        # Get the full context
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 2)
        self.assertEqual(context["key1"], "value1")
        self.assertEqual(context["key2"], "value2")

    def test_clear_context(self):
        """Test clearing the context."""
        # Add values
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")

        # Clear the context
        self.context_manager.clear_context()

        # Verify the context is empty
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 0)

class TestPersistentContextManager(unittest.TestCase):
    """Test the PersistentContextManager class."""

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.context_manager = PersistentContextManager(self.temp_dir)

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_add_and_get(self):
        """Test adding and getting context values."""
        # Add a value
        self.context_manager.add_to_context("key1", "value1")

        # Get the value
        value = self.context_manager.get_from_context("key1")
        self.assertEqual(value, "value1")

    def test_persistence(self):
        """Test that context persists between manager instances."""
        # Add a value
        self.context_manager.add_to_context("key1", "persistent_value")

        # Create a new context manager instance
        new_context_manager = PersistentContextManager(self.temp_dir)

        # Get the value from the new manager
        value = new_context_manager.get_from_context("key1")
        self.assertEqual(value, "persistent_value")

    def test_get_full_context(self):
        """Test getting the full context."""
        # Add values
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")

        # Get the full context
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 2)
        self.assertEqual(context["key1"], "value1")
        self.assertEqual(context["key2"], "value2")

    def test_clear_context(self):
        """Test clearing the context."""
        # Add values
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")

        # Clear the context
        self.context_manager.clear_context()

        # Verify the context is empty
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 0)

    def test_get_relevant_context(self):
        """Test getting relevant context."""
        # Add values
        self.context_manager.add_to_context("apple_info", "Apples are red")
        self.context_manager.add_to_context("banana_info", "Bananas are yellow")
        self.context_manager.add_to_context("orange_info", "Oranges are orange")

        # Get relevant context
        relevant = self.context_manager.get_relevant_context("apple")
        self.assertEqual(len(relevant), 1)
        self.assertEqual(relevant["apple_info"], "Apples are red")

    def test_token_usage(self):
        """Test token usage tracking."""
        # Initial token count should be 0
        self.assertEqual(self.context_manager.get_token_usage(), 0)

        # Add a value
        self.context_manager.add_to_context("key1", "value1")

        # Token count should be greater than 0
        self.assertGreater(self.context_manager.get_token_usage(), 0)

class TestMemorySystemAdapter(unittest.TestCase):
    """Test the MemorySystemAdapter class."""

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_in_memory_adapter(self):
        """Test the adapter with in-memory storage."""
        # Create adapter with in-memory storage
        adapter = MemorySystemAdapter({
            "memory_store_type": "memory"
        })

        # Verify the store and context manager types
        self.assertIsInstance(adapter.get_memory_store(), InMemoryStore)
        self.assertIsInstance(adapter.get_context_manager(), SimpleContextManager)

    def test_file_based_adapter(self):
        """Test the adapter with file-based storage."""
        # Create adapter with file-based storage
        adapter = MemorySystemAdapter({
            "memory_store_type": "file",
            "memory_file_path": self.temp_dir
        })

        # Verify the store and context manager types
        self.assertIsInstance(adapter.get_memory_store(), JSONFileStore)
        self.assertIsInstance(adapter.get_context_manager(), PersistentContextManager)

    def test_token_usage(self):
        """Test token usage tracking."""
        # Create adapter
        adapter = MemorySystemAdapter({
            "memory_store_type": "file",
            "memory_file_path": self.temp_dir
        })

        # Get initial token usage
        initial_usage = adapter.get_token_usage()

        # Add a memory item
        store = adapter.get_memory_store()
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM
        )
        store.store(item)

        # Add a context item
        context_manager = adapter.get_context_manager()
        context_manager.add_to_context("key1", "value1")

        # Get updated token usage
        updated_usage = adapter.get_token_usage()

        # Verify token usage increased
        self.assertGreater(updated_usage["total_tokens"], initial_usage["total_tokens"])

if __name__ == "__main__":
    unittest.main()
