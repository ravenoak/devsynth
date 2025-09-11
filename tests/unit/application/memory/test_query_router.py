from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from devsynth.application.memory.query_router import QueryRouter


@dataclass
class DummyItem:
    content: str
    id: str = field(default_factory=lambda: "id")
    metadata: dict[str, Any] = field(default_factory=dict)


class DummyAdapter:
    def __init__(self, results: list[DummyItem]):
        self._results = results

    def search(self, query: dict[str, str] | str) -> list[DummyItem]:
        return list(self._results)


class DummySyncManager:
    def __init__(self, grouped: dict[str, list[DummyItem]]):
        self._grouped = grouped

    def cross_store_query(self, query: str, stores: list[str] | None = None):
        if stores:
            return {k: v for k, v in self._grouped.items() if k in stores}
        return self._grouped


class DummyMemoryManager:
    def __init__(self):
        self.adapters = {
            "vector": DummyAdapter([DummyItem("vec")]),
            "graph": DummyAdapter([DummyItem("graph")]),
        }
        grouped = {k: list(v._results) for k, v in self.adapters.items()}
        self.sync_manager = DummySyncManager(grouped)

    def search_memory(self, query: str) -> list[DummyItem]:
        return [DummyItem("vec")]

    def query_related_items(self, query: str) -> list[DummyItem]:
        return [DummyItem("graph")]

    def _embed_text(self, text: str) -> list[float]:
        return [1.0]


@pytest.fixture
def router() -> QueryRouter:
    return QueryRouter(DummyMemoryManager())


@pytest.mark.fast
def test_direct_query_adds_source_store(router: QueryRouter):
    """Direct queries annotate the source store.

    ReqID: N/A"""

    items = router.direct_query("q", "vector")
    assert items[0].metadata["source_store"] == "vector"


@pytest.mark.fast
def test_cross_store_query_groups_results(router: QueryRouter):
    """Cross-store queries group and tag results.

    ReqID: N/A"""

    grouped = router.cross_store_query("q")
    assert set(grouped) == {"vector", "graph"}
    for store, items in grouped.items():
        assert all(item.metadata["source_store"] == store for item in items)


@pytest.mark.fast
def test_cascading_and_federated(router: QueryRouter):
    """Cascading and federated strategies aggregate results.

    ReqID: N/A"""

    cascading = router.cascading_query("q")
    assert {item.metadata["source_store"] for item in cascading} == {"vector", "graph"}
    federated = router.federated_query("q")
    assert len({id(item) for item in federated}) == len(federated)


@pytest.mark.fast
def test_context_aware_and_route(router: QueryRouter):
    """Context-aware routing delegates to strategies.

    ReqID: N/A"""

    context = {"user": "x"}
    context_res = router.context_aware_query("q", context)
    assert set(context_res) == {"vector", "graph"}
    assert router.route("q", store="vector")[0].metadata["source_store"] == "vector"
    assert "graph" in router.route("q", strategy="cross")
    assert isinstance(router.route("q", strategy="cascading"), list)
    assert isinstance(router.route("q", strategy="federated"), list)
    assert router.route("q", strategy="context_aware", context=context)
