import importlib
import os

import pytest

# Minimal smoke tests for retrieval/memory backends. These are skipped by default
# unless DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true and the backend is importable.
# ReqID: B4


@pytest.mark.fast
@pytest.mark.requires_resource("chromadb")
def test_chromadb_importable_when_enabled(monkeypatch):
    if (
        os.environ.get("DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE", "false").lower()
        != "true"
    ):
        pytest.skip("chromadb not enabled via env flag")
    mod = importlib.import_module("chromadb")
    assert hasattr(mod, "__name__")


@pytest.mark.fast
@pytest.mark.requires_resource("faiss")
def test_faiss_importable_when_enabled(monkeypatch):
    if os.environ.get("DEVSYNTH_RESOURCE_FAISS_AVAILABLE", "false").lower() != "true":
        pytest.skip("faiss not enabled via env flag")
    mod = importlib.import_module("faiss")
    assert hasattr(mod, "__name__")


@pytest.mark.fast
@pytest.mark.requires_resource("kuzu")
def test_kuzu_importable_when_enabled(monkeypatch):
    if os.environ.get("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "false").lower() != "true":
        pytest.skip("kuzu not enabled via env flag")
    mod = importlib.import_module("kuzu")
    assert hasattr(mod, "__name__")


@pytest.mark.fast
@pytest.mark.requires_resource("tinydb")
def test_tinydb_importable_when_enabled(monkeypatch):
    if os.environ.get("DEVSYNTH_RESOURCE_TINYDB_AVAILABLE", "false").lower() != "true":
        pytest.skip("tinydb not enabled via env flag")
    mod = importlib.import_module("tinydb")
    assert hasattr(mod, "__name__")
