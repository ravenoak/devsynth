"""Query Router for hybrid memory system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ...logging_setup import DevSynthLogger
from .dto import (
    GroupedMemoryResults,
    MemoryQueryResults,
    MemoryRecord,
    build_query_results,
    deduplicate_records,
)

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from .memory_manager import MemoryManager

logger = DevSynthLogger(__name__)


class QueryRouter:
    """Route queries to the appropriate memory stores using DTO responses."""

    def __init__(self, memory_manager: "MemoryManager") -> None:
        self.memory_manager = memory_manager

    def direct_query(self, query: str, store: str) -> MemoryQueryResults:
        """Query a single store and return normalized results."""

        store = store.lower()
        adapter = self.memory_manager.adapters.get(store)
        if not adapter:
            logger.warning("Adapter %s not found", store)
            return build_query_results(store, [])

        if store == "vector":
            records = self.memory_manager.search_memory(query)
            return build_query_results(store, records)

        if store == "graph" and not hasattr(adapter, "search"):
            results = self.memory_manager.query_related_items(query)
            return build_query_results(store, results)

        if hasattr(adapter, "search"):
            payload = (
                adapter.search({"content": query})
                if isinstance(query, str)
                else adapter.search(query)
            )
            return build_query_results(store, payload)

        logger.warning("Adapter %s does not support direct queries", store)
        return build_query_results(store, [])

    def cross_store_query(
        self, query: str, stores: Optional[List[str]] | None = None
    ) -> GroupedMemoryResults:
        """Query configured stores and return grouped DTO results."""

        raw_grouped = self.memory_manager.sync_manager.cross_store_query(query, stores)
        by_store = {
            name: build_query_results(name, payload)
            for name, payload in raw_grouped.items()
        }
        return {"by_store": by_store, "query": query}

    def cascading_query(
        self, query: str, order: Optional[List[str]] = None
    ) -> List[MemoryRecord]:
        """Query stores sequentially and concatenate unique records."""

        order = order or ["document", "tinydb", "vector", "graph"]
        collected: List[MemoryRecord] = []
        for name in order:
            if name not in self.memory_manager.adapters:
                continue
            results = self.direct_query(query, name)
            collected.extend(results["records"])
        return deduplicate_records(collected)

    def federated_query(self, query: str) -> List[MemoryRecord]:
        """Aggregate results from all stores and rank by cosine similarity."""

        grouped = self.cross_store_query(query)
        aggregated: List[MemoryRecord] = []
        for payload in grouped["by_store"].values():
            aggregated.extend(payload["records"])

        unique_records = deduplicate_records(aggregated)
        query_emb = self.memory_manager._embed_text(query)

        def _embedding(record: MemoryRecord) -> List[float]:
            metadata = record.metadata or {}
            candidate = metadata.get("embedding")
            if isinstance(candidate, list):
                return [float(x) for x in candidate]
            return self.memory_manager._embed_text(str(record.content))

        def _similarity(a: List[float], b: List[float]) -> float:
            import math

            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        unique_records.sort(
            key=lambda record: _similarity(query_emb, _embedding(record)),
            reverse=True,
        )

        return unique_records

    def context_aware_query(
        self, query: str, context: Dict[str, Any], store: Optional[str] = None
    ) -> MemoryQueryResults | GroupedMemoryResults:
        """Enhance the query with context information before routing."""

        context_str = " ".join(f"{k}:{v}" for k, v in context.items())
        enhanced_query = f"{query} {context_str}".strip()
        if store:
            return self.direct_query(enhanced_query, store)
        return self.cross_store_query(enhanced_query)

    def route(
        self,
        query: str,
        store: Optional[str] = None,
        strategy: str = "direct",
        context: Optional[Dict[str, Any]] = None,
        stores: Optional[List[str]] | None = None,
    ) -> MemoryQueryResults | GroupedMemoryResults | List[MemoryRecord]:
        """Route a query according to the specified strategy."""

        if strategy == "direct" and store:
            return self.direct_query(query, store)
        if strategy == "cross":
            return self.cross_store_query(query, stores)
        if strategy == "cascading":
            return self.cascading_query(query)
        if strategy == "federated":
            return self.federated_query(query)
        if strategy == "context_aware":
            return self.context_aware_query(query, context or {}, store)

        logger.warning("Unknown query strategy %s", strategy)
        return []
