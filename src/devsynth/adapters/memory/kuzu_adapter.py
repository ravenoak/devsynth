"""Simple vector store used as a fallback when KuzuDB is unavailable.

The adapter stores vectors in memory but also persists them to disk so that
subsequent adapter instances created with the same ``persist_directory`` can
retrieve previously stored vectors.  This mirrors the behaviour of other vector
stores used throughout the codebase and keeps the tests deterministic.
"""

from __future__ import annotations

import os
import json
import uuid
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None

from devsynth.domain.interfaces.memory import VectorStore
from devsynth.domain.models.memory import MemoryVector
from devsynth.logging_setup import DevSynthLogger
from devsynth.config.settings import ensure_path_exists

logger = DevSynthLogger(__name__)


class KuzuAdapter(VectorStore):
    """Vector store interface mimicking ``ChromaDBAdapter``."""

    def __init__(
        self, persist_directory: str, collection_name: str = "devsynth_vectors"
    ) -> None:
        self.persist_directory = os.path.expanduser(persist_directory)
        self.collection_name = collection_name
        # Ensure the directory exists even when ``ensure_path_exists`` is
        # patched to no-op during tests.  ``os.makedirs`` is safe to call on an
        # existing path and avoids failures when persisting vectors.
        ensure_path_exists(self.persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        self._data_file = os.path.join(
            self.persist_directory, f"{collection_name}.json"
        )
        self._store: Dict[str, MemoryVector] = {}
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        """Load persisted vectors from disk if available."""
        if not os.path.exists(self._data_file):
            return
        try:
            with open(self._data_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load persisted vectors: %s", exc)
            self._store = {}
            return

        for item in raw:
            try:
                vec = MemoryVector(**item)
                self._store[vec.id] = vec
            except Exception:  # pragma: no cover - defensive
                logger.warning("Invalid vector record skipped: %s", item)

    def _persist(self) -> None:
        """Persist the vector store to disk."""
        try:
            temp_file = f"{self._data_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(
                    [
                        {
                            "id": v.id,
                            "content": v.content,
                            "embedding": v.embedding,
                            "metadata": v.metadata,
                        }
                        for v in self._store.values()
                    ],
                    f,
                )
            os.replace(temp_file, self._data_file)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to persist vectors: %s", exc)

    def store_vector(self, vector: MemoryVector) -> str:
        if not vector.id:
            vector.id = str(uuid.uuid4())
        self._store[vector.id] = vector
        self._persist()
        return vector.id

    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        return self._store.get(vector_id)

    def similarity_search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[MemoryVector]:
        """Return vectors most similar to the query embedding."""
        results = []
        if np is not None:
            q = np.array(query_embedding, dtype=float)
            for vec in self._store.values():
                try:
                    dist = float(
                        np.linalg.norm(q - np.array(vec.embedding, dtype=float))
                    )
                except ValueError:
                    # Skip vectors with mismatched dimensions
                    continue
                results.append((dist, vec))
        else:  # pragma: no cover - extremely rare fallback

            def _distance(a: List[float], b: List[float]) -> float:
                return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

            for vec in self._store.values():
                if len(vec.embedding) != len(query_embedding):
                    continue
                dist = _distance(query_embedding, vec.embedding)
                results.append((dist, vec))
        results.sort(key=lambda x: x[0])
        return [v for _, v in results[:top_k]]

    def delete_vector(self, vector_id: str) -> bool:
        existed = self._store.pop(vector_id, None) is not None
        if existed:
            self._persist()
        return existed

    def get_all_vectors(self) -> List[MemoryVector]:
        """Return all stored vectors."""

        return list(self._store.values())

    def get_collection_stats(self) -> Dict[str, Any]:
        dim = 0
        if self._store:
            dim = len(next(iter(self._store.values())).embedding)
        return {
            "collection_name": self.collection_name,
            "num_vectors": len(self._store),
            "embedding_dimension": dim,
            "persist_directory": self.persist_directory,
        }
