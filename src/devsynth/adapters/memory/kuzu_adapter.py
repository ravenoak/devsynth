"""Simple vector store used as a fallback when KuzuDB is unavailable.

The adapter stores vectors in memory but also persists them to disk so that
subsequent adapter instances created with the same ``persist_directory`` can
retrieve previously stored vectors.  This mirrors the behaviour of other vector
stores used throughout the codebase and keeps the tests deterministic.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None

from devsynth.application.memory.dto import VectorStoreStats

# Import settings module so ``ensure_path_exists`` can be monkeypatched
from devsynth.config import settings as settings_module
from devsynth.domain.interfaces.memory import VectorStore
from devsynth.domain.models.memory import MemoryVector
from devsynth.exceptions import MemoryStoreError
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class KuzuAdapter(VectorStore[MemoryVector]):
    """Vector store interface mimicking ``ChromaDBAdapter``."""

    def __init__(
        self, persist_directory: str, collection_name: str = "devsynth_vectors"
    ) -> None:
        # Normalise and redirect the persistence path so tests can run in an
        # isolated filesystem.  ``ensure_path_exists`` may return a different
        # path when test isolation is active; use that value for all subsequent
        # operations.
        self.persist_directory = os.path.abspath(os.path.expanduser(persist_directory))
        self.collection_name = collection_name
        self.persist_directory = settings_module.ensure_path_exists(
            self.persist_directory
        )
        os.makedirs(self.persist_directory, exist_ok=True)
        self._data_file = os.path.join(
            self.persist_directory, f"{collection_name}.json"
        )
        self._store: dict[str, MemoryVector] = {}
        # Track snapshots for basic transaction support.  Each transaction
        # ID maps to a complete copy of the current store which can be
        # restored if a rollback is requested.
        self._snapshots: dict[str, dict[str, MemoryVector]] = {}
        # Track temporary directories created via ``create_ephemeral`` so they
        # can be removed in :meth:`cleanup`.
        self._temp_dir: str | None = None
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        """Load persisted vectors from disk if available."""
        if not os.path.exists(self._data_file):
            return
        try:
            with open(self._data_file, encoding="utf-8") as f:
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

    def flush(self) -> None:
        """Flush pending vector updates to disk."""

        self._persist()

    def store_vector(self, vector: MemoryVector) -> str:
        if not vector.id:
            vector.id = str(uuid.uuid4())
        self._store[vector.id] = vector
        if not self._snapshots:
            self._persist()
        return vector.id

    def retrieve_vector(self, vector_id: str) -> MemoryVector | None:
        return self._store.get(vector_id)

    def similarity_search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[MemoryVector]:
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

            def _distance(a: list[float], b: list[float]) -> float:
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
        if existed and not self._snapshots:
            self._persist()
        return existed

    def get_all_vectors(self) -> list[MemoryVector]:
        """Return all stored vectors."""

        return list(self._store.values())

    def get_collection_stats(self) -> VectorStoreStats:
        dim = 0
        if self._store:
            dim = len(next(iter(self._store.values())).embedding)
        return {
            "collection_name": self.collection_name,
            "vector_count": len(self._store),
            "embedding_dimensions": dim,
            "persist_directory": self.persist_directory,
        }

    # ------------------------------------------------------------------
    # transactional helpers -------------------------------------------------

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """Begin a new transaction and return its identifier."""

        tx_id = transaction_id or str(uuid.uuid4())
        if tx_id in self._snapshots:
            raise MemoryStoreError(f"Transaction {tx_id} already active")
        self._snapshots[tx_id] = {
            vid: deepcopy(vec) for vid, vec in self._store.items()
        }
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a previously started transaction."""

        if transaction_id not in self._snapshots:
            raise MemoryStoreError(
                f"Commit requested for unknown transaction {transaction_id}"
            )
        self._snapshots.pop(transaction_id, None)
        self._persist()
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction to its starting snapshot."""

        snapshot = self._snapshots.pop(transaction_id, None)
        if snapshot is None:
            raise MemoryStoreError(
                f"Rollback requested for unknown transaction {transaction_id}"
            )
        self._store = {vid: deepcopy(vec) for vid, vec in snapshot.items()}
        self._persist()
        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if ``transaction_id`` is active."""

        return transaction_id in self._snapshots

    @contextmanager
    def transaction(self, transaction_id: str | None = None):
        """Context manager providing transactional semantics."""

        tx_id = self.begin_transaction(transaction_id)
        try:
            yield tx_id
        except Exception:
            self.rollback_transaction(tx_id)
            raise
        else:
            self.commit_transaction(tx_id)

    # ------------------------------------------------------------------
    @classmethod
    def create_ephemeral(
        cls, collection_name: str = "devsynth_vectors"
    ) -> KuzuAdapter:
        """Create an ephemeral adapter backed by a temporary directory.

        The directory is created using :func:`tempfile.mkdtemp` and tracked so
        that :meth:`cleanup` can remove it after tests complete.
        """

        temp_dir = tempfile.mkdtemp(prefix="kuzu_adapter_")
        adapter = cls(temp_dir, collection_name)
        if adapter.persist_directory != temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        adapter._temp_dir = adapter.persist_directory
        return adapter

    def cleanup(self) -> None:
        """Remove any temporary directory created by ``create_ephemeral``."""

        if not self._temp_dir:
            return
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Failed to remove temporary directory %s: %s", self._temp_dir, exc
            )
        finally:
            self._temp_dir = None
