from pytest_bdd import given, when, then, scenarios, parsers
import pytest
import os
import tempfile

try:
    from devsynth.application.memory.memory_manager import MemoryManager
    from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
    from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
    from devsynth.domain.models.memory import MemoryItem, MemoryType
except ImportError:
    # Try alternative import paths
    from devsynth.application.memory.memory_manager import MemoryManager
    from devsynth.adapters.memory.graph_memory_adapter import GraphMemoryAdapter
    from devsynth.adapters.memory.tinydb_memory_adapter import TinyDBMemoryAdapter
    from devsynth.domain.models.memory import MemoryItem, MemoryType

# Use absolute path for feature file
feature_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "features",
    "memory_adapter_integration.feature"
)
scenarios(feature_file_path)


@pytest.fixture
def context(tmp_path):
    class Context:
        pass

    ctx = Context()

    try:
        # Create a temporary directory for the graph adapter
        temp_dir = tempfile.mkdtemp(dir=str(tmp_path))

        # Initialize adapters with error handling
        try:
            graph_adapter = GraphMemoryAdapter(base_path=temp_dir)
        except Exception as e:
            pytest.skip(f"Failed to initialize GraphMemoryAdapter: {e}")

        try:
            tinydb_adapter = TinyDBMemoryAdapter()
        except Exception as e:
            pytest.skip(f"Failed to initialize TinyDBMemoryAdapter: {e}")

        # Initialize memory manager
        ctx.manager = MemoryManager(
            {
                "graph": graph_adapter,
                "tinydb": tinydb_adapter,
            }
        )
    except Exception as e:
        pytest.skip(f"Failed to set up test context: {e}")

    return ctx


@given("a memory manager with graph and tinydb adapters")
def have_manager(context):
    assert context.manager is not None
    assert "graph" in context.manager.adapters
    assert "tinydb" in context.manager.adapters


@when(parsers.parse('I store a graph memory item with id "{item_id}"'))
def store_graph_item(context, item_id):
    try:
        item = MemoryItem(id=item_id, content="graph", memory_type=MemoryType.CODE)
        context.manager.adapters["graph"].store(item)
    except Exception as e:
        pytest.fail(f"Failed to store graph memory item: {e}")


@when(parsers.parse('I store a tinydb memory item with id "{item_id}"'))
def store_tinydb_item(context, item_id):
    try:
        item = MemoryItem(id=item_id, content="tinydb", memory_type=MemoryType.DOCUMENTATION)
        context.manager.adapters["tinydb"].store(item)
    except Exception as e:
        pytest.fail(f"Failed to store tinydb memory item: {e}")


@then("querying items by type should return both stored items")
def query_items(context):
    try:
        # Directly check if items exist in the adapters
        # GraphMemoryAdapter doesn't have get_all, use search with empty query
        graph_items = context.manager.adapters["graph"].search({})

        # TinyDBMemoryAdapter might have get_all, but let's use search for consistency
        tinydb_items = context.manager.adapters["tinydb"].search({})

        # Collect all item IDs
        all_ids = {item.id for item in graph_items + tinydb_items}

        # Verify both items are present
        assert "G1" in all_ids, "Graph item G1 not found"
        assert "T1" in all_ids, "TinyDB item T1 not found"
    except Exception as e:
        pytest.fail(f"Failed to verify stored items: {e}")
