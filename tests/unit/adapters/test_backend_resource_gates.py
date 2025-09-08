import os
import pytest

# Speed marker discipline: exactly one speed marker per test


@pytest.mark.fast
@pytest.mark.requires_resource("CHROMADB")
def test_chromadb_adapter_imports() -> None:
    """
    ReqID: FR-09; Plan Phase 2 Section 4.2
    Enable locally with:
      poetry install --with dev --extras chromadb
      export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
    """
    mod = __import__("devsynth.adapters.chromadb_memory_store", fromlist=["ChromaDBMemoryStore"])  # noqa: S401
    assert hasattr(mod, "ChromaDBMemoryStore")


@pytest.mark.fast
@pytest.mark.requires_resource("KUZU")
def test_kuzu_adapter_imports() -> None:
    """
    Enable locally with (simplest path uses kuzu extra if provided):
      poetry install --with dev --extras retrieval
      export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true
    """
    mod = __import__("devsynth.adapters.kuzu_memory_store", fromlist=["KuzuMemoryStore"])  # noqa: S401
    assert hasattr(mod, "KuzuMemoryStore")


@pytest.mark.fast
@pytest.mark.requires_resource("FAISS")
def test_faiss_store_imports_and_minimal() -> None:
    """
    Minimal smoke: verify FAISS import and store class import path.
    Enable locally with:
      poetry install --with dev --extras retrieval
      export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true
    """
    # External dependency import (skips if not installed per resource fixture)
    faiss = pytest.importorskip("faiss")
    assert hasattr(faiss, "IndexFlatL2")

    # Our store is under application.memory.faiss_store
    mod = __import__("devsynth.application.memory.faiss_store", fromlist=["FAISSStore"])  # noqa: S401
    assert hasattr(mod, "FAISSStore")
