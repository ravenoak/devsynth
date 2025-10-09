"""
Step definitions for ChromaDB Integration feature with provider system integration.
"""

import os
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, then, when

# Import the necessary modules
from devsynth.domain.models.memory import MemoryItem, MemoryType

pytestmark = pytest.mark.requires_resource("chromadb")


try:
    chromadb = pytest.importorskip("chromadb")
    from devsynth.adapters.chromadb_memory_store import ChromaDBMemoryStore
    from devsynth.adapters.provider_system import embed, get_provider
    from devsynth.ports.memory_port import MemoryPort

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    ChromaDBMemoryStore = None
    embed = None
    get_provider = None
    MemoryPort = None


@pytest.fixture
def temp_chromadb_path(tmp_project_dir):
    """Create a temporary directory for ChromaDB persistence within the project dir."""
    chroma_dir = os.path.join(tmp_project_dir, ".devsynth", "chromadb_store")
    os.makedirs(chroma_dir, exist_ok=True)
    return chroma_dir


@pytest.fixture
def memory_store(temp_chromadb_path, llm_provider):
    """
    Create a ChromaDB memory store instance that uses the provider system for embeddings.

    This fixture leverages the llm_provider fixture from conftest.py to ensure
    the memory store can use either OpenAI or LM Studio for embeddings.
    """
    store = ChromaDBMemoryStore(
        persist_directory=temp_chromadb_path, use_provider_system=True
    )
    return store


@pytest.fixture
def memory_port(memory_store):
    """Create a memory port with the ChromaDB memory store."""
    # Note: For simplicity, we're not implementing a full context manager
    # In a real implementation, you would inject a proper context manager
    mock_context_manager = MagicMock()
    port = MemoryPort(context_manager=mock_context_manager, memory_store=memory_store)
    return port


@when(parsers.parse('I configure the memory store type as "{store_type}"'))
def configure_memory_store_type(store_type):
    """Configure the memory store type."""
    # This step is now an assertion that we're using ChromaDB
    assert (
        store_type == "chromadb"
    ), "Only chromadb store type is supported in these tests"


@then("a ChromaDB memory store should be initialized")
def check_chromadb_initialized(memory_store):
    """Verify that a ChromaDB memory store is initialized."""
    assert isinstance(memory_store, ChromaDBMemoryStore)
    # Verify that the store is configured to use the provider system
    assert memory_store.use_provider_system is True


@given(parsers.parse('the memory store type is configured as "{store_type}"'))
def given_memory_store_type(store_type, memory_store):
    """Configure the memory store type."""
    assert (
        store_type == "chromadb"
    ), "Only chromadb store type is supported in these tests"
    assert isinstance(memory_store, ChromaDBMemoryStore)


@when("I store an item in the memory store")
def store_item_in_memory(memory_port):
    """Store an item in the memory store."""
    # Store a test item in memory
    memory_port.store_memory(
        content="This is a test item for semantic search",
        memory_type=MemoryType.WORKING,
        metadata={"test_id": "test-item-1"},
    )


@then("I should be able to retrieve the item by its ID")
def retrieve_item_by_id(memory_port):
    """Verify that an item can be retrieved by its ID."""
    # First search for the item to get its ID
    search_results = memory_port.search_memory({"query": "test item"})
    assert len(search_results) > 0, "No items found in search results"

    # Get the first item's ID
    item_id = search_results[0].id

    # Retrieve the item by ID
    retrieved_item = memory_port.retrieve_memory(item_id)

    # Verify the item was retrieved
    assert retrieved_item is not None
    assert "test item" in retrieved_item.content.lower()


@given("I have stored multiple items with different content")
def store_multiple_items(memory_port):
    """Store multiple items with different content."""
    items = [
        (
            "Document about Python programming language",
            MemoryType.WORKING,
            {"test_id": "python"},
        ),
        (
            "Article about JavaScript frameworks",
            MemoryType.WORKING,
            {"test_id": "javascript"},
        ),
        (
            "Tutorial on machine learning algorithms",
            MemoryType.WORKING,
            {"test_id": "ml"},
        ),
        (
            "Guide to natural language processing",
            MemoryType.WORKING,
            {"test_id": "nlp"},
        ),
        (
            "Introduction to database systems",
            MemoryType.WORKING,
            {"test_id": "database"},
        ),
    ]

    for content, memory_type, metadata in items:
        memory_port.store_memory(
            content=content, memory_type=memory_type, metadata=metadata
        )


@when(parsers.parse("I perform a semantic search for similar content"))
def perform_semantic_search(memory_port):
    """Perform a semantic search for similar content."""
    memory_port.context_manager.add_to_context.return_value = None
    memory_port.context_manager.get_from_context.return_value = None

    # Store the search results in the context for later assertion
    results = memory_port.search_memory({"query": "programming languages", "top_k": 3})
    memory_port.context_manager.add_to_context.assert_called_once()
    memory_port.context_manager.add_to_context.return_value = results


@then("I should receive items ranked by semantic similarity")
def check_semantic_search_results(memory_port):
    """Verify that items are ranked by semantic similarity."""
    # Retrieve the search results from the context
    memory_port.context_manager.get_from_context.return_value = (
        memory_port.search_memory({"query": "programming languages", "top_k": 3})
    )
    results = memory_port.context_manager.get_from_context.return_value

    # Verify that we have results
    assert len(results) > 0, "No search results found"

    # Check that the Python document is in the top results
    python_found = False
    for item in results:
        if "python" in item.content.lower():
            python_found = True
            break

    assert python_found, "Expected Python document in top results"


@when("I restart the application")
def restart_application(memory_store, temp_chromadb_path):
    """Simulate restarting the application by recreating the memory store."""
    # We're simulating a restart by creating a new instance with the same persistence directory
    new_store = ChromaDBMemoryStore(
        persist_directory=temp_chromadb_path, use_provider_system=True
    )

    # Store the new instance for later assertions
    memory_store.client = new_store.client
    memory_store.collection = new_store.collection


@then("the previously stored items should still be available")
def check_item_persistence(memory_port):
    """Verify that items are still available after restart."""
    # Check that items can still be found
    results = memory_port.search_memory({"query": "programming", "top_k": 5})
    assert len(results) > 0, "No items found after 'restart'"

    # Check that we can still find the Python document
    python_found = False
    for item in results:
        if "python" in item.content.lower():
            python_found = True
            break

    assert python_found, "Expected Python document to persist"
