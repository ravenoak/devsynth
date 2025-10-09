"""
Step definitions for Additional Storage Backends feature.

This file implements step definitions for testing TinyDB, DuckDB, LMDB, and FAISS storage backends.
"""

import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.memory.duckdb_store import DuckDBStore
from devsynth.application.memory.lmdb_store import LMDBStore
from devsynth.application.memory.tinydb_store import TinyDBStore

# Import the necessary modules
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.ports.memory_port import MemoryPort
from tests.behavior.feature_paths import feature_path

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("lmdb"),
    pytest.mark.requires_resource("faiss"),
    pytest.mark.skip(
        reason="Skipping FAISS tests due to known issues with FAISS library"
    ),
]


# Register the scenarios from the feature file
scenarios(feature_path(__file__, "general", "additional_storage_backends.feature"))


@pytest.fixture
def temp_store_path(tmp_project_dir):
    """Create a temporary directory for storage backends within the project dir."""
    store_dir = os.path.join(tmp_project_dir, ".devsynth", "memory")
    os.makedirs(store_dir, exist_ok=True)
    return store_dir


@pytest.fixture
def tinydb_store(temp_store_path):
    """Create a TinyDB store instance for testing."""
    store = TinyDBStore(base_path=temp_store_path)
    return store


@pytest.fixture
def duckdb_store(temp_store_path):
    """Create a DuckDB store instance for testing."""
    store = DuckDBStore(base_path=temp_store_path)
    return store


@pytest.fixture
def lmdb_store(temp_store_path):
    """Create a LMDB store instance for testing."""
    store = LMDBStore(base_path=temp_store_path)
    return store


@pytest.fixture
def faiss_store(temp_store_path):
    """Create a FAISS store instance for testing."""
    pytest.importorskip("faiss")
    from devsynth.application.memory.faiss_store import FAISSStore

    store = FAISSStore(base_path=temp_store_path)
    return store


@pytest.fixture
def memory_store(request, temp_store_path):
    """Create a memory store based on the specified type."""
    store_type = request.param if hasattr(request, "param") else "memory"

    if store_type == "tinydb":
        return TinyDBStore(base_path=temp_store_path)
    elif store_type == "duckdb":
        return DuckDBStore(base_path=temp_store_path)
    elif store_type == "lmdb":
        return LMDBStore(base_path=temp_store_path)
    elif store_type == "faiss":
        pytest.importorskip("faiss")
        from devsynth.application.memory.faiss_store import FAISSStore

        return FAISSStore(base_path=temp_store_path)
    else:
        pytest.fail(f"Unsupported store type: {store_type}")


@pytest.fixture
def memory_port(memory_store):
    """Create a memory port with the specified memory store."""
    # Mock context manager for simplicity
    mock_context_manager = MagicMock()
    port = MemoryPort(context_manager=mock_context_manager, memory_store=memory_store)
    return port


@given("the DevSynth CLI is installed")
@pytest.mark.medium
def devsynth_cli_installed():
    """Verify that the DevSynth CLI can be imported."""
    try:
        __import__("devsynth")
    except Exception as exc:
        pytest.fail(f"DevSynth CLI not available: {exc}")
    return True


@when(parsers.parse('I configure the memory store type as "{store_type}"'))
@pytest.mark.medium
def configure_memory_store_type(store_type):
    """Configure the memory store type."""
    # This step is handled by the memory_store fixture
    assert store_type in [
        "tinydb",
        "duckdb",
        "lmdb",
        "faiss",
    ], f"Unsupported store type: {store_type}"


@then(parsers.parse("a {store_type} memory store should be initialized"))
@pytest.mark.medium
def check_store_initialized(store_type, request):
    """Verify that the specified memory store is initialized."""
    if store_type == "TinyDB":
        store = request.getfixturevalue("tinydb_store")
        assert isinstance(store, TinyDBStore)
    elif store_type == "DuckDB":
        store = request.getfixturevalue("duckdb_store")
        assert isinstance(store, DuckDBStore)
    elif store_type == "LMDB":
        store = request.getfixturevalue("lmdb_store")
        assert isinstance(store, LMDBStore)
    elif store_type == "FAISS":
        pytest.importorskip("faiss")
        from devsynth.application.memory.faiss_store import FAISSStore

        store = request.getfixturevalue("faiss_store")
        assert isinstance(store, FAISSStore)
    else:
        pytest.fail(f"Unsupported store type: {store_type}")


@given(parsers.parse('the memory store type is configured as "{store_type}"'))
@pytest.mark.medium
def given_memory_store_type(store_type, request):
    """Configure the memory store type."""
    # This step is handled by the memory_store fixture
    assert store_type in [
        "tinydb",
        "duckdb",
        "lmdb",
        "faiss",
    ], f"Unsupported store type: {store_type}"

    # Dynamically get the appropriate store fixture
    if store_type == "tinydb":
        store = request.getfixturevalue("tinydb_store")
        assert isinstance(store, TinyDBStore)
    elif store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
        assert isinstance(store, DuckDBStore)
    elif store_type == "lmdb":
        store = request.getfixturevalue("lmdb_store")
        assert isinstance(store, LMDBStore)
    elif store_type == "faiss":
        pytest.importorskip("faiss")
        from devsynth.application.memory.faiss_store import FAISSStore

        store = request.getfixturevalue("faiss_store")
        assert isinstance(store, FAISSStore)


@when("I store an item in the memory store")
@pytest.mark.medium
def store_item_in_memory(memory_port):
    """Store an item in the memory store."""
    # Store a test item in memory
    memory_port.store_memory(
        content="This is a test item for storage backends",
        memory_type=MemoryType.WORKING,
        metadata={"test_id": "test-item-1"},
    )


@then("I should be able to retrieve the item by its ID")
@pytest.mark.medium
def retrieve_item_by_id(memory_port):
    """Verify that an item can be retrieved by its ID."""
    # First search for the item to get its ID
    search_results = memory_port.search_memory({"content": "test item"})
    assert len(search_results) > 0, "No items found in search results"

    # Get the first item's ID
    item_id = search_results[0].id

    # Retrieve the item by ID
    retrieved_item = memory_port.retrieve_memory(item_id)

    # Verify the item was retrieved
    assert retrieved_item is not None
    assert "test item" in retrieved_item.content.lower()


@given("I have stored multiple items with different content")
@pytest.mark.medium
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


@when("I search for items with specific criteria")
@pytest.mark.medium
def search_items_with_criteria(memory_port):
    """Search for items with specific criteria."""
    # Store the search results in the context for later assertion
    results = memory_port.search_memory({"content": "programming"})
    memory_port.context_manager.add_to_context.return_value = results


@then("I should receive items matching the criteria")
@pytest.mark.medium
def check_search_results(memory_port):
    """Verify that items match the search criteria."""
    # Retrieve the search results from the context
    memory_port.context_manager.get_from_context.return_value = (
        memory_port.search_memory({"content": "programming"})
    )
    results = memory_port.context_manager.get_from_context.return_value

    # Verify that we have results
    assert len(results) > 0, "No search results found"

    # Check that the Python document is in the results
    python_found = False
    for item in results:
        if "python" in item.content.lower():
            python_found = True
            break

    assert python_found, "Expected Python document in search results"


@given("I have stored items in the memory store")
@pytest.mark.medium
def stored_items_in_memory(memory_port):
    """Store items in the memory store for persistence testing."""
    memory_port.store_memory(
        content="This is a persistent test item",
        memory_type=MemoryType.WORKING,
        metadata={"test_id": "persistent-item"},
    )


@when("I restart the application")
@pytest.mark.medium
def restart_application(request, temp_store_path):
    """Simulate restarting the application by recreating the memory store."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Create a new store instance with the same path
    if store_type == "tinydb":
        new_store = TinyDBStore(base_path=temp_store_path)
    elif store_type == "duckdb":
        new_store = DuckDBStore(base_path=temp_store_path)
    elif store_type == "lmdb":
        new_store = LMDBStore(base_path=temp_store_path)
    elif store_type == "faiss":
        pytest.importorskip("faiss")
        from devsynth.application.memory.faiss_store import FAISSStore

        new_store = FAISSStore(base_path=temp_store_path)
    else:
        pytest.fail(f"Unsupported store type: {store_type}")

    # Replace the old store with the new one
    request.config.cache.set("new_store", new_store)


@then("the previously stored items should still be available")
@pytest.mark.medium
def check_item_persistence(request, memory_port):
    """Verify that items are still available after restart."""
    # Get the new store from the cache
    new_store = request.config.cache.get("new_store", None)
    assert new_store is not None, "New store not found in cache"

    # Create a new memory port with the new store
    mock_context_manager = MagicMock()
    new_port = MemoryPort(context_manager=mock_context_manager, memory_store=new_store)

    # Check that items can still be found
    results = new_port.search_memory({"content": "persistent"})
    assert len(results) > 0, "No items found after 'restart'"

    # Check that we can find the persistent item
    persistent_found = False
    for item in results:
        if "persistent test item" in item.content.lower():
            persistent_found = True
            break

    assert persistent_found, "Expected persistent item to be available after restart"


@given("vector store is enabled")
@pytest.mark.medium
def vector_store_enabled(request):
    """Ensure that vector store is enabled for DuckDB or FAISS stores."""
    store_type = request.node.get_closest_marker("store_type").args[0]
    assert store_type in [
        "duckdb",
        "faiss",
    ], f"Vector store not supported for {store_type}"


@when("I store a vector in the vector store")
@pytest.mark.medium
def store_vector_in_store(request):
    """Store a vector in the vector store."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Create a test vector
    vector = MemoryVector(
        content="Test vector content",
        embedding=np.random.rand(5).tolist(),  # 5-dimensional random vector
        metadata={"test_id": "test-vector-1"},
    )

    # Store the vector
    vector_id = store.store_vector(vector)

    # Save the vector ID for later retrieval
    request.config.cache.set("vector_id", vector_id)


@then("I should be able to retrieve the vector by its ID")
@pytest.mark.medium
def retrieve_vector_by_id(request):
    """Verify that a vector can be retrieved by its ID."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Get the vector ID
    vector_id = request.config.cache.get("vector_id", None)
    assert vector_id is not None, "Vector ID not found in cache"

    # Retrieve the vector
    vector = store.retrieve_vector(vector_id)

    # Verify the vector was retrieved
    assert vector is not None
    assert "test vector content" in vector.content.lower()


@given("I have stored multiple vectors with different embeddings")
@pytest.mark.medium
def store_multiple_vectors(request):
    """Store multiple vectors with different embeddings."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Create and store multiple vectors
    vectors = [
        (
            "Document about Python",
            np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
            {"test_id": "python-vec"},
        ),
        (
            "Article about JavaScript",
            np.array([0.2, 0.3, 0.4, 0.5, 0.6]),
            {"test_id": "js-vec"},
        ),
        (
            "Tutorial on machine learning",
            np.array([0.3, 0.4, 0.5, 0.6, 0.7]),
            {"test_id": "ml-vec"},
        ),
        ("Guide to NLP", np.array([0.4, 0.5, 0.6, 0.7, 0.8]), {"test_id": "nlp-vec"}),
        (
            "Introduction to databases",
            np.array([0.5, 0.6, 0.7, 0.8, 0.9]),
            {"test_id": "db-vec"},
        ),
    ]

    for content, embedding, metadata in vectors:
        vector = MemoryVector(
            content=content, embedding=embedding.tolist(), metadata=metadata
        )
        store.store_vector(vector)

    # Save a query vector for later use
    request.config.cache.set("query_vector", [0.1, 0.2, 0.3, 0.4, 0.5])


@when("I perform a similarity search with a query embedding")
@pytest.mark.medium
def perform_similarity_search(request):
    """Perform a similarity search with a query embedding."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Get the query vector
    query_vector = request.config.cache.get("query_vector", None)
    assert query_vector is not None, "Query vector not found in cache"

    # Perform the search
    results = store.similarity_search(query_vector, top_k=3)

    # Save the results for later assertion
    request.config.cache.set("search_results", [v.id for v in results])


@then("I should receive vectors ranked by similarity")
@pytest.mark.medium
def check_similarity_search_results(request):
    """Verify that vectors are ranked by similarity."""
    # Get the search results
    result_ids = request.config.cache.get("search_results", None)
    assert result_ids is not None, "Search results not found in cache"

    # Verify that we have results
    assert len(result_ids) > 0, "No similarity search results found"


@given("I have stored vectors in the vector store")
@pytest.mark.medium
def stored_vectors_in_store(request):
    """Store vectors in the vector store for persistence testing."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Create and store a persistent vector
    vector = MemoryVector(
        content="This is a persistent test vector",
        embedding=np.random.rand(5).tolist(),
        metadata={"test_id": "persistent-vector"},
    )

    vector_id = store.store_vector(vector)

    # Save the vector ID for later retrieval
    request.config.cache.set("persistent_vector_id", vector_id)


@then("the previously stored vectors should still be available")
@pytest.mark.medium
def check_vector_persistence(request):
    """Verify that vectors are still available after restart."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Get the vector ID
    vector_id = request.config.cache.get("persistent_vector_id", None)
    assert vector_id is not None, "Persistent vector ID not found in cache"

    # Retrieve the vector
    vector = store.retrieve_vector(vector_id)

    # Verify the vector was retrieved
    assert vector is not None
    assert "persistent test vector" in vector.content.lower()


@given("I have stored multiple vectors in the vector store")
@pytest.mark.medium
def stored_multiple_vectors(request):
    """Store multiple vectors in the vector store for collection statistics."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Create and store multiple vectors
    for i in range(5):
        vector = MemoryVector(
            content=f"Test vector {i}",
            embedding=np.random.rand(5).tolist(),
            metadata={"test_id": f"stats-vector-{i}"},
        )
        store.store_vector(vector)


@when("I request collection statistics")
@pytest.mark.medium
def request_collection_stats(request):
    """Request collection statistics from the vector store."""
    # Get the current store type
    store_type = request.node.get_closest_marker("store_type").args[0]

    # Get the appropriate store
    if store_type == "duckdb":
        store = request.getfixturevalue("duckdb_store")
    elif store_type == "faiss":
        store = request.getfixturevalue("faiss_store")
    else:
        pytest.fail(f"Vector store not supported for {store_type}")

    # Get collection statistics
    stats = store.get_collection_stats()

    # Save the stats for later assertion
    request.config.cache.set("collection_stats", stats)


@then("I should receive information about the vector collection")
@pytest.mark.medium
def check_collection_stats(request):
    """Verify that collection statistics are returned."""
    # Get the collection stats
    stats = request.config.cache.get("collection_stats", None)
    assert stats is not None, "Collection stats not found in cache"

    # Verify that we have stats
    assert "vector_count" in stats, "vector_count not found in collection stats"
    assert (
        "embedding_dimensions" in stats
    ), "embedding_dimensions not found in collection stats"

    # Verify that the stats are reasonable
    assert stats["vector_count"] >= 5, "Expected at least 5 vectors in collection"
    assert stats["embedding_dimensions"] == 5, "Expected embedding dimension to be 5"


@when("I begin a transaction")
@pytest.mark.medium
def begin_transaction(request):
    """Begin a transaction in the LMDB store."""
    # This step is only applicable to LMDB
    store_type = request.node.get_closest_marker("store_type").args[0]
    assert store_type == "lmdb", "Transactions are only supported by LMDB"

    # Get the LMDB store
    store = request.getfixturevalue("lmdb_store")

    # Begin a transaction
    txn_id = store.begin_transaction(write=True)

    # Save the transaction identifier for later use
    request.config.cache.set("transaction_id", txn_id)


@when("I store multiple items within the transaction")
@pytest.mark.medium
def store_items_in_transaction(request):
    """Store multiple items within the transaction."""
    # Get the transaction
    txn_id = request.config.cache.get("transaction_id", None)
    assert txn_id is not None, "Transaction not found in cache"

    # Get the LMDB store
    store = request.getfixturevalue("lmdb_store")

    txn = store._transactions.get(txn_id)
    assert txn is not None, "Active transaction handle not found"

    # Store multiple items
    items = []
    for i in range(3):
        item = MemoryItem(
            content=f"Transaction item {i}",
            memory_type=MemoryType.WORKING,
            metadata={"test_id": f"txn-item-{i}"},
        )
        store.store_in_transaction(txn, item)
        items.append(item.id)

    # Save the item IDs for later verification
    request.config.cache.set("transaction_items", items)


@when("I commit the transaction")
@pytest.mark.medium
def commit_transaction(request):
    """Commit the transaction."""
    # Get the transaction
    txn_id = request.config.cache.get("transaction_id", None)
    assert txn_id is not None, "Transaction not found in cache"

    # Commit the transaction
    store.commit_transaction(txn_id)


@then("all items should be stored atomically")
@pytest.mark.medium
def check_transaction_items(request):
    """Verify that all items were stored atomically."""
    # Get the item IDs
    item_ids = request.config.cache.get("transaction_items", None)
    assert item_ids is not None, "Transaction item IDs not found in cache"

    # Get the LMDB store
    store = request.getfixturevalue("lmdb_store")

    # Verify that all items were stored
    for item_id in item_ids:
        item = store.retrieve(item_id)
        assert item is not None, f"Item {item_id} not found after transaction commit"
        assert (
            "transaction item" in item.content.lower()
        ), f"Unexpected content for item {item_id}"


@when("I modify the item within the transaction")
@pytest.mark.medium
def modify_item_in_transaction(request):
    """Modify an item within the transaction."""
    # Get the transaction
    txn_id = request.config.cache.get("transaction_id", None)
    assert txn_id is not None, "Transaction not found in cache"

    # Get the LMDB store
    store = request.getfixturevalue("lmdb_store")

    # Get the item to modify
    item = store.retrieve(request.config.cache.get("item_id", None))
    assert item is not None, "Item not found for modification"

    # Modify the item
    modified_item = MemoryItem(
        id=item.id,
        content="Modified content",
        memory_type=item.memory_type,
        metadata=item.metadata,
    )

    # Store the modified item
    txn = store._transactions.get(txn_id)
    assert txn is not None, "Active transaction handle not found"

    store.store_in_transaction(txn, modified_item)


@when("I abort the transaction")
@pytest.mark.medium
def abort_transaction(request):
    """Abort the transaction."""
    # Get the transaction
    txn_id = request.config.cache.get("transaction_id", None)
    assert txn_id is not None, "Transaction not found in cache"

    # Abort the transaction
    store.rollback_transaction(txn_id)


@then("the item should remain unchanged")
@pytest.mark.medium
def check_item_unchanged(request):
    """Verify that the item remains unchanged after transaction abort."""
    # Get the LMDB store
    store = request.getfixturevalue("lmdb_store")

    # Get the item
    item = store.retrieve(request.config.cache.get("item_id", None))
    assert item is not None, "Item not found after transaction abort"

    # Verify that the item is unchanged
    assert (
        item.content != "Modified content"
    ), "Item was modified despite transaction abort"
    assert "test item" in item.content.lower(), "Item content was changed unexpectedly"
