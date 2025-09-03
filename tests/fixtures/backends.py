"""
Backend test fixtures for temporary, isolated stores (chromadb/faiss/kuzu/duckdb/lmdb/tinydb/rdflib).

All fixtures are lightweight and guarded implicitly by requires_resource("<name>")
markers on tests. They only attempt to import the backend package when a test
requests the fixture, and will skip cleanly if the package is not installed or
if the resource is disabled via DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=false.

These fixtures help standardize minimal temporary stores per docs/tasks.md #25.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Optional

import pytest

from tests.conftest import is_resource_available


# --------------------------- ChromaDB -----------------------------------------
@pytest.fixture
def chromadb_temp_path(tmp_path: Path) -> Path:
    """Provide a temporary directory for ChromaDB persistent client usage.

    Tests may create a Client(persist_directory=str(chromadb_temp_path)).
    Guard usage with @pytest.mark.requires_resource("chromadb").
    """
    return tmp_path / "chromadb_store"


@pytest.fixture
def chromadb_client(chromadb_temp_path: Path):
    """Return a minimal ChromaDB client if chromadb is available, else skip.

    Designed to be optional; many tests prefer their own client setup.
    """
    if not is_resource_available("chromadb"):
        pytest.skip("Resource 'chromadb' not available")
    try:  # pragma: no cover - simple import check
        import chromadb

        return chromadb.PersistentClient(path=str(chromadb_temp_path))
    except Exception as e:  # pragma: no cover
        pytest.skip(f"chromadb not usable in this environment: {e}")


# --------------------------- FAISS --------------------------------------------
@pytest.fixture
def faiss_index():
    """Return a minimal in-memory FAISS index (IndexFlatL2) if available.

    Requires @pytest.mark.requires_resource("faiss").
    """
    if not is_resource_available("faiss"):
        pytest.skip("Resource 'faiss' not available")
    try:  # pragma: no cover - import check only
        import faiss  # type: ignore

        return faiss.IndexFlatL2(8)
    except Exception as e:  # pragma: no cover
        pytest.skip(f"faiss not usable in this environment: {e}")


# --------------------------- Kuzu ---------------------------------------------
@pytest.fixture
def kuzu_db_path(tmp_path: Path) -> Path:
    """Provide a temporary directory for a Kuzu database.

    Tests can create the DB using the returned path when kuzu is available.
    Guard with @pytest.mark.requires_resource("kuzu").
    """
    return tmp_path / "kuzu_db"


# --------------------------- DuckDB -------------------------------------------
@pytest.fixture
def duckdb_path(tmp_path: Path) -> Path:
    """Provide a path for a temporary DuckDB database file."""
    return tmp_path / "devsynth.duckdb"


@pytest.fixture
def duckdb_connection(duckdb_path: Path):
    if not is_resource_available("duckdb"):
        pytest.skip("Resource 'duckdb' not available")
    try:  # pragma: no cover - import check only
        import duckdb  # type: ignore

        return duckdb.connect(str(duckdb_path))
    except Exception as e:  # pragma: no cover
        pytest.skip(f"duckdb not usable in this environment: {e}")


# --------------------------- LMDB ---------------------------------------------
@pytest.fixture
def lmdb_env(tmp_path: Path):
    """Return a minimal LMDB environment under a temporary directory."""
    if not is_resource_available("lmdb"):
        pytest.skip("Resource 'lmdb' not available")
    try:  # pragma: no cover - import check only
        import lmdb  # type: ignore

        env_path = tmp_path / "lmdb_env"
        env_path.mkdir(exist_ok=True)
        return lmdb.open(str(env_path), map_size=8 * 1024 * 1024)  # 8MB
    except Exception as e:  # pragma: no cover
        pytest.skip(f"lmdb not usable in this environment: {e}")


# --------------------------- TinyDB -------------------------------------------
@pytest.fixture
def tinydb_path(tmp_path: Path) -> Path:
    """Provide a path for a temporary TinyDB JSON store."""
    return tmp_path / "tinydb.json"


# --------------------------- RDFLib -------------------------------------------
@pytest.fixture
def rdflib_graph():
    """Return an empty rdflib.Graph if available, else skip."""
    if not is_resource_available("rdflib"):
        pytest.skip("Resource 'rdflib' not available")
    try:  # pragma: no cover - import check only
        import rdflib  # type: ignore

        return rdflib.Graph()
    except Exception as e:  # pragma: no cover
        pytest.skip(f"rdflib not usable in this environment: {e}")
