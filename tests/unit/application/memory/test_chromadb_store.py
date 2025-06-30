"""Tests for the ChromaDBStore fallback logic and logging."""

import os

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("chromadb")

if os.environ.get("ENABLE_CHROMADB", "false").lower() in {"0", "false", "no"}:
    pytest.skip("ChromaDB feature not enabled", allow_module_level=True)

from devsynth.application.memory.chromadb_store import ChromaDBStore
from devsynth.domain.models.memory import MemoryItem


pytestmark = pytest.mark.requires_resource("chromadb")


@patch(
    "devsynth.application.memory.chromadb_store.chromadb.EphemeralClient",
    autospec=True,
)
def test_init_logs_error_on_bad_fallback(
    mock_client_cls, tmp_path, caplog, monkeypatch
):
    """Initialization logs an error when fallback file is invalid."""

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("ENABLE_CHROMADB", "1")
    (tmp_path / "fallback_store.json").write_text("{ bad json")

    mock_client = MagicMock()
    mock_client.get_collection.return_value = MagicMock()
    mock_client_cls.return_value = mock_client

    caplog.set_level(logging.WARNING)
    store = ChromaDBStore(str(tmp_path))

    assert not store._use_fallback
    assert any("Failed to load fallback store" in rec.message for rec in caplog.records)


@patch(
    "devsynth.application.memory.chromadb_store.chromadb.EphemeralClient",
    autospec=True,
)
def test_init_fallback_when_collection_creation_fails(
    mock_client_cls, tmp_path, caplog, monkeypatch
):
    """Fallback mode is enabled and errors are logged when collections fail."""

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("ENABLE_CHROMADB", "1")
    (tmp_path / "fallback_store.json").write_text("{ bad json")

    mock_client = MagicMock()
    mock_client.get_collection.side_effect = Exception("get")
    mock_client.create_collection.side_effect = Exception("create")
    mock_client_cls.return_value = mock_client

    caplog.set_level(logging.WARNING)
    store = ChromaDBStore(str(tmp_path))

    assert store._use_fallback
    messages = [rec.message for rec in caplog.records]
    assert any("Failed to initialize ChromaDB collection" in m for m in messages)
    assert any("Failed to load fallback store" in m for m in messages)


@patch(
    "devsynth.application.memory.chromadb_store.chromadb.EphemeralClient",
    autospec=True,
)
def test_save_fallback_logs_error(mock_client_cls, tmp_path, caplog, monkeypatch):
    """Errors during saving fallback store are logged."""

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("ENABLE_CHROMADB", "1")
    mock_client = MagicMock()
    mock_client.get_collection.return_value = MagicMock()
    mock_client_cls.return_value = mock_client

    store = ChromaDBStore(str(tmp_path))
    store._use_fallback = True
    store._store["x"] = MemoryItem(
        id="x", content="c", memory_type=None, metadata={}, created_at=datetime.now()
    )

    caplog.set_level(logging.ERROR)
    with patch("builtins.open", side_effect=IOError("fail")):
        store._save_fallback()

    assert any("Failed to save fallback store" in rec.message for rec in caplog.records)
