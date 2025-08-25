import sys
import types

import pytest


@pytest.fixture
def ephemeral_kuzu_store():
    """Yield an ephemeral :class:`KuzuMemoryStore` for tests."""
    sys.modules.setdefault("kuzu", types.ModuleType("kuzu"))
    from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore

    store = KuzuMemoryStore.create_ephemeral()
    try:
        yield store
    finally:
        store.cleanup()


@pytest.fixture
def temporary_kuzu_config(tmp_path, monkeypatch):
    """Set temporary Kuzu configuration via environment variables."""
    db_path = tmp_path / "kuzu_db"
    monkeypatch.setenv("DEVSYNTH_KUZU_DB_PATH", str(db_path))
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")
    yield str(db_path)
