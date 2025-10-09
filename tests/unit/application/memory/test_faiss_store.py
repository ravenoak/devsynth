"""Unit tests for the FAISS-backed vector store."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from datetime import datetime

import numpy as np
import pytest

from devsynth.application.memory.faiss_store import FAISSStore  # noqa: E402
from devsynth.domain.models.memory import MemoryVector  # noqa: E402


def _build_vector(
    content: str,
    embedding: Iterable[float],
    *,
    metadata: dict[str, object] | None = None,
    created_at: datetime | None = None,
) -> MemoryVector:
    """Create a MemoryVector with a generated identifier."""

    return MemoryVector(
        id="",
        content=content,
        embedding=list(embedding),
        metadata=metadata,
        created_at=created_at,
    )


@pytest.mark.requires_resource("faiss")
@pytest.mark.fast
def test_store_and_retrieve_round_trip_preserves_metadata(tmp_path) -> None:
    """ReqID: N/A – Stored vectors persist embeddings and metadata."""

    store = FAISSStore(str(tmp_path))
    created_at = datetime.now()
    vector = _build_vector(
        "vector-a",
        [0.05, 0.1, 0.15, 0.2],
        metadata={"created_at": created_at, "topic": "faiss"},
        created_at=created_at,
    )

    vector_id = store.store_vector(vector)
    assert store.dimension == len(vector.embedding)

    metadata_path = os.path.join(str(tmp_path), "metadata.json")
    with open(metadata_path, encoding="utf-8") as fh:
        serialized = json.load(fh)

    assert serialized[vector_id]["metadata"]["created_at"] == created_at.isoformat()

    retrieved = store.retrieve_vector(vector_id)
    assert retrieved is not None
    assert retrieved.id == vector_id
    assert np.allclose(retrieved.item.embedding, vector.embedding)
    assert retrieved.metadata is not None
    assert retrieved.metadata["created_at"] == created_at
    assert retrieved.metadata["topic"] == "faiss"
    assert store.token_count > 0


@pytest.mark.requires_resource("faiss")
@pytest.mark.fast
def test_transaction_commit_persists_changes(tmp_path) -> None:
    """ReqID: N/A – Transaction commits flush new vectors to disk."""

    base_path = str(tmp_path)
    store = FAISSStore(base_path)
    vector = _build_vector("vector-b", [0.2, 0.1, 0.0, -0.1])

    with store.transaction():
        committed_id = store.store_vector(vector)

    reopened = FAISSStore(base_path)
    retrieved = reopened.retrieve_vector(committed_id)
    assert retrieved is not None
    assert retrieved.content == "vector-b"


@pytest.mark.requires_resource("faiss")
@pytest.mark.fast
def test_transaction_rollback_restores_snapshot(tmp_path) -> None:
    """ReqID: N/A – Rollbacks revert the index and metadata state."""

    base_path = str(tmp_path)
    store = FAISSStore(base_path)
    baseline_id = store.store_vector(_build_vector("baseline", [0.0, 0.1, 0.2, 0.3]))

    staged_ids: list[str] = []
    with pytest.raises(RuntimeError, match="force rollback"):
        with store.transaction():
            staged_id = store.store_vector(
                _build_vector("transient", [0.3, 0.2, 0.1, 0.0])
            )
            staged_ids.append(staged_id)
            raise RuntimeError("force rollback")

    assert staged_ids, "transaction should have produced a staged id"

    reopened = FAISSStore(base_path)
    assert reopened.retrieve_vector(baseline_id) is not None
    assert reopened.retrieve_vector(staged_ids[0]) is None

    with open(os.path.join(base_path, "metadata.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    assert baseline_id in data
    assert staged_ids[0] not in data


@pytest.mark.requires_resource("faiss")
@pytest.mark.fast
def test_similarity_search_and_stats_ignore_deleted_vectors(tmp_path) -> None:
    """ReqID: N/A – Similarity search ignores deleted vectors.

    Stats stay accurate for active entries.
    """

    store = FAISSStore(str(tmp_path))
    embeddings = [
        [0.1, 0.0, 0.0, 0.0],
        [0.0, 0.1, 0.0, 0.0],
        [0.0, 0.0, 0.1, 0.0],
    ]
    ids = [
        store.store_vector(_build_vector(f"vector-{idx}", emb))
        for idx, emb in enumerate(embeddings, start=1)
    ]

    assert store.delete_vector(ids[1]) is True

    results = store.similarity_search(embeddings[0], top_k=5)
    result_ids = [record.id for record in results]
    assert all(
        record.similarity is None or 0.0 <= record.similarity <= 1.0
        for record in results
    )
    assert ids[0] in result_ids
    assert ids[1] not in result_ids

    stats = store.get_collection_stats()
    assert stats["vector_count"] == 2

    active_ids = {vec.id for vec in store.get_all_vectors()}
    assert active_ids == {ids[0], ids[2]}
