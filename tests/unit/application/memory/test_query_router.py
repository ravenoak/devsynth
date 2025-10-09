from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from devsynth.application.memory.dto import MemoryRecord, build_memory_record
from devsynth.application.memory.query_router import QueryRouter
from devsynth.domain.models.memory import MemoryItem, MemoryType


def _build_record(store: str, content: str) -> MemoryRecord:
    item = MemoryItem(
        id=f"{store}-{content}",
        content=content,
        memory_type=MemoryType.CONTEXT,
        metadata={"source_store": store},
    )
    return build_memory_record(item, source=store)


class DummyAdapter:
    def __init__(self, results: list[MemoryRecord]) -> None:
        self._results = list(results)
        self.queries: list[dict[str, Any]] = []

    def search(self, query: dict[str, Any]) -> list[MemoryRecord]:
        self.queries.append(dict(query))
        return list(self._results)


class DummyGraphAdapter:
    """Adapter lacking ``search`` to exercise graph fallbacks."""

    def __init__(self, items: list[MemoryItem]) -> None:
        self.items = items


class DummySyncManager:
    def __init__(self, grouped: dict[str, list[MemoryRecord]]) -> None:
        self._grouped = {name: list(records) for name, records in grouped.items()}

    def cross_store_query(
        self, query: str, stores: list[str] | None = None
    ) -> dict[str, list[MemoryRecord]]:
        if stores is None:
            return {name: list(records) for name, records in self._grouped.items()}
        return {
            name: list(self._grouped[name]) for name in stores if name in self._grouped
        }


@dataclass
class DummyMemoryManager:
    adapters: dict[str, Any] = field(init=False)
    sync_manager: DummySyncManager = field(init=False)

    def __post_init__(self) -> None:
        vector_records = [_build_record("vector", "vec")]
        graph_items = [
            MemoryItem(
                id="graph-1",
                content="graph",
                memory_type=MemoryType.CONTEXT,
                metadata={"source_store": "graph"},
            )
        ]
        self.adapters = {
            "vector": object(),
            "graph": DummyGraphAdapter(graph_items),
            "tinydb": DummyAdapter([_build_record("tinydb", "doc")]),
        }
        grouped = {
            "vector": vector_records,
            "graph": [_build_record("graph", "rel")],
        }
        self._vector_results = vector_records
        self._graph_items = graph_items
        self.sync_manager = DummySyncManager(grouped)

    def search_memory(self, query: str) -> list[MemoryRecord]:
        return list(self._vector_results)

    def query_related_items(self, query: str) -> list[MemoryItem]:
        return list(self._graph_items)

    def _embed_text(self, text: str) -> list[float]:
        return [float(len(text) or 1)]


@pytest.fixture
def router() -> QueryRouter:
    return QueryRouter(DummyMemoryManager())


@pytest.mark.fast
def test_direct_query_and_vector_branch(router: QueryRouter) -> None:
    """Direct queries return typed DTO payloads with sources."""

    result = router.direct_query("hello", "vector")
    assert result["store"] == "vector"
    assert all(isinstance(record, MemoryRecord) for record in result["records"])
    assert {record.source for record in result["records"]} == {"vector"}

    graph_result = router.direct_query("topic", "graph")
    assert graph_result["store"] == "graph"
    assert graph_result["records"][0].item.content == "graph"


@pytest.mark.fast
def test_cross_store_query_groups_results(router: QueryRouter) -> None:
    """Cross-store queries return grouped DTO responses."""

    grouped = router.cross_store_query("topic")
    assert grouped["query"].startswith("topic")
    assert set(grouped["by_store"]) == {"vector", "graph"}
    for store, payload in grouped["by_store"].items():
        assert payload["store"] == store
        assert all(record.source == store for record in payload["records"])


@pytest.mark.fast
def test_cascading_and_federated(router: QueryRouter) -> None:
    """Cascading and federated strategies yield MemoryRecord sequences."""

    cascading = router.cascading_query("topic")
    assert {record.source for record in cascading} == {"vector", "graph"}

    federated = router.federated_query("topic")
    assert all(isinstance(record, MemoryRecord) for record in federated)
    assert len({id(record) for record in federated}) == len(federated)


@pytest.mark.fast
def test_context_aware_and_route(router: QueryRouter) -> None:
    """Context-aware routing delegates to the configured strategy."""

    context = {"user": "x"}
    context_res = router.context_aware_query("topic", context)
    assert "user:x" in context_res["query"]
    assert set(context_res["by_store"]) == {"vector", "graph"}

    direct = router.route("topic", store="vector")
    assert direct["store"] == "vector"
    assert router.route("topic", strategy="cross")["by_store"]
    assert isinstance(router.route("topic", strategy="cascading"), list)
    assert isinstance(router.route("topic", strategy="federated"), list)
    assert router.route("topic", strategy="context_aware", context=context)
