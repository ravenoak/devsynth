import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "memory_operations.feature"))


@pytest.fixture
def context():
    class Context:
        adapter: MemorySystemAdapter
        item_id: str
        retrieved: MemoryItem

    return Context()


@given("a memory system adapter")
def given_adapter(context):
    context.adapter = MemorySystemAdapter.create_for_testing()


@when(parsers.parse('I write "{content}" to memory'))
def write_memory(context, content):
    item = MemoryItem(id="", content=content, memory_type=MemoryType.CONTEXT)
    context.item_id = context.adapter.write(item)


@when("I read the item from memory")
def read_memory(context):
    context.retrieved = context.adapter.read(context.item_id)


@then(parsers.parse('the retrieved content should be "{content}"'))
def check_content(context, content):
    assert context.retrieved.content == content
