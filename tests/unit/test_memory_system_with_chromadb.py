
"""
Unit tests for the MemorySystemAdapter with ChromaDB integration.
"""
import pytest
import os
import json
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.adapters.memory.chroma_db_adapter import ChromaDBAdapter
from devsynth.exceptions import MemoryStoreError

pytestmark = pytest.mark.requires_resource("chromadb")


class TestMemorySystemWithChromaDB:
    """Test the MemorySystemAdapter with ChromaDB integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after the test
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_system(self, temp_dir):
        """Create a MemorySystemAdapter instance with ChromaDB for testing."""
        config = {
            "memory_store_type": "chromadb",
            "memory_file_path": temp_dir,
            "vector_store_enabled": True,
            "chromadb_collection_name": "test_vectors"
        }
        return MemorySystemAdapter(config=config)
    
    def test_initialization_with_chromadb(self, temp_dir):
        """Test that the memory system initializes correctly with ChromaDB."""
        config = {
            "memory_store_type": "chromadb",
            "memory_file_path": temp_dir,
            "vector_store_enabled": True,
            "chromadb_collection_name": "test_vectors"
        }
        memory_system = MemorySystemAdapter(config=config)
        
        # Check that the memory store is a ChromaDBStore
        assert memory_system.memory_store is not None
        
        # Check that the vector store is a ChromaDBAdapter
        assert memory_system.vector_store is not None
        assert isinstance(memory_system.vector_store, ChromaDBAdapter)
        assert memory_system.has_vector_store() is True
    
    def test_initialization_without_vector_store(self, temp_dir):
        """Test that the memory system initializes correctly without vector store."""
        config = {
            "memory_store_type": "chromadb",
            "memory_file_path": temp_dir,
            "vector_store_enabled": False
        }
        memory_system = MemorySystemAdapter(config=config)
        
        # Check that the memory store is a ChromaDBStore
        assert memory_system.memory_store is not None
        
        # Check that the vector store is None
        assert memory_system.vector_store is None
        assert memory_system.has_vector_store() is False
    
    def test_memory_and_vector_store_integration(self, memory_system):
        """Test that both memory store and vector store work together."""
        # Create a memory item
        memory_item = MemoryItem(
            id="test-item-1",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "memory"}
        )
        
        # Store the memory item
        memory_store = memory_system.get_memory_store()
        item_id = memory_store.store(memory_item)
        
        # Create a vector
        vector = MemoryVector(
            id="test-vector-1",
            content="This is a test vector",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"test": "vector", "memory_item_id": item_id}
        )
        
        # Store the vector
        vector_store = memory_system.get_vector_store()
        vector_id = vector_store.store_vector(vector)
        
        # Retrieve the memory item
        retrieved_item = memory_store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == memory_item.id
        assert retrieved_item.content == memory_item.content
        
        # Retrieve the vector
        retrieved_vector = vector_store.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector.id
        assert retrieved_vector.content == vector.content
        assert retrieved_vector.metadata["memory_item_id"] == item_id
    
    def test_context_manager_with_chromadb(self, memory_system):
        """Test that the context manager works with ChromaDB."""
        # Add items to the context
        context_manager = memory_system.get_context_manager()
        context_manager.add_to_context("test_key", "test_value")
        context_manager.add_to_context("vector_data", {"embeddings": [0.1, 0.2, 0.3]})
        
        # Retrieve items from the context
        value = context_manager.get_from_context("test_key")
        assert value == "test_value"
        
        vector_data = context_manager.get_from_context("vector_data")
        assert vector_data["embeddings"] == [0.1, 0.2, 0.3]
        
        # Get the full context
        full_context = context_manager.get_full_context()
        assert "test_key" in full_context
        assert "vector_data" in full_context
        
        # Clear the context
        context_manager.clear_context()
        assert context_manager.get_from_context("test_key") is None
