"""
Step Definitions for Multi-Layered Memory System and Tiered Cache Strategy BDD Tests

This file implements the step definitions for the multi-layered memory system
and tiered cache strategy feature file, testing the memory organization and
caching capabilities.
"""

import time
from typing import Any, Dict, List, Optional

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file


scenarios(feature_path(__file__, "general", "multi_layered_memory_system.feature"))

from devsynth.application.memory.multi_layered_memory import MultiLayeredMemorySystem
from devsynth.application.memory.tiered_cache import TieredCache

# Import the modules needed for the steps
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""

    class Context:
        def __init__(self):
            self.memory_system = None
            self.stored_items = {}
            self.retrieved_items = {}
            self.query_results = []
            self.access_times = {}
            self.cache_hits = {}
            self.cache_misses = {}
            self.layer_contents = {"short-term": [], "episodic": [], "semantic": []}

    return Context()


# Background steps


@given("the DevSynth system is initialized")
def devsynth_system_initialized(context):
    """Initialize the DevSynth system."""
    assert context is not None


@given("the multi-layered memory system is configured")
def multi_layered_memory_system_configured(context):
    """Configure the multi-layered memory system."""
    # Initialize the multi-layered memory system
    context.memory_system = MultiLayeredMemorySystem()
    assert context.memory_system is not None


# Scenario: Multi-layered memory system categorization


@when(
    parsers.parse(
        'I store information with content "{content}" and type "{memory_type}" in the memory system'
    )
)
def store_information_in_memory_system(context, content, memory_type):
    """Store information in the memory system."""
    # Create a memory item
    memory_item = MemoryItem(
        id="",
        content=content,
        memory_type=getattr(MemoryType, memory_type),
        metadata={},
    )

    # Store the memory item
    item_id = context.memory_system.store(memory_item)

    # Save the item ID for later retrieval
    context.stored_items[content] = item_id


@then(parsers.parse("it should be categorized into the {layer} memory layer"))
def check_memory_layer_categorization(context, layer):
    """Check that the information is categorized into the specified memory layer."""
    # Get the content from the previous step
    content = None
    if layer == "short-term":
        content = "Current task context"
    elif layer == "episodic":
        content = "Previous task execution"
    elif layer == "semantic":
        content = "Python language reference"

    assert content is not None, f"Unknown layer: {layer}"

    # Get the item ID
    item_id = context.stored_items[content]

    # Check that the item is in the specified layer
    items_in_layer = context.memory_system.get_items_by_layer(layer)

    # Find the item in the layer
    found = False
    for item in items_in_layer:
        if item.id == item_id:
            found = True
            break

    assert found, f"Item with content '{content}' not found in {layer} memory layer"


# Scenario: Short-term memory contains immediate context


@then("the short-term memory layer should contain these items")
def check_short_term_memory_contents(context):
    """Check that the short-term memory layer contains the expected items."""
    # Get the items from the short-term memory layer
    items = context.memory_system.get_items_by_layer("short-term")

    # Check that the items are in the layer
    for content in ["Current user request", "Current conversation state"]:
        item_id = context.stored_items[content]
        found = False
        for item in items:
            if item.id == item_id:
                found = True
                context.layer_contents["short-term"].append(item)
                break
        assert (
            found
        ), f"Item with content '{content}' not found in short-term memory layer"


@then("I should be able to retrieve all items from the short-term memory layer")
def retrieve_items_from_short_term_memory(context):
    """Retrieve all items from the short-term memory layer."""
    # Get the items from the short-term memory layer
    items = context.memory_system.get_items_by_layer("short-term")

    # Check that all expected items are retrieved
    assert len(items) == len(context.layer_contents["short-term"])

    # Check that the retrieved items match the expected items
    for expected_item in context.layer_contents["short-term"]:
        found = False
        for retrieved_item in items:
            if retrieved_item.id == expected_item.id:
                found = True
                break
        assert (
            found
        ), f"Item with ID '{expected_item.id}' not retrieved from short-term memory layer"


# Scenario: Episodic memory contains past events


@then("the episodic memory layer should contain these items")
def check_episodic_memory_contents(context):
    """Check that the episodic memory layer contains the expected items."""
    # Get the items from the episodic memory layer
    items = context.memory_system.get_items_by_layer("episodic")

    # Check that the items are in the layer
    for content in ["Task execution at 2023-06-01", "Error encountered at 2023-06-02"]:
        item_id = context.stored_items[content]
        found = False
        for item in items:
            if item.id == item_id:
                found = True
                context.layer_contents["episodic"].append(item)
                break
        assert (
            found
        ), f"Item with content '{content}' not found in episodic memory layer"


@then("I should be able to retrieve all items from the episodic memory layer")
def retrieve_items_from_episodic_memory(context):
    """Retrieve all items from the episodic memory layer."""
    # Get the items from the episodic memory layer
    items = context.memory_system.get_items_by_layer("episodic")

    # Check that all expected items are retrieved
    assert len(items) == len(context.layer_contents["episodic"])

    # Check that the retrieved items match the expected items
    for expected_item in context.layer_contents["episodic"]:
        found = False
        for retrieved_item in items:
            if retrieved_item.id == expected_item.id:
                found = True
                break
        assert (
            found
        ), f"Item with ID '{expected_item.id}' not retrieved from episodic memory layer"


# Scenario: Semantic memory contains general knowledge


@then("the semantic memory layer should contain these items")
def check_semantic_memory_contents(context):
    """Check that the semantic memory layer contains the expected items."""
    # Get the items from the semantic memory layer
    items = context.memory_system.get_items_by_layer("semantic")

    # Check that the items are in the layer
    for content in ["Python dictionary usage", "Git workflow best practices"]:
        item_id = context.stored_items[content]
        found = False
        for item in items:
            if item.id == item_id:
                found = True
                context.layer_contents["semantic"].append(item)
                break
        assert (
            found
        ), f"Item with content '{content}' not found in semantic memory layer"


@then("I should be able to retrieve all items from the semantic memory layer")
def retrieve_items_from_semantic_memory(context):
    """Retrieve all items from the semantic memory layer."""
    # Get the items from the semantic memory layer
    items = context.memory_system.get_items_by_layer("semantic")

    # Check that all expected items are retrieved
    assert len(items) == len(context.layer_contents["semantic"])

    # Check that the retrieved items match the expected items
    for expected_item in context.layer_contents["semantic"]:
        found = False
        for retrieved_item in items:
            if retrieved_item.id == expected_item.id:
                found = True
                break
        assert (
            found
        ), f"Item with ID '{expected_item.id}' not retrieved from semantic memory layer"


# Scenario: Cross-layer memory querying


@given("I have stored items in all memory layers")
def store_items_in_all_memory_layers(context):
    """Store items in all memory layers."""
    # Store items in the short-term memory layer
    for content in ["Short-term item 1", "Short-term item 2"]:
        memory_item = MemoryItem(
            id="", content=content, memory_type=MemoryType.CONTEXT, metadata={}
        )
        item_id = context.memory_system.store(memory_item)
        context.stored_items[content] = item_id

    # Store items in the episodic memory layer
    for content in ["Episodic item 1", "Episodic item 2"]:
        memory_item = MemoryItem(
            id="", content=content, memory_type=MemoryType.TASK_HISTORY, metadata={}
        )
        item_id = context.memory_system.store(memory_item)
        context.stored_items[content] = item_id

    # Store items in the semantic memory layer
    for content in ["Semantic item 1", "Semantic item 2"]:
        memory_item = MemoryItem(
            id="", content=content, memory_type=MemoryType.KNOWLEDGE, metadata={}
        )
        item_id = context.memory_system.store(memory_item)
        context.stored_items[content] = item_id


@when("I query the memory system without specifying a layer")
def query_memory_system_without_layer(context):
    """Query the memory system without specifying a layer."""
    # Query the memory system
    context.query_results = context.memory_system.query({})


@then("I should receive results from all memory layers")
def check_results_from_all_layers(context):
    """Check that the query results include items from all memory layers."""
    # Check that the query results include items from all layers
    short_term_found = False
    episodic_found = False
    semantic_found = False

    for item in context.query_results:
        if item.memory_type == MemoryType.CONTEXT:
            short_term_found = True
        elif item.memory_type == MemoryType.TASK_HISTORY:
            episodic_found = True
        elif item.memory_type == MemoryType.KNOWLEDGE:
            semantic_found = True

    assert (
        short_term_found
    ), "No items from short-term memory layer found in query results"
    assert episodic_found, "No items from episodic memory layer found in query results"
    assert semantic_found, "No items from semantic memory layer found in query results"


@when(parsers.parse('I query the memory system specifying the "{layer}" layer'))
def query_memory_system_with_layer(context, layer):
    """Query the memory system specifying a layer."""
    # Query the memory system
    context.query_results = context.memory_system.query({"layer": layer})


@then(parsers.parse("I should only receive results from the {layer} memory layer"))
def check_results_from_specific_layer(context, layer):
    """Check that the query results only include items from the specified layer."""
    # Check that the query results only include items from the specified layer
    for item in context.query_results:
        if layer == "short-term":
            assert (
                item.memory_type == MemoryType.CONTEXT
            ), f"Item with type {item.memory_type} found in short-term query results"
        elif layer == "episodic":
            assert (
                item.memory_type == MemoryType.TASK_HISTORY
            ), f"Item with type {item.memory_type} found in episodic query results"
        elif layer == "semantic":
            assert (
                item.memory_type == MemoryType.KNOWLEDGE
            ), f"Item with type {item.memory_type} found in semantic query results"


# Scenario: Tiered cache strategy with in-memory cache


@given("the tiered cache strategy is enabled")
def tiered_cache_strategy_enabled(context):
    """Enable the tiered cache strategy."""
    # Enable the tiered cache strategy
    context.memory_system.enable_tiered_cache()
    assert context.memory_system.is_tiered_cache_enabled()


@when("I access an item from the memory system for the first time")
def access_item_first_time(context):
    """Access an item from the memory system for the first time."""
    # Store a new item
    memory_item = MemoryItem(
        id="", content="Cached item", memory_type=MemoryType.CONTEXT, metadata={}
    )
    item_id = context.memory_system.store(memory_item)
    context.stored_items["Cached item"] = item_id

    # Record the start time
    start_time = time.time()

    # Access the item
    retrieved_item = context.memory_system.retrieve(item_id)

    # Record the end time
    end_time = time.time()

    # Calculate the access time
    access_time = end_time - start_time

    # Save the access time
    context.access_times["first_access"] = access_time

    # Save the retrieved item
    context.retrieved_items["Cached item"] = retrieved_item

    # Check that the item was retrieved from the underlying storage
    assert context.memory_system.get_cache_stats()["misses"] > 0


@then("it should be retrieved from the underlying storage")
def check_retrieved_from_storage(context):
    """Check that the item was retrieved from the underlying storage."""
    # Check that the item was retrieved from the underlying storage
    assert context.memory_system.get_cache_stats()["misses"] > 0


@when("I access the same item again")
def access_item_again(context):
    """Access the same item again."""
    # Get the item ID
    item_id = context.stored_items["Cached item"]

    # Record the start time
    start_time = time.time()

    # Access the item
    retrieved_item = context.memory_system.retrieve(item_id)

    # Record the end time
    end_time = time.time()

    # Calculate the access time
    access_time = end_time - start_time

    # Save the access time
    context.access_times["second_access"] = access_time

    # Save the retrieved item
    context.retrieved_items["Cached item again"] = retrieved_item

    # Check that the item was retrieved from the cache
    assert context.memory_system.get_cache_stats()["hits"] > 0


@then("it should be retrieved from the in-memory cache")
def check_retrieved_from_cache(context):
    """Check that the item was retrieved from the in-memory cache."""
    # Check that the item was retrieved from the cache
    assert context.memory_system.get_cache_stats()["hits"] > 0


@then("accessing the cached item should be faster than the first access")
def check_cached_access_faster(context):
    """Check that accessing the cached item is faster than the first access."""
    # Check that the second access was faster than the first access
    assert context.access_times["second_access"] < context.access_times["first_access"]


# Scenario: Cache update based on access patterns


@given("the tiered cache strategy is enabled with a limited cache size")
def tiered_cache_strategy_enabled_with_limited_size(context):
    """Enable the tiered cache strategy with a limited cache size."""
    # Enable the tiered cache strategy with a limited cache size
    context.memory_system.enable_tiered_cache(max_size=2)
    assert context.memory_system.is_tiered_cache_enabled()
    assert context.memory_system.get_cache_max_size() == 2


@when("I access multiple items from the memory system")
def access_multiple_items(context):
    """Access multiple items from the memory system."""
    # Store and access multiple items
    for i in range(1, 3):
        content = f"Limited cache item {i}"
        memory_item = MemoryItem(
            id="", content=content, memory_type=MemoryType.CONTEXT, metadata={}
        )
        item_id = context.memory_system.store(memory_item)
        context.stored_items[content] = item_id

        # Access the item to put it in the cache
        retrieved_item = context.memory_system.retrieve(item_id)
        context.retrieved_items[content] = retrieved_item


@when("the cache reaches its capacity")
def cache_reaches_capacity(context):
    """Check that the cache has reached its capacity."""
    # Check that the cache has reached its capacity
    assert context.memory_system.get_cache_size() == 2


@when("I access a new item")
def access_new_item(context):
    """Access a new item from the memory system."""
    # Store and access a new item
    content = "New limited cache item"
    memory_item = MemoryItem(
        id="", content=content, memory_type=MemoryType.CONTEXT, metadata={}
    )
    item_id = context.memory_system.store(memory_item)
    context.stored_items[content] = item_id

    # Access the item to put it in the cache
    retrieved_item = context.memory_system.retrieve(item_id)
    context.retrieved_items[content] = retrieved_item


@then("the least recently used item should be removed from the cache")
def check_lru_item_removed(context):
    """Check that the least recently used item has been removed from the cache."""
    # Check that the cache size is still at its maximum
    assert context.memory_system.get_cache_size() == 2

    # Check that the first item is no longer in the cache
    item_id = context.stored_items["Limited cache item 1"]

    # Directly check if the item is in the cache using the cache's contains method
    assert not context.memory_system.cache.contains(
        item_id
    ), "The least recently used item is still in the cache"

    # Access the item to verify it can still be retrieved from the memory layer
    retrieved_item = context.memory_system.retrieve(item_id)
    assert (
        retrieved_item is not None
    ), "The item should still be retrievable from the memory layer"

    # After retrieval, the item should now be in the cache again
    assert context.memory_system.cache.contains(
        item_id
    ), "The item should be in the cache after retrieval"


@then("the new item should be added to the cache")
def check_new_item_added_to_cache(context):
    """Check that the new item has been added to the cache."""
    # Check that the new item is in the cache
    item_id = context.stored_items["New limited cache item"]

    # Directly check if the item is in the cache using the cache's contains method
    assert context.memory_system.cache.contains(
        item_id
    ), "The new item is not in the cache"

    # Access the item to verify it can be retrieved from the cache
    retrieved_item = context.memory_system.retrieve(item_id)
    assert retrieved_item is not None, "The item should be retrievable from the cache"

    # The item should still be in the cache after retrieval
    assert context.memory_system.cache.contains(
        item_id
    ), "The item should still be in the cache after retrieval"
