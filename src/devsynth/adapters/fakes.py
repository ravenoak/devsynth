"""Lightweight fakes for heavy adapter seams.

These fakes are intended purely for unit testing and fast smoke paths. They
implement the domain protocols without importing heavy optional dependencies
(e.g., chromadb, faiss, kuzu). Use them in unit tests to exercise control flow
without requiring extra packages or external services.

Conventions:
- Deterministic behavior (no randomness) to keep tests reliable.
- In-memory data only; process-local and cleared per instance.
- Minimal surface area: only methods used by tests are implemented fully.

This module aligns with docs/plan.md Phase 2 and docs/tasks.md §4.1.
"""

from __future__ import annotations

from typing import Any

from devsynth.application.memory.dto import VectorStoreStats
from devsynth.domain.interfaces.memory import MemoryStore, VectorStore
from devsynth.domain.models.memory import MemoryItem, MemoryVector


class FakeMemoryStore(MemoryStore):
    """A simple in-memory implementation of MemoryStore for tests.

    - Stores MemoryItem objects in a dict by id.
    - Provides naive substring search over ``content``.
    - Transactions are simulated by buffering operations until commit.
    """

    def __init__(self) -> None:
        self._store: dict[str, MemoryItem] = {}
        self._tx_buffers: dict[str, list[tuple[str, Any]]] = {}
        self._next_id = 1
        self._active_tx: str | None = None

    def _gen_id(self) -> str:
        nid = str(self._next_id)
        self._next_id += 1
        return nid

    def store(self, item: MemoryItem, transaction_id: str | None = None) -> str:
        item_id = item.id or self._gen_id()
        if self._active_tx:
            self._tx_buffers.setdefault(self._active_tx, []).append(
                ("store", (item_id, item))
            )
            return item_id
        self._store[item_id] = MemoryItem(
            id=item_id, **{k: v for k, v in item.__dict__.items() if k != "id"}
        )
        return item_id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        return self._store.get(item_id)

    def search(self, query: dict[str, Any]) -> list[MemoryItem]:
        text = str(query.get("text", "")).lower()
        mtype = query.get("type")
        results: list[MemoryItem] = []
        for itm in self._store.values():
            if mtype is not None and itm.memory_type != mtype:
                continue
            if text and text not in (itm.content or "").lower():
                continue
            results.append(itm)
        return results

    def delete(self, item_id: str) -> bool:
        if self._active_tx:
            self._tx_buffers.setdefault(self._active_tx, []).append(("delete", item_id))
            return True
        return self._store.pop(item_id, None) is not None

    def begin_transaction(self) -> str:
        tx_id = f"tx-{len(self._tx_buffers)+1}"
        self._tx_buffers[tx_id] = []
        self._active_tx = tx_id
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        if transaction_id != self._active_tx:
            return False
        ops = self._tx_buffers.pop(transaction_id, None)
        if ops is None:
            return False
        for op, payload in ops:
            if op == "store":
                item_id, item = payload
                self._store[item_id] = MemoryItem(
                    id=item_id, **{k: v for k, v in item.__dict__.items() if k != "id"}
                )
            elif op == "delete":
                item_id = payload
                self._store.pop(item_id, None)
        self._active_tx = None
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        if transaction_id != self._active_tx:
            return False
        self._active_tx = None
        return self._tx_buffers.pop(transaction_id, None) is not None

    def is_transaction_active(self, transaction_id: str) -> bool:
        return transaction_id == self._active_tx


class FakeVectorStore(VectorStore[MemoryVector]):
    """A simple in-memory vector store with cosine similarity for tests."""

    def __init__(self) -> None:
        self._vectors: dict[str, MemoryVector] = {}
        self._next_id = 1

    def _gen_id(self) -> str:
        nid = str(self._next_id)
        self._next_id += 1
        return nid

    def store_vector(self, vector: MemoryVector) -> str:
        vid = vector.id or self._gen_id()
        self._vectors[vid] = MemoryVector(
            id=vid,
            content=vector.content,
            embedding=vector.embedding,
            metadata=vector.metadata,
        )
        return vid

    def retrieve_vector(self, vector_id: str) -> MemoryVector | None:
        return self._vectors.get(vector_id)

    def similarity_search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[MemoryVector]:
        def cosine(a: list[float], b: list[float]) -> float:
            if not a or not b or len(a) != len(b):
                return -1.0
            import math

            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            if na == 0 or nb == 0:
                return -1.0
            return dot / (na * nb)

        scored = [
            (cosine(vec.embedding, query_embedding), vec)
            for vec in self._vectors.values()
        ]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [vec for _score, vec in scored[: top_k or 5]]

    def delete_vector(self, vector_id: str) -> bool:
        return self._vectors.pop(vector_id, None) is not None

    def get_collection_stats(self) -> VectorStoreStats:
        return {"collection_name": "fake", "vector_count": len(self._vectors)}
