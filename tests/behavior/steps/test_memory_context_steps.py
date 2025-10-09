"""
Step Definitions for Memory and Context System BDD Tests

This file implements the step definitions for the Memory and Context System
feature file, which tests the functionality of storing, retrieving, and
searching for information during the development process.
"""

import json

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file


scenarios(feature_path(__file__, "general", "memory_context_system.feature"))

from devsynth.domain.interfaces.memory import ContextManager, MemoryStore

# Import the modules needed for the steps
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.ports.memory_port import MemoryPort


class MockMemoryStore(MemoryStore):
    """Mock implementation of MemoryStore for testing."""

    def __init__(self):
        self.items = {}
        self.next_id = 1

    def store(self, item: MemoryItem) -> str:
        """Store an item and return its ID."""
        item_id = f"item_{self.next_id}"
        self.next_id += 1
        item.id = item_id
        self.items[item_id] = item
        return item_id

    def retrieve(self, item_id: str) -> MemoryItem:
        """Retrieve an item by ID."""
        return self.items.get(item_id)

    def search(self, query):
        """Search for items matching the query."""
        results = []
        for item in self.items.values():
            match = True
            for key, value in query.items():
                if key == "type":
                    if item.memory_type != value:
                        match = False
                        break
                elif key in item.metadata:
                    if item.metadata[key] != value:
                        match = False
                        break
                else:
                    match = False
                    break
            if match:
                results.append(item)
        return results

    def delete(self, item_id: str) -> bool:
        """Delete an item from memory by ID."""
        if item_id in self.items:
            del self.items[item_id]
            return True
        return False


class MockContextManager(ContextManager):
    """Mock implementation of ContextManager for testing."""

    def __init__(self):
        self.context = {}

    def add_to_context(self, key, value):
        """Add a value to the context."""
        self.context[key] = value

    def get_from_context(self, key):
        """Get a value from the context."""
        return self.context.get(key)

    def get_full_context(self):
        """Get the full context."""
        return self.context

    def clear_context(self):
        """Clear the current context."""
        self.context = {}


@pytest.fixture
def context():
    """Fixture to provide a context object for sharing state between steps."""

    class Context:
        def __init__(self):
            self.memory_store = MockMemoryStore()
            self.context_manager = MockContextManager()
            self.memory_port = MemoryPort(
                memory_store=self.memory_store, context_manager=self.context_manager
            )
            self.memory_item_id = None
            self.retrieved_item = None
            self.search_results = None
            self.context_value = None
            self.full_context = None

    return Context()


# Background steps


@given("the DevSynth system is initialized")
def devsynth_initialized(context):
    """Step: the DevSynth system is initialized."""
    assert context.memory_store is not None
    assert context.context_manager is not None


@given("a memory store is configured")
def memory_store_configured(context):
    """Step: a memory store is configured."""
    # The context fixture already configures a memory store
    assert context.memory_store is not None


@given("a context manager is configured")
def context_manager_configured(context):
    """Step: a context manager is configured."""
    # The context fixture already configures a context manager
    assert context.context_manager is not None


# Scenario: Store and retrieve memory item


@when(
    parsers.parse(
        'I store a memory item with content "{content}" and type "{memory_type}"'
    )
)
def store_memory_item(context, content, memory_type):
    """Step: I store a memory item with content and type."""
    memory_type_enum = MemoryType[memory_type]
    context.memory_item_id = context.memory_port.store_memory(
        content=content, memory_type=memory_type_enum
    )


@then("I should receive a memory item ID")
def receive_memory_item_id(context):
    """Step: I should receive a memory item ID."""
    assert context.memory_item_id is not None
    assert isinstance(context.memory_item_id, str)
    assert context.memory_item_id.startswith("item_")


@then("I should be able to retrieve the memory item using its ID")
def retrieve_memory_item(context):
    """Step: I should be able to retrieve the memory item using its ID."""
    context.retrieved_item = context.memory_port.retrieve_memory(context.memory_item_id)
    assert context.retrieved_item is not None


@then(
    parsers.parse(
        'the retrieved memory item should have content "{content}" and type "{memory_type}"'
    )
)
def check_retrieved_item_content_and_type(context, content, memory_type):
    """Step: the retrieved memory item should have content and type."""
    assert context.retrieved_item.content == content
    assert context.retrieved_item.memory_type == MemoryType[memory_type]


# Scenario: Store memory item with metadata


@when(
    parsers.parse(
        'I store a memory item with content "{content}", type "{memory_type}", and metadata:'
    )
)
def store_memory_item_with_metadata(context, content, memory_type, table):
    """Step: I store a memory item with content, type, and metadata."""
    memory_type_enum = MemoryType[memory_type]
    metadata = {row["key"]: row["value"] for row in table}
    context.memory_item_id = context.memory_port.store_memory(
        content=content, memory_type=memory_type_enum, metadata=metadata
    )


@then("the retrieved memory item should have the specified metadata")
def check_retrieved_item_metadata(context, table):
    """Step: the retrieved memory item should have the specified metadata."""
    metadata = {row["key"]: row["value"] for row in table}
    for key, value in metadata.items():
        assert key in context.retrieved_item.metadata
        assert context.retrieved_item.metadata[key] == value


# Scenario: Search for memory items


@given("I have stored the following memory items:")
def store_multiple_memory_items(context, table):
    """Step: I have stored the following memory items."""
    for row in table:
        memory_type_enum = MemoryType[row["type"]]
        metadata = json.loads(row["metadata"])
        context.memory_port.store_memory(
            content=row["content"], memory_type=memory_type_enum, metadata=metadata
        )


@when("I search for memory items with query:")
def search_memory_items(context, table):
    """Step: I search for memory items with query."""
    query = {row["key"]: row["value"] for row in table}
    if "type" in query:
        query["type"] = MemoryType[query["type"]]
    context.search_results = context.memory_port.search_memory(query)


@then("I should receive a list of matching memory items")
def receive_search_results(context):
    """Step: I should receive a list of matching memory items."""
    assert context.search_results is not None
    assert isinstance(context.search_results, list)


@then(parsers.parse("the list should contain {count:d} item"))
def check_search_results_count(context, count):
    """Step: the list should contain a specific number of items."""
    assert len(context.search_results) == count


@then(parsers.parse('the first item should have content "{content}"'))
def check_first_search_result_content(context, content):
    """Step: the first item should have specific content."""
    assert context.search_results[0].content == content


# Scenario: Add and retrieve context values


@given(parsers.parse('I have added a value "{value}" to the context with key "{key}"'))
def given_add_value_to_context(context, value, key):
    """Step: I have added a value to the context with a key."""
    context.memory_port.add_to_context(key, value)


@when(parsers.parse('I add a value "{value}" to the context with key "{key}"'))
def add_value_to_context(context, value, key):
    """Step: I add a value to the context with a key."""
    context.memory_port.add_to_context(key, value)


@then(parsers.parse('I should be able to retrieve the value using the key "{key}"'))
def retrieve_value_from_context(context, key):
    """Step: I should be able to retrieve the value using a key."""
    context.context_value = context.memory_port.get_from_context(key)
    assert context.context_value is not None


@then(
    parsers.parse('I should still be able to retrieve the value using the key "{key}"')
)
def still_retrieve_value_from_context(context, key):
    """Step: I should still be able to retrieve the value using a key after operations."""
    context.context_value = context.memory_port.get_from_context(key)
    assert context.context_value is not None


@then(parsers.parse('the retrieved value should be "{value}"'))
def check_retrieved_context_value(context, value):
    """Step: the retrieved value should be a specific value."""
    assert context.context_value == value


# Scenario: Get full context


@given("I have added the following values to the context:")
def add_multiple_values_to_context(context, table):
    """Step: I have added multiple values to the context."""
    for row in table:
        context.memory_port.add_to_context(row["key"], row["value"])


@when("I request the full context")
def request_full_context(context):
    """Step: I request the full context."""
    context.full_context = context.memory_port.get_full_context()


@then("I should receive a dictionary with all context values")
def receive_full_context(context):
    """Step: I should receive a dictionary with all context values."""
    assert context.full_context is not None
    assert isinstance(context.full_context, dict)


@then(parsers.parse('the dictionary should contain the keys "{keys}"'))
def check_full_context_keys(context, keys):
    """Step: the dictionary should contain specific keys."""
    key_list = [key.strip() for key in keys.split(",")]
    for key in key_list:
        assert key in context.full_context


@then("the values should match what was added")
def check_full_context_values(context, table):
    """Step: the values should match what was added."""
    for row in table:
        assert context.full_context[row["key"]] == row["value"]


# Scenario: Context persistence across operations


@when("I perform multiple memory operations")
def perform_multiple_memory_operations(context):
    """Step: I perform multiple memory operations."""
    # Store a memory item
    context.memory_port.store_memory(
        content="Test content", memory_type=MemoryType.CODE
    )

    # Search for memory items
    context.memory_port.search_memory({"type": MemoryType.CODE})

    # Add another context value
    context.memory_port.add_to_context("another_key", "another_value")
