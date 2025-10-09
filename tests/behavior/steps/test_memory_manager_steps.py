"""
Step Definitions for Memory Manager and Adapters BDD Tests

This file implements the step definitions for the Memory Manager and Adapters
feature file, which tests the functionality of the Memory Manager layer with
specialized adapters and memory tagging with EDRR phases.
"""

import ast
import json
from typing import Any, Dict, List, Optional

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file


scenarios(feature_path(__file__, "general", "memory_manager.feature"))

from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.interfaces.memory import MemoryStore, VectorStore

# Import the modules needed for the steps
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""

    class Context:
        def __init__(self):
            self.memory_manager = None
            self.graph_adapter = None
            self.vector_adapter = None
            self.tinydb_adapter = None
            self.memory_item_id = None
            self.retrieved_item = None
            self.search_results = None
            self.memory_items = {}
            self.related_items = {}

    return Context()


# Background steps


@given("the DevSynth system is initialized")
def devsynth_initialized(context):
    """Step: the DevSynth system is initialized."""
    assert context is not None


@given("the Memory Manager is configured with the following adapters")
def memory_manager_configured(context, table):
    """Step: the Memory Manager is configured with the following adapters."""
    # Create mock adapters for testing
    context.graph_adapter = GraphMemoryAdapter()
    context.vector_adapter = VectorMemoryAdapter()
    context.tinydb_adapter = TinyDBMemoryAdapter()

    # Configure adapters based on the table
    adapters = {}
    for row in table:
        adapter_type = row["adapter_type"]
        enabled = row["enabled"].lower() == "true"

        if adapter_type == "Graph" and enabled:
            adapters["graph"] = context.graph_adapter
        elif adapter_type == "Vector" and enabled:
            adapters["vector"] = context.vector_adapter
        elif adapter_type == "TinyDB" and enabled:
            adapters["tinydb"] = context.tinydb_adapter

    # Create the Memory Manager with the configured adapters
    context.memory_manager = MemoryManager(adapters=adapters)


# Scenario: Query memory using GraphMemoryAdapter


@given("I have stored the following memory items with relationships")
def store_memory_items_with_relationships(context, table):
    """Step: I have stored the following memory items with relationships."""
    # Store memory items
    for row in table:
        item_id = row["id"]
        content = row["content"]
        memory_type = MemoryType[row["type"]]
        related_to = row["related_to"]

        # Create and store the memory item
        memory_item = MemoryItem(
            id=item_id,
            content=content,
            memory_type=memory_type,
            metadata={"related_to": related_to} if related_to else {},
        )

        # Store in the graph adapter
        context.graph_adapter.store(memory_item)

        # Keep track of the item for later use
        context.memory_items[item_id] = memory_item

        # Add relationship if specified
        if related_to:
            if related_to not in context.related_items:
                context.related_items[related_to] = []
            context.related_items[related_to].append(item_id)

            if item_id not in context.related_items:
                context.related_items[item_id] = []
            context.related_items[item_id].append(related_to)


@when(parsers.parse('I query the graph for items related to "{item_id}"'))
def query_graph_for_related_items(context, item_id):
    """Step: I query the graph for items related to an item ID."""
    context.search_results = context.memory_manager.query_related_items(item_id)


@then("I should receive a list of related memory items")
def receive_related_memory_items(context):
    """Step: I should receive a list of related memory items."""
    assert context.search_results is not None
    assert isinstance(context.search_results, list)


@then(parsers.parse('the list should contain items with ids "{ids}"'))
def check_related_items_ids(context, ids):
    """Step: the list should contain items with specific IDs."""
    expected_ids = [id.strip() for id in ids.split("and")]
    actual_ids = [item.id for item in context.search_results]

    for expected_id in expected_ids:
        assert expected_id in actual_ids


# Scenario: Query memory using VectorMemoryAdapter


@given("I have stored the following memory items with embeddings")
def store_memory_items_with_embeddings(context, table):
    """Step: I have stored the following memory items with embeddings."""
    for row in table:
        content = row["content"]
        memory_type = MemoryType[row["type"]]
        embedding = ast.literal_eval(row["embedding"])

        # Create and store the memory vector
        memory_vector = MemoryVector(
            id="",
            content=content,
            embedding=embedding,
            metadata={"type": memory_type.value},
        )

        # Store in the vector adapter
        vector_id = context.vector_adapter.store_vector(memory_vector)

        # Keep track of the vector for later use
        context.memory_items[vector_id] = memory_vector


@when(parsers.parse("I perform a similarity search with embedding {embedding}"))
def perform_similarity_search(context, embedding):
    """Step: I perform a similarity search with a specific embedding."""
    query_embedding = ast.literal_eval(embedding)
    context.search_results = context.memory_manager.similarity_search(
        query_embedding, top_k=3
    )


@then("I should receive a list of similar memory items")
def receive_similar_memory_items(context):
    """Step: I should receive a list of similar memory items."""
    assert context.search_results is not None
    assert isinstance(context.search_results, list)


@then(parsers.parse('the first item should have content "{content}"'))
def check_first_item_content(context, content):
    """Step: the first item should have specific content."""
    assert context.search_results[0].content == content


@then(parsers.parse('the second item should have content "{content}"'))
def check_second_item_content(context, content):
    """Step: the second item should have specific content."""
    assert context.search_results[1].content == content


# Scenario: Query memory using TinyDBMemoryAdapter


@given("I have stored the following memory items with structured data")
def store_memory_items_with_structured_data(context, table):
    """Step: I have stored the following memory items with structured data."""
    for row in table:
        content = row["content"]
        memory_type = MemoryType[row["type"]]
        metadata = json.loads(row["metadata"])

        # Create and store the memory item
        memory_item = MemoryItem(
            id="", content=content, memory_type=memory_type, metadata=metadata
        )

        # Store in the TinyDB adapter
        item_id = context.tinydb_adapter.store(memory_item)

        # Keep track of the item for later use
        context.memory_items[item_id] = memory_item


@when(parsers.parse('I query TinyDB with condition "{condition}"'))
def query_tinydb_with_condition(context, condition):
    """Step: I query TinyDB with a specific condition."""
    # Parse the condition (simple version for testing)
    field, value = condition.split("==")
    field = field.strip()
    value = value.strip()

    # Create a query dictionary
    query = {field: value}

    # Perform the query
    context.search_results = context.memory_manager.query_structured_data(query)


@then(parsers.parse("the list should contain {count:d} item"))
def check_search_results_count(context, count):
    """Step: the list should contain a specific number of items."""
    assert len(context.search_results) == count


# Scenario: Tag memory items with EDRR phases


@when(
    parsers.parse(
        'I store a memory item with content "{content}", type "{memory_type}", and EDRR phase "{edrr_phase}"'
    )
)
def store_memory_item_with_edrr_phase(context, content, memory_type, edrr_phase):
    """Step: I store a memory item with content, type, and EDRR phase."""
    memory_type_enum = MemoryType[memory_type]

    # Store the memory item with EDRR phase in metadata
    context.memory_item_id = context.memory_manager.store_with_edrr_phase(
        content=content, memory_type=memory_type_enum, edrr_phase=edrr_phase
    )


@then("I should receive a memory item ID")
def receive_memory_item_id(context):
    """Step: I should receive a memory item ID."""
    assert context.memory_item_id is not None
    assert isinstance(context.memory_item_id, str)


@then("I should be able to retrieve the memory item using its ID")
def retrieve_memory_item(context):
    """Step: I should be able to retrieve the memory item using its ID."""
    context.retrieved_item = context.memory_manager.retrieve(context.memory_item_id)
    assert context.retrieved_item is not None


@then(
    parsers.parse(
        'the retrieved memory item should have metadata with "{key}" set to "{value}"'
    )
)
def check_retrieved_item_metadata(context, key, value):
    """Step: the retrieved memory item should have metadata with a specific key and value."""
    assert key in context.retrieved_item.metadata
    assert context.retrieved_item.metadata[key] == value


# Scenario: Query memory items by EDRR phase


@given("I have stored the following memory items with EDRR phases")
def store_memory_items_with_edrr_phases(context, table):
    """Step: I have stored the following memory items with EDRR phases."""
    for row in table:
        content = row["content"]
        memory_type = MemoryType[row["type"]]
        edrr_phase = row["edrr_phase"]

        # Store the memory item with EDRR phase
        item_id = context.memory_manager.store_with_edrr_phase(
            content=content, memory_type=memory_type, edrr_phase=edrr_phase
        )

        # Keep track of the item for later use
        memory_item = context.memory_manager.retrieve(item_id)
        context.memory_items[item_id] = memory_item


@when(parsers.parse('I query memory items by EDRR phase "{edrr_phase}"'))
def query_memory_items_by_edrr_phase(context, edrr_phase):
    """Step: I query memory items by a specific EDRR phase."""
    context.search_results = context.memory_manager.query_by_edrr_phase(edrr_phase)


# Scenario: Maintain relationships between items across EDRR phases


@given("I have stored the following memory items with EDRR phases and relationships")
def store_memory_items_with_edrr_phases_and_relationships(context, table):
    """Step: I have stored the following memory items with EDRR phases and relationships."""
    for row in table:
        item_id = row["id"]
        content = row["content"]
        memory_type = MemoryType[row["type"]]
        edrr_phase = row["edrr_phase"]
        related_to = row["related_to"]

        # Create metadata with EDRR phase and relationship
        metadata = {
            "edrr_phase": edrr_phase,
            "related_to": related_to if related_to else None,
        }

        # Create and store the memory item
        memory_item = MemoryItem(
            id=item_id, content=content, memory_type=memory_type, metadata=metadata
        )

        # Store in the graph adapter
        context.graph_adapter.store(memory_item)

        # Keep track of the item for later use
        context.memory_items[item_id] = memory_item

        # Add relationship if specified
        if related_to:
            if related_to not in context.related_items:
                context.related_items[related_to] = []
            context.related_items[related_to].append(item_id)


@when(
    parsers.parse(
        'I query the graph for the evolution of item "{item_id}" across EDRR phases'
    )
)
def query_graph_for_evolution_across_edrr_phases(context, item_id):
    """Step: I query the graph for the evolution of an item across EDRR phases."""
    context.search_results = context.memory_manager.query_evolution_across_edrr_phases(
        item_id
    )


@then("I should receive a list of related memory items in EDRR phase order")
def receive_related_memory_items_in_edrr_phase_order(context):
    """Step: I should receive a list of related memory items in EDRR phase order."""
    assert context.search_results is not None
    assert isinstance(context.search_results, list)
    assert len(context.search_results) > 0


@then(parsers.parse('the items should be ordered by EDRR phase: "{phases}"'))
def check_items_ordered_by_edrr_phase(context, phases):
    """Step: the items should be ordered by specific EDRR phases."""
    expected_phases = [phase.strip() for phase in phases.split(",")]
    actual_phases = [item.metadata.get("edrr_phase") for item in context.search_results]

    # Check that the phases are in the expected order
    for i, expected_phase in enumerate(expected_phases):
        assert actual_phases[i] == expected_phase.strip('"')
