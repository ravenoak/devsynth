import sys
import types
from unittest.mock import MagicMock

import pytest

from tests.fixtures.resources import skip_module_if_backend_disabled

skip_module_if_backend_disabled("chromadb")

sys.modules.setdefault(
    "chromadb",
    types.SimpleNamespace(
        HttpClient=MagicMock(),
        PersistentClient=MagicMock(),
        EphemeralClient=MagicMock(),
    ),
)

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter

pytestmark = [pytest.mark.requires_resource("chromadb")]


@pytest.mark.medium
def test_memory_adapter_uses_ephemeral_client_when_no_network(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_NETWORK", "1")
    cfg = {
        "memory_store_type": "chromadb",
        "memory_file_path": str(tmp_path),
        "chromadb_host": "localhost",
        "chromadb_port": 9000,
        "enable_chromadb": True,
        "vector_store_enabled": False,
    }
    adapter = MemorySystemAdapter(config=cfg)
    chroma_mod = sys.modules["chromadb"]
    chroma_mod.HttpClient.assert_not_called()
    chroma_mod.EphemeralClient.assert_called_once_with()
    assert adapter.memory_store is not None
