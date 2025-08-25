"""
Tests for the memory system components.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Any, Dict

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType

try:
    from devsynth.application.memory import (
        InMemoryStore,
        JSONFileStore,
        PersistentContextManager,
        SimpleContextManager,
    )
except Exception as exc:
    pytest.skip(f"Memory system unavailable: {exc}", allow_module_level=True)
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.config import get_settings


class TestInMemoryStore(unittest.TestCase):
    """Test the InMemoryStore class.

    ReqID: N/A"""

    def setUp(self):
        self.store = InMemoryStore()

    def test_store_and_retrieve_succeeds(self):
        """Test storing and retrieving items.

        ReqID: N/A"""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
        )
        item_id = self.store.store(item)
        self.assertIsNotNone(item_id)
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.content, "Test content")
        self.assertEqual(retrieved_item.memory_type, MemoryType.SHORT_TERM)
        self.assertEqual(retrieved_item.metadata["key"], "value")

    def test_search_succeeds(self):
        """Test searching for items.

        ReqID: N/A"""
        item1 = MemoryItem(
            id="",
            content="Apple content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"fruit": "apple"},
        )
        item2 = MemoryItem(
            id="",
            content="Banana content",
            memory_type=MemoryType.LONG_TERM,
            metadata={"fruit": "banana"},
        )
        self.store.store(item1)
        self.store.store(item2)
        results = self.store.search({"content": "Apple"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Apple content")
        results = self.store.search({"memory_type": "long_term"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")
        results = self.store.search({"fruit": "banana"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")

    def test_delete_succeeds(self):
        """Test deleting items.

        ReqID: N/A"""
        item = MemoryItem(
            id="", content="Test content", memory_type=MemoryType.SHORT_TERM
        )
        item_id = self.store.store(item)
        result = self.store.delete(item_id)
        self.assertTrue(result)
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNone(retrieved_item)


class TestJSONFileStore(unittest.TestCase):
    """Test the JSONFileStore class.

    ReqID: N/A"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = JSONFileStore(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_store_and_retrieve_succeeds(self):
        """Test storing and retrieving items.

        ReqID: N/A"""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
        )
        item_id = self.store.store(item)
        self.assertIsNotNone(item_id)
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.content, "Test content")
        self.assertEqual(retrieved_item.memory_type, MemoryType.SHORT_TERM)
        self.assertEqual(retrieved_item.metadata["key"], "value")

    def test_persistence_succeeds(self):
        """Test that items persist between store instances.

        ReqID: N/A"""
        item = MemoryItem(
            id="", content="Persistent content", memory_type=MemoryType.LONG_TERM
        )
        item_id = self.store.store(item)
        new_store = JSONFileStore(self.temp_dir)
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if no_file_logging:
            print(
                "Skipping persistence check in test environment with DEVSYNTH_NO_FILE_LOGGING=1"
            )
        else:
            retrieved_item = new_store.retrieve(item_id)
            self.assertIsNotNone(retrieved_item)
            self.assertEqual(retrieved_item.content, "Persistent content")

    def test_search_succeeds(self):
        """Test searching for items.

        ReqID: N/A"""
        item1 = MemoryItem(
            id="",
            content="Apple content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"fruit": "apple"},
        )
        item2 = MemoryItem(
            id="",
            content="Banana content",
            memory_type=MemoryType.LONG_TERM,
            metadata={"fruit": "banana"},
        )
        self.store.store(item1)
        self.store.store(item2)
        results = self.store.search({"content": "Apple"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Apple content")
        results = self.store.search({"memory_type": "long_term"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")
        results = self.store.search({"fruit": "banana"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Banana content")

    def test_delete_succeeds(self):
        """Test deleting items.

        ReqID: N/A"""
        item = MemoryItem(
            id="", content="Test content", memory_type=MemoryType.SHORT_TERM
        )
        item_id = self.store.store(item)
        result = self.store.delete(item_id)
        self.assertTrue(result)
        retrieved_item = self.store.retrieve(item_id)
        self.assertIsNone(retrieved_item)

    def test_token_usage_succeeds(self):
        """Test token usage tracking.

        ReqID: N/A"""
        self.assertEqual(self.store.get_token_usage(), 0)
        item = MemoryItem(
            id="", content="Test content", memory_type=MemoryType.SHORT_TERM
        )
        self.store.store(item)
        self.assertGreater(self.store.get_token_usage(), 0)


class TestSimpleContextManager(unittest.TestCase):
    """Test the SimpleContextManager class.

    ReqID: N/A"""

    def setUp(self):
        self.context_manager = SimpleContextManager()

    def test_add_and_get_succeeds(self):
        """Test adding and getting context values.

        ReqID: N/A"""
        self.context_manager.add_to_context("key1", "value1")
        value = self.context_manager.get_from_context("key1")
        self.assertEqual(value, "value1")

    def test_get_full_context_succeeds(self):
        """Test getting the full context.

        ReqID: N/A"""
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 2)
        self.assertEqual(context["key1"], "value1")
        self.assertEqual(context["key2"], "value2")

    def test_clear_context_succeeds(self):
        """Test clearing the context.

        ReqID: N/A"""
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")
        self.context_manager.clear_context()
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 0)


class TestPersistentContextManager(unittest.TestCase):
    """Test the PersistentContextManager class.

    ReqID: N/A"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.context_manager = PersistentContextManager(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_add_and_get_succeeds(self):
        """Test adding and getting context values.

        ReqID: N/A"""
        self.context_manager.add_to_context("key1", "value1")
        value = self.context_manager.get_from_context("key1")
        self.assertEqual(value, "value1")

    def test_persistence_succeeds(self):
        """Test that context persists between manager instances.

        ReqID: N/A"""
        self.context_manager.add_to_context("key1", "persistent_value")
        new_context_manager = PersistentContextManager(self.temp_dir)
        value = new_context_manager.get_from_context("key1")
        self.assertEqual(value, "persistent_value")

    def test_get_full_context_succeeds(self):
        """Test getting the full context.

        ReqID: N/A"""
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 2)
        self.assertEqual(context["key1"], "value1")
        self.assertEqual(context["key2"], "value2")

    def test_clear_context_succeeds(self):
        """Test clearing the context.

        ReqID: N/A"""
        self.context_manager.add_to_context("key1", "value1")
        self.context_manager.add_to_context("key2", "value2")
        self.context_manager.clear_context()
        context = self.context_manager.get_full_context()
        self.assertEqual(len(context), 0)

    def test_get_relevant_context_succeeds(self):
        """Test getting relevant context.

        ReqID: N/A"""
        self.context_manager.add_to_context("apple_info", "Apples are red")
        self.context_manager.add_to_context("banana_info", "Bananas are yellow")
        self.context_manager.add_to_context("orange_info", "Oranges are orange")
        relevant = self.context_manager.get_relevant_context("apple")
        self.assertEqual(len(relevant), 1)
        self.assertEqual(relevant["apple_info"], "Apples are red")

    def test_token_usage_succeeds(self):
        """Test token usage tracking.

        ReqID: N/A"""
        self.assertEqual(self.context_manager.get_token_usage(), 0)
        self.context_manager.add_to_context("key1", "value1")
        self.assertGreater(self.context_manager.get_token_usage(), 0)


class TestMemorySystemAdapter(unittest.TestCase):
    """Test the MemorySystemAdapter class.

    ReqID: N/A"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_in_memory_adapter_succeeds(self):
        """Test the adapter with in-memory storage.

        ReqID: N/A"""
        adapter = MemorySystemAdapter({"memory_store_type": "memory"})
        self.assertIsInstance(adapter.get_memory_store(), InMemoryStore)
        self.assertIsInstance(adapter.get_context_manager(), SimpleContextManager)

    def test_file_based_adapter_succeeds(self):
        """Test the adapter with file-based storage.

        ReqID: N/A"""
        adapter = MemorySystemAdapter(
            {"memory_store_type": "file", "memory_file_path": self.temp_dir}
        )
        self.assertIsInstance(adapter.get_memory_store(), JSONFileStore)
        self.assertIsInstance(adapter.get_context_manager(), PersistentContextManager)

    def test_token_usage_succeeds(self):
        """Test token usage tracking.

        ReqID: N/A"""
        adapter = MemorySystemAdapter(
            {"memory_store_type": "file", "memory_file_path": self.temp_dir}
        )
        initial_usage = adapter.get_token_usage()
        store = adapter.get_memory_store()
        item = MemoryItem(
            id="", content="Test content", memory_type=MemoryType.SHORT_TERM
        )
        store.store(item)
        context_manager = adapter.get_context_manager()
        context_manager.add_to_context("key1", "value1")
        updated_usage = adapter.get_token_usage()
        self.assertGreater(updated_usage["total_tokens"], initial_usage["total_tokens"])


if __name__ == "__main__":
    unittest.main()
