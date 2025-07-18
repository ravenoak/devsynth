import types
import sys
from unittest.mock import MagicMock
import pytest

sys.modules.setdefault('chromadb', types.SimpleNamespace(HttpClient=MagicMock(), PersistentClient=MagicMock(), EphemeralClient=MagicMock()))

from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter


def test_memory_adapter_uses_http_client_when_host_specified(tmp_path, monkeypatch):
    cfg = {
        'memory_store_type': 'chromadb',
        'memory_file_path': str(tmp_path),
        'chromadb_host': 'localhost',
        'chromadb_port': 9000,
        'enable_chromadb': True,
    }
    adapter = MemorySystemAdapter(config=cfg)
    chroma_mod = sys.modules['chromadb']
    chroma_mod.HttpClient.assert_called_once_with(host='localhost', port=9000)
    assert adapter.memory_store is not None

