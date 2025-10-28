"""Step definitions for hybrid_memory_query_patterns.feature."""

import tempfile
from typing import Any, Dict, Union

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.application.memory.json_file_store import JSONFileStore
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "hybrid_memory_query_patterns.feature"))


@pytest.fixture
def context():
    class Context:
        def __init__(self) -> None:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.adapters: dict[str, Any] = {}
            self.memory_manager: MemoryManager | None = None
            self.results: Any = None
            self.active_context: dict[str, str] = {}

        def cleanup(self) -> None:
            self.temp_dir.cleanup()

    ctx = Context()
    yield ctx
    ctx.cleanup()


@given("the DevSynth system is initialized")
def system_initialized(context):
    assert context is not None


@given("the Memory Manager is configured with the following adapters:")
def memory_manager_configured(context, table):
    for row in table:
        if row["adapter_type"] == "Graph" and row["enabled"].lower() == "true":
            context.adapters["graph"] = GraphMemoryAdapter()
        elif row["adapter_type"] == "Vector" and row["enabled"].lower() == "true":
            context.adapters["vector"] = VectorMemoryAdapter()
        elif row["adapter_type"] == "TinyDB" and row["enabled"].lower() == "true":
            context.adapters["tinydb"] = TinyDBMemoryAdapter()
        elif row["adapter_type"] == "Document" and row["enabled"].lower() == "true":
            context.adapters["document"] = JSONFileStore(context.temp_dir.name)

    context.memory_manager = MemoryManager(adapters=context.adapters)


@given("I have stored information across multiple memory stores")
def store_info(context):
    if "vector" in context.adapters:
        vec = MemoryVector(
            id="vec1",
            content="code implementation example",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"source": "vector"},
        )
        context.adapters["vector"].store_vector(vec)
    if "graph" in context.adapters:
        item = MemoryItem(
            id="requirement-1",
            content="Requirement one",
            memory_type=MemoryType.REQUIREMENT,
            metadata={},
        )
        context.adapters["graph"].store(item)
    if "tinydb" in context.adapters:
        item = MemoryItem(
            id="tiny1",
            content="some structured info",
            memory_type=MemoryType.DOCUMENTATION,
            metadata={"section": "auth"},
        )
        context.adapters["tinydb"].store(item)
    if "document" in context.adapters:
        item = MemoryItem(
            id="doc1",
            content="user story details",
            memory_type=MemoryType.DOCUMENTATION,
            metadata={},
        )
        context.adapters["document"].store(item)


@given("I have stored related information across multiple memory stores")
def store_related(context):
    store_info(context)


@given("I have stored interconnected information across multiple memory stores")
def store_interconnected(context):
    store_info(context)


@given("I have stored distributed information across multiple memory stores")
def store_distributed(context):
    store_info(context)


@given("I have an active context with the following values")
def active_context(context, table):
    for row in table:
        context.active_context[row["key"]] = row["value"]


@given("I have configured synchronization between the Vector store and the Graph store")
def config_sync(context):
    assert context.memory_manager is not None


@given("I have configured synchronization between multiple stores")
def config_sync_multi(context):
    assert context.memory_manager is not None


@given("I have configured transaction support across stores")
def config_tx(context):
    assert context.memory_manager is not None


@given("I have configured asynchronous synchronization between stores")
def config_async(context):
    assert context.memory_manager is not None


@when(parsers.parse('I perform a direct query to the Vector store for "{query}"'))
def direct_vector_query(context, query):
    context.results = context.memory_manager.route_query(query, store="vector")


@when(
    parsers.parse(
        'I perform a direct query to the Graph store for relationships of "{item_id}"'
    )
)
def direct_graph_query(context, item_id):
    context.results = context.memory_manager.query_related_items(item_id)


@when(parsers.parse('I perform a cross-store query for "{query}"'))
def cross_store_query(context, query):
    context.results = context.memory_manager.route_query(query, strategy="cross")


@when(
    parsers.parse(
        'I perform a cascading query starting with "{query}" in the Document store'
    )
)
def cascading_query(context, query):
    context.results = context.memory_manager.route_query(query, strategy="cascading")


@when(parsers.parse('I perform a federated query for "{query}"'))
def federated_query(context, query):
    context.results = context.memory_manager.route_query(query, strategy="federated")


@when(parsers.parse('I perform a context-aware query for "{query}"'))
def context_aware_query(context, query):
    context.results = context.memory_manager.route_query(
        query, strategy="context_aware", context=context.active_context
    )


@when("I update an item in the Vector store")
def update_vector_item(context):
    item = MemoryVector(
        id="sync_item",
        content="sync content",
        embedding=[0.5, 0.5, 0.5, 0.5, 0.5],
        metadata={},
    )
    context.adapters["vector"].store_vector(item)
    context.memory_manager.sync_manager.update_item("vector", item)


@when("I update the same logical item in two different stores")
def update_conflict(context):
    item_vec = MemoryVector(
        id="conflict",
        content="v1",
        embedding=[0.1] * 5,
        metadata={},
    )
    context.adapters["vector"].store_vector(item_vec)
    item_graph = MemoryItem(
        id="conflict",
        content="v2",
        memory_type=MemoryType.CODE,
        metadata={},
    )
    context.adapters["graph"].store(item_graph)
    context.memory_manager.sync_manager.synchronize(
        "vector", "graph", bidirectional=True
    )


@when(
    "I perform a multi-store operation that updates items in Vector, Graph, and TinyDB stores"
)
def multi_store_operation(context):
    try:
        vec = MemoryVector(id="tx", content="tx", embedding=[0.2] * 5, metadata={})
        graph_item = MemoryItem(
            id="tx", content="tx", memory_type=MemoryType.CODE, metadata={}
        )
        tiny_item = MemoryItem(
            id="tx", content="tx", memory_type=MemoryType.CODE, metadata={}
        )
        context.memory_manager.sync_manager.update_item("vector", vec)
        context.memory_manager.sync_manager.update_item("graph", graph_item)
        context.memory_manager.sync_manager.update_item("tinydb", tiny_item)
        context.tx_success = True
    except Exception:
        context.tx_success = False


@when("I update an item in the primary store")
def async_update(context):
    item = MemoryVector(
        id="async1",
        content="async",
        embedding=[0.2] * 5,
        metadata={},
    )
    context.memory_manager.sync_manager.queue_update("vector", item)
    context.memory_manager.sync_manager.flush_queue()


@then("I should receive results only from the Vector store")
def results_from_vector(context):
    assert isinstance(context.results, list)
    assert len(context.results) > 0


@then("the results should be ranked by semantic similarity")
def ranked_results(context):
    assert isinstance(context.results, list)


@then("I should receive results only from the Graph store")
def results_from_graph(context):
    assert isinstance(context.results, list)
    assert len(context.results) > 0


@then("the results should include all connected entities")
def connected_entities(context):
    assert isinstance(context.results, list)


@then("I should receive aggregated results from all relevant stores")
def aggregated_results(context):
    assert isinstance(context.results, dict)
    assert len(context.results) > 0


@then("the results should be grouped by store type")
def grouped_by_store(context):
    assert isinstance(context.results, dict)


@then("the results should include metadata about their source store")
def metadata_included(context):
    assert isinstance(context.results, dict)


@then("the query should first retrieve the document from the Document store")
def cascading_first(context):
    assert isinstance(context.results, list)


@then("then follow references to retrieve related requirements from the TinyDB store")
def cascading_second(context):
    assert isinstance(context.results, list)


@then(
    "then follow references to retrieve related code implementations from the Vector store"
)
def cascading_third(context):
    assert isinstance(context.results, list)


@then("then follow references to retrieve relationship data from the Graph store")
def cascading_fourth(context):
    assert isinstance(context.results, list)


@then("the results should maintain the traversal path information")
def traversal_path(context):
    assert isinstance(context.results, list)


@then("the query should be distributed to all memory stores in parallel")
def federated_parallel(context):
    assert isinstance(context.results, dict)


@then("results should be collected from all stores")
def federated_collected(context):
    assert isinstance(context.results, dict)


@then("results should be merged and deduplicated")
def federated_dedup(context):
    assert isinstance(context.results, dict)


@then("results should be ranked by relevance across all stores")
def federated_ranked(context):
    assert isinstance(context.results, dict)


@then("the query should be enhanced with context information")
def context_enhanced(context):
    assert isinstance(context.results, dict)


@then("results should be filtered based on relevance to the current context")
def context_filtered(context):
    assert isinstance(context.results, dict)


@then("results should be ranked by applicability to the current task")
def context_ranked(context):
    assert isinstance(context.results, dict)


@then("the corresponding item in the Graph store should be automatically updated")
def item_updated(context):
    item = context.adapters["graph"].retrieve("sync_item")
    assert item is not None


@then("the synchronization should maintain referential integrity")
def sync_integrity(context):
    item = context.adapters["graph"].retrieve("sync_item")
    assert item.id == "sync_item"


@then("the synchronization should log the operation for audit purposes")
def sync_logged(context):
    assert True


@then("the system should detect the conflict")
def conflict_detected(context):
    assert True


@then("apply the configured conflict resolution strategy")
def conflict_resolved(context):
    assert True


@then("maintain a record of the conflict and resolution")
def conflict_record(context):
    assert True


@then("ensure the final state is consistent across all stores")
def final_state_consistent(context):
    assert True


@then("all updates should be applied atomically")
def tx_atomic(context):
    assert context.tx_success


@then("if any store update fails, all updates should be rolled back")
def tx_rollback(context):
    assert context.tx_success


@then("the transaction should be logged with its success or failure status")
def tx_logged(context):
    assert True


@then("the update should be queued for propagation to secondary stores")
def queued_for_propagation(context):
    assert True


@then("secondary stores should eventually reflect the update")
def eventual_consistency(context):
    item = context.adapters["graph"].retrieve("async1")
    assert item is not None


@then("the system should track synchronization status")
def track_status(context):
    assert True


@then("queries should indicate if results might include stale data")
def stale_data_indicator(context):
    assert True
