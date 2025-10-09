import os
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.conftest import is_resource_available
from tests.fixtures.resources import (
    OPTIONAL_BACKEND_REQUIREMENTS,
    backend_import_reason,
    backend_skip_reason,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("kuzu")

_KUZU_EXTRAS = tuple(OPTIONAL_BACKEND_REQUIREMENTS["kuzu"]["extras"])

pytest.importorskip("kuzu", reason=backend_import_reason("kuzu", _KUZU_EXTRAS))

if not is_resource_available("kuzu"):
    pytest.skip(
        backend_skip_reason("kuzu", _KUZU_EXTRAS),
        allow_module_level=True,
    )

from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.domain.models.memory import MemoryItem, MemoryType

pytestmark = [pytest.mark.requires_resource("kuzu")]

# These integration tests interact with multiple storage backends


@pytest.fixture
def no_kuzu(monkeypatch):
    """Ensure tests run without the real ``kuzu`` dependency."""
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")
    monkeypatch.delitem(sys.modules, "kuzu", raising=False)
    monkeypatch.setattr(KuzuMemoryStore, "__abstractmethods__", frozenset())
    monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())


@pytest.fixture
def fake_kuzu(monkeypatch):
    """Provide a minimal stub of the kuzu package."""

    class Database:
        def __init__(self, path):
            pass

    class Connection:
        def __init__(self, db):
            pass

        def execute(self, *args, **kwargs):
            return None

    fake = types.SimpleNamespace(Database=Database, Connection=Connection)
    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "true")
    monkeypatch.setitem(sys.modules, "kuzu", fake)
    monkeypatch.setattr(KuzuMemoryStore, "__abstractmethods__", frozenset())
    monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())
    return fake


@pytest.fixture
def kuzu_store(no_kuzu):
    store = KuzuMemoryStore.create_ephemeral()
    try:
        yield store
    finally:
        store.cleanup()


@pytest.fixture
def kuzu_store_embedded(fake_kuzu):
    store = KuzuMemoryStore.create_ephemeral()
    try:
        yield store
    finally:
        store.cleanup()


@pytest.fixture(autouse=True)
def mock_embed():
    with (
        patch(
            "devsynth.adapters.kuzu_memory_store.embed", return_value=[[0.1, 0.2, 0.3]]
        ),
        patch(
            "devsynth.adapters.kuzu_memory_store.embedding_functions",
            types.SimpleNamespace(
                DefaultEmbeddingFunction=lambda: (lambda x: [0.0] * 5)
            ),
        ),
    ):
        yield


@pytest.mark.parametrize("store_fixture", ["kuzu_store", "kuzu_store_embedded"])
@pytest.mark.medium
def test_kuzu_memory_vector_integration_succeeds(request, store_fixture):
    store = request.getfixturevalue(store_fixture)
    config = {
        "memory_store_type": "kuzu",
        "memory_file_path": store.persist_directory,
        "vector_store_enabled": True,
    }
    adapter = MemorySystemAdapter(config=config)
    memory_item = MemoryItem(
        id="item1",
        content="hello world",
        memory_type=MemoryType.LONG_TERM,
        metadata={},
    )
    item_id = adapter.memory_store.store(memory_item)
    results = adapter.vector_store.similarity_search([0.1, 0.2, 0.3], top_k=1)
    assert results
    assert results[0].id == item_id


@pytest.mark.parametrize("store_fixture", ["kuzu_store", "kuzu_store_embedded"])
@pytest.mark.medium
def test_create_for_testing_with_kuzu(request, store_fixture):
    store = request.getfixturevalue(store_fixture)
    adapter = MemorySystemAdapter.create_for_testing(
        storage_type="kuzu", memory_path=store.persist_directory
    )
    assert adapter.storage_type == "kuzu"
    assert adapter.memory_store is not None
    assert adapter.context_manager is not None
    assert adapter.vector_store is not None


@pytest.mark.medium
def test_ephemeral_store_cleanup(no_kuzu):
    store = KuzuMemoryStore.create_ephemeral()
    path = store.persist_directory
    assert os.path.exists(path)
    assert store._store._use_fallback
    store.cleanup()
    assert not os.path.exists(path)


@pytest.mark.medium
def test_ephemeral_store_startup_respects_env(monkeypatch, no_kuzu):
    """Explicitly disabling embedded mode still allows startup."""
    from devsynth.config import settings as settings_module

    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "false")
    settings_module.get_settings(reload=True)

    store = KuzuMemoryStore.create_ephemeral()
    try:
        assert store._store._use_fallback
    finally:
        store.cleanup()


@pytest.mark.medium
def test_configured_path_usage(fake_kuzu):
    """Store initialises at configured path when provided."""
    project_dir = Path(os.environ["DEVSYNTH_PROJECT_DIR"])
    config_path = project_dir / "configured"
    config_path.mkdir()
    store = KuzuMemoryStore(str(config_path))
    try:
        assert store.persist_directory == str(config_path)
    finally:
        store.cleanup()


@pytest.mark.medium
def test_provider_fallback_on_empty_embedding(tmp_path, no_kuzu):
    with patch("devsynth.adapters.kuzu_memory_store.embed", return_value=[[]]):
        store = KuzuMemoryStore(str(tmp_path))
        assert store._store._use_fallback
        emb = store._get_embedding("hello")
        assert emb == store.embedder("hello")


@pytest.mark.medium
def test_create_ephemeral_embedded_mode(kuzu_store_embedded):
    assert not kuzu_store_embedded._store._use_fallback


@pytest.mark.parametrize("embedded", [True, False])
@pytest.mark.medium
def test_kuzu_embedded_env_setting(monkeypatch, embedded):
    from devsynth.config import settings as settings_module

    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", str(embedded).lower())
    s = settings_module.get_settings(reload=True)
    assert s.kuzu_embedded is embedded
    assert s["kuzu_embedded"] is embedded


@pytest.mark.medium
def test_kuzu_embedded_module_export(monkeypatch):
    """settings.kuzu_embedded should mirror the environment."""
    from devsynth.config import settings as settings_module

    monkeypatch.setenv("DEVSYNTH_KUZU_EMBEDDED", "false")
    settings_module.get_settings(reload=True)
    try:
        assert settings_module.kuzu_embedded is False
    finally:
        # Reset to default to avoid leaking state
        settings_module.get_settings(
            reload=True, kuzu_embedded=settings_module.DEFAULT_KUZU_EMBEDDED
        )


@pytest.mark.medium
def test_kuzu_adapter_ephemeral_cleanup(monkeypatch, tmp_path, no_kuzu):
    from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
    from devsynth.config import settings as settings_module

    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    settings_module.get_settings(reload=True)
    created: list[str] = []

    real_mkdtemp = tempfile.mkdtemp

    def fake_mkdtemp(prefix: str):
        d = real_mkdtemp(prefix=prefix)
        created.append(d)
        return d

    monkeypatch.setattr(tempfile, "mkdtemp", fake_mkdtemp)

    adapter = KuzuAdapter.create_ephemeral()
    original_dir = created[0]
    redirected_dir = adapter.persist_directory
    adapter.cleanup()

    assert not os.path.exists(original_dir)
    assert not os.path.exists(redirected_dir)
