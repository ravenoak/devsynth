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

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from devsynth.domain.interfaces.memory import MemoryStore, VectorStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class FakeMemoryStore(MemoryStore):
    """A simple in-memory implementation of MemoryStore for tests.

    - Stores MemoryItem objects in a dict by id.
    - Provides naive substring search over ``content``.
    - Transactions are simulated by buffering operations until commit.
    """

    def __init__(self) -> None:
        self._store: Dict[str, MemoryItem] = {}
        self._tx_buffers: Dict[str, List[Tuple[str, Any]]] = {}
        self._next_id = 1

    def _gen_id(self) -> str:
        nid = str(self._next_id)
        self._next_id += 1
        return nid

    def store(self, item: MemoryItem, transaction_id: str | None = None) -> str:  # type: ignore[override]
        item_id = item.id or self._gen_id()
        if transaction_id:
            self._tx_buffers.setdefault(transaction_id, []).append(("store", (item_id, item)))
            return item_id
        self._store[item_id] = MemoryItem(id=item_id, **{k: v for k, v in item.__dict__.items() if k != "id"})
        return item_id

    def retrieve(self, item_id: str) -> Optional[MemoryItem]:  # type: ignore[override]
        return self._store.get(item_id)

    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:  # type: ignore[override]
        text = str(query.get("text", "")).lower()
        mtype = query.get("type")
        results: List[MemoryItem] = []
        for itm in self._store.values():
            if mtype is not None and itm.memory_type != mtype:
                continue
            if text and text not in (itm.content or "").lower():
                continue
            results.append(itm)
        return results

    def delete(self, item_id: str, transaction_id: str | None = None) -> bool:  # type: ignore[override]
        if transaction_id:
            self._tx_buffers.setdefault(transaction_id, []).append(("delete", item_id))
            return True
        return self._store.pop(item_id, None) is not None

    def begin_transaction(self) -> str:  # type: ignore[override]
        tx_id = f"tx-{len(self._tx_buffers)+1}"
        self._tx_buffers[tx_id] = []
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:  # type: ignore[override]
        ops = self._tx_buffers.pop(transaction_id, None)
        if ops is None:
            return False
        for op, payload in ops:
            if op == "store":
                item_id, item = payload
                self._store[item_id] = MemoryItem(id=item_id, **{k: v for k, v in item.__dict__.items() if k != "id"})
            elif op == "delete":
                item_id = payload
                self._store.pop(item_id, None)
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:  # type: ignore[override]
        return self._tx_buffers.pop(transaction_id, None) is not None

    def is_transaction_active(self, transaction_id: str) -> bool:  # type: ignore[override]
        return transaction_id in self._tx_buffers


class FakeVectorStore(VectorStore):
    """A simple in-memory vector store with cosine similarity for tests."""

    def __init__(self) -> None:
        self._vectors: Dict[str, MemoryVector] = {}
        self._next_id = 1

    def _gen_id(self) -> str:
        nid = str(self._next_id)
        self._next_id += 1
        return nid

    def store_vector(self, vector: MemoryVector) -> str:  # type: ignore[override]
        vid = vector.id or self._gen_id()
        self._vectors[vid] = MemoryVector(id=vid, content=vector.content, embedding=vector.embedding, metadata=vector.metadata)
        return vid

    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:  # type: ignore[override]
        return self._vectors.get(vector_id)

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryVector]:  # type: ignore[override]
        def cosine(a: List[float], b: List[float]) -> float:
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
            (cosine(vec.embedding, query_embedding), vec) for vec in self._vectors.values()
        ]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [vec for _score, vec in scored[: top_k or 5]]

    def delete_vector(self, vector_id: str) -> bool:  # type: ignore[override]
        return self._vectors.pop(vector_id, None) is not None

    def get_collection_stats(self) -> Dict[str, Any]:  # type: ignore[override]
        return {"count": len(self._vectors)}
