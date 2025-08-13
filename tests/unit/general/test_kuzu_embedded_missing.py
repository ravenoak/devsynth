import importlib
from types import SimpleNamespace

import pytest

from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore


@pytest.mark.fast
def test_ephemeral_kuzu_store_initialises_without_kuzu_embedded(monkeypatch):
    """KuzuMemoryStore should initialise even if settings lack ``kuzu_embedded``."""
    pytest.importorskip("kuzu")

    settings_module = importlib.import_module("devsynth.config.settings")

    # Simulate an older settings module without the ``kuzu_embedded`` attribute
    monkeypatch.delattr(settings_module, "kuzu_embedded", raising=False)

    def dummy_settings(*_args, **_kwargs):
        return SimpleNamespace(kuzu_db_path=None)

    monkeypatch.setattr(settings_module, "get_settings", dummy_settings)

    store = KuzuMemoryStore.create_ephemeral()
    assert store is not None
    store.cleanup()
