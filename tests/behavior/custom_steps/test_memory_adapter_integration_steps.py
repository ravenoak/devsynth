from pytest_bdd import given, when, then, scenarios, parsers
import pytest

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType

scenarios("../features/memory_adapter_integration.feature")


@pytest.fixture
def context(tmp_path):
    class Context:
        pass

    ctx = Context()
    ctx.manager = MemoryManager(
        {
            "graph": GraphMemoryAdapter(base_path=str(tmp_path)),
            "tinydb": TinyDBMemoryAdapter(),
        }
    )
    return ctx


@given("a memory manager with graph and tinydb adapters")
def have_manager(context):
    assert context.manager is not None


@when(parsers.parse('I store a graph memory item with id "{item_id}"'))
def store_graph_item(context, item_id):
    item = MemoryItem(id=item_id, content="graph", memory_type=MemoryType.CODE)
    context.manager.adapters["graph"].store(item)


@when(parsers.parse('I store a tinydb memory item with id "{item_id}"'))
def store_tinydb_item(context, item_id):
    item = MemoryItem(id=item_id, content="tinydb", memory_type=MemoryType.REQUIREMENT)
    context.manager.adapters["tinydb"].store(item)


@then("querying items by type should return both stored items")
def query_items(context):
    codes = context.manager.query_by_type(MemoryType.CODE)
    reqs = context.manager.query_by_type(MemoryType.REQUIREMENT)
    ids = {i.id for i in codes + reqs}
    assert {"G1", "T1"} <= ids
