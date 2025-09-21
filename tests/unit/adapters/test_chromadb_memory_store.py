import os
import uuid

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType


def _require_resource(resource: str) -> None:
    """Skip when an optional backend resource is explicitly disabled."""

    env_name = f"DEVSYNTH_RESOURCE_{resource.upper()}_AVAILABLE"
    if os.environ.get(env_name, "true").lower() == "false":
        pytest.skip(f"Resource '{resource}' disabled via {env_name}")


@pytest.mark.requires_resource("chromadb")
@pytest.mark.fast
def test_store_and_retrieve_roundtrip(monkeypatch, tmp_path):
    """Store and retrieve using ChromaDBMemoryStore. ReqID: N/A"""
    chromadb = pytest.importorskip("chromadb")
    _require_resource("chromadb")

    try:
        from devsynth.adapters import chromadb_memory_store
    except ImportError as exc:  # pragma: no cover - optional dependency missing
        pytest.skip(f"Optional memory store dependency missing: {exc}")

    class DummyEF:
        def __call__(self, texts):
            if isinstance(texts, str):
                return [0.0, 0.0, 0.0]
            return [[0.0, 0.0, 0.0] for _ in texts]

    monkeypatch.setattr(chromadb_memory_store, "ClientAPI", chromadb.Client)
    monkeypatch.setattr(
        chromadb_memory_store.embedding_functions,
        "DefaultEmbeddingFunction",
        lambda: DummyEF(),
    )
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    store = chromadb_memory_store.ChromaDBMemoryStore(
        persist_directory=str(tmp_path),
        use_provider_system=False,
    )

    item = MemoryItem(
        id=str(uuid.uuid4()),
        content="hello",
        memory_type=MemoryType.WORKING,
        metadata={"note": "test"},
    )

    store.store(item)
    retrieved = store.retrieve(item.id)
    assert retrieved.content == "hello"

    assert store.delete(item.id)
    with pytest.raises(RuntimeError):
        store.retrieve(item.id)
