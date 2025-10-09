"""Query Router for hybrid memory system."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ...logging_setup import DevSynthLogger
from .adapter_types import AdapterRegistry, SupportsSearch
from .dto import (
    GroupedMemoryResults,
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
    MemoryRecordInput,
    MemorySearchQuery,
    build_query_results,
    deduplicate_records,
)
from .vector_protocol import VectorStoreProtocol

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from .memory_manager import MemoryManager

logger = DevSynthLogger(__name__)


class QueryRouter:
    """Route queries to the appropriate memory stores using DTO responses."""

    def __init__(self, memory_manager: "MemoryManager") -> None:
        self.memory_manager = memory_manager

    def direct_query(self, query: str, store: str) -> MemoryQueryResults:
        """Query a single store and return normalized results."""

        store_key = store.lower()
        adapters: AdapterRegistry = self.memory_manager.adapters
        adapter = adapters.get(store_key)
        if adapter is None:
            logger.warning("Adapter %s not found", store_key)
            return build_query_results(store_key, [])

        if store_key == "vector":
            records = self.memory_manager.search_memory(query)
            return build_query_results(store_key, records)

        if store_key == "graph" and not hasattr(adapter, "search"):
            results = self.memory_manager.query_related_items(query)
            return build_query_results(store_key, results)

        if isinstance(adapter, SupportsSearch):
            payload = adapter.search({"content": query})
            return build_query_results(store_key, payload)

        logger.warning("Adapter %s does not support direct queries", store_key)
        return build_query_results(store_key, [])

    def cross_store_query(
        self, query: str, stores: Sequence[str] | None = None
    ) -> GroupedMemoryResults:
        """Query configured stores and return grouped DTO results."""

        requested = list(stores) if stores is not None else None
        raw_grouped = self.memory_manager.sync_manager.cross_store_query(
            query, requested
        )
        by_store = {
            name: build_query_results(name, payload)
            for name, payload in raw_grouped.items()
        }
        return {"by_store": by_store, "query": query}

    def cascading_query(
        self, query: str, order: Sequence[str] | None = None
    ) -> list[MemoryRecord]:
        """Query stores sequentially and concatenate unique records."""

        cascade_order = (
            list(order)
            if order is not None
            else [
                "document",
                "tinydb",
                "vector",
                "graph",
            ]
        )
        collected: list[MemoryRecord] = []
        for name in cascade_order:
            if name not in self.memory_manager.adapters:
                continue
            results = self.direct_query(query, name)
            collected.extend(results.get("records", []))
        return deduplicate_records(collected)

    def federated_query(self, query: str) -> list[MemoryRecord]:
        """Aggregate results from all stores and rank by cosine similarity."""

        grouped = self.cross_store_query(query)
        aggregated: list[MemoryRecord] = []
        for payload in grouped["by_store"].values():
            aggregated.extend(payload.get("records", []))

        unique_records = deduplicate_records(aggregated)
        query_emb = self.memory_manager._embed_text(query)

        vector_adapter = self.memory_manager.adapters.get("vector")
        vector_dim = None
        if isinstance(vector_adapter, VectorStoreProtocol):
            vector_dim = getattr(vector_adapter, "dimension", None)

        def _embedding(record: MemoryRecord) -> list[float]:
            metadata = record.metadata or {}
            candidate = metadata.get("embedding")
            if isinstance(candidate, list):
                return [float(x) for x in candidate]
            if vector_dim is None:
                return self.memory_manager._embed_text(str(record.content))
            return self.memory_manager._embed_text(
                str(record.content), dimension=int(vector_dim)
            )

        def _similarity(a: list[float], b: list[float]) -> float:
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
        self,
        query: str,
        context: MemoryMetadata,
        store: str | None = None,
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
        store: str | None = None,
        strategy: str = "direct",
        context: MemoryMetadata | None = None,
        stores: Sequence[str] | None = None,
    ) -> MemoryQueryResults | GroupedMemoryResults | list[MemoryRecord]:
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
