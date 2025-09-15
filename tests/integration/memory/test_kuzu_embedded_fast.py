"""Fast resource-enabled tests for Kuzu-backed stores."""

from __future__ import annotations

import os
import uuid

import pytest

try:  # pragma: no cover - guarded optional dependency
    import kuzu  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - optional dependency missing
    pytest.skip("Kuzu package not available", allow_module_level=True)

from devsynth.adapters import kuzu_memory_store
from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.domain.models.memory import MemoryItem, MemoryType

pytestmark = [pytest.mark.requires_resource("kuzu"), pytest.mark.fast]


def _kuzu_enabled() -> bool:
    """Return ``True`` when the Kuzu resource flag is opt-in."""

    return os.environ.get("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "true").lower() in {
        "true",
        "1",
        "yes",
    }


def test_kuzu_store_round_trip(tmp_path, monkeypatch):
    """Exercise :class:`KuzuStore` when the embedded backend is active. ReqID: N/A"""

    if not _kuzu_enabled():
        pytest.skip("Kuzu resource not enabled")

    monkeypatch.setenv("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "true")
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")

    store = KuzuStore(str(tmp_path))
    try:
        assert store._use_fallback is False

        item = MemoryItem(
            id=str(uuid.uuid4()),
            content="embedded round trip",
            memory_type=MemoryType.WORKING,
            metadata={"scope": "fast"},
        )
        store.store(item)

        retrieved = store.retrieve(item.id)
        assert retrieved is not None
        assert retrieved.content == "embedded round trip"
        assert store.get_latest_version(item.id) == 1

        assert store.delete(item.id) is True
        assert store.retrieve(item.id) is None
    finally:
        store.close()


def test_kuzu_memory_store_search_round_trip(tmp_path, monkeypatch):
    """Exercise :class:`KuzuMemoryStore` end-to-end with vector search. ReqID: N/A"""

    if not _kuzu_enabled():
        pytest.skip("Kuzu resource not enabled")

    monkeypatch.setenv("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "true")
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")
    # Ensure deterministic embeddings without a provider system.
    monkeypatch.setattr(kuzu_memory_store, "embedding_functions", None, raising=False)

    store = KuzuMemoryStore(
        persist_directory=str(tmp_path),
        use_provider_system=False,
        collection_name="fast_vectors",
    )
    try:
        assert hasattr(store, "_store")
        assert getattr(store._store, "_use_fallback", True) is False

        item = MemoryItem(
            id=str(uuid.uuid4()),
            content="kuzu memory search",
            memory_type=MemoryType.WORKING,
            metadata={"scope": "fast"},
        )
        stored_id = store.store(item)
        assert stored_id == item.id

        retrieved = store.retrieve(item.id)
        assert retrieved is not None
        assert retrieved.content == "kuzu memory search"
        assert retrieved.metadata.get("version") == 1

        results = store.search({"query": "kuzu memory", "top_k": 1})
        assert results and results[0].id == item.id

        assert store.delete(item.id) is True
    finally:
        store.cleanup()
