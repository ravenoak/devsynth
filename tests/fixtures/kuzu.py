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

