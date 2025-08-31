"""
Unit tests for the MemorySystemAdapter with ChromaDB integration.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from devsynth.adapters.memory.chroma_db_adapter import ChromaDBAdapter
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.exceptions import MemoryStoreError

pytestmark = pytest.mark.requires_resource("chromadb")


class TestMemorySystemWithChromaDB:
    """Test the MemorySystemAdapter with ChromaDB integration.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory_system(self, temp_dir):
        """Create a MemorySystemAdapter instance with ChromaDB for testing."""
        config = {
            "memory_store_type": "chromadb",
            "memory_file_path": temp_dir,
            "vector_store_enabled": True,
            "chromadb_collection_name": "test_vectors",
        }
        return MemorySystemAdapter(config=config)

    @pytest.mark.fast
    def test_initialization_with_chromadb_succeeds(self, temp_dir):
        """Test that the memory system initializes correctly with ChromaDB.

        ReqID: N/A"""
        config = {
            "memory_store_type": "chromadb",
            "memory_file_path": temp_dir,
            "vector_store_enabled": True,
            "chromadb_collection_name": "test_vectors",
        }
        memory_system = MemorySystemAdapter(config=config)
        assert memory_system.memory_store is not None
        assert memory_system.vector_store is not None
        assert isinstance(memory_system.vector_store, ChromaDBAdapter)
        assert memory_system.has_vector_store() is True

    @pytest.mark.fast
    def test_initialization_without_vector_store_succeeds(self, temp_dir):
        """Test that the memory system initializes correctly without vector store.

        ReqID: N/A"""
        config = {
            "memory_store_type": "chromadb",
            "memory_file_path": temp_dir,
            "vector_store_enabled": False,
        }
        memory_system = MemorySystemAdapter(config=config)
        assert memory_system.memory_store is not None
        assert memory_system.vector_store is None
        assert memory_system.has_vector_store() is False

    @pytest.mark.fast
    def test_memory_and_vector_store_integration_succeeds(self, memory_system):
        """Test that both memory store and vector store work together.

        ReqID: N/A"""
        memory_item = MemoryItem(
            id="test-item-1",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "memory"},
        )
        memory_store = memory_system.get_memory_store()
        item_id = memory_store.store(memory_item)
        vector = MemoryVector(
            id="test-vector-1",
            content="This is a test vector",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"test": "vector", "memory_item_id": item_id},
        )
        vector_store = memory_system.get_vector_store()
        vector_id = vector_store.store_vector(vector)
        retrieved_item = memory_store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == memory_item.id
        assert retrieved_item.content == memory_item.content
        retrieved_vector = vector_store.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector.id
        assert retrieved_vector.content == vector.content
        assert retrieved_vector.metadata["memory_item_id"] == item_id

    @pytest.mark.fast
    def test_context_manager_with_chromadb_succeeds(self, memory_system):
        """Test that the context manager works with ChromaDB.

        ReqID: N/A"""
        context_manager = memory_system.get_context_manager()
        context_manager.add_to_context("test_key", "test_value")
        context_manager.add_to_context("vector_data", {"embeddings": [0.1, 0.2, 0.3]})
        value = context_manager.get_from_context("test_key")
        assert value == "test_value"
        vector_data = context_manager.get_from_context("vector_data")
        assert vector_data["embeddings"] == [0.1, 0.2, 0.3]
        full_context = context_manager.get_full_context()
        assert "test_key" in full_context
        assert "vector_data" in full_context
        context_manager.clear_context()
        assert context_manager.get_from_context("test_key") is None
