"""Tests for the ``KuzuAdapter`` vector store."""

import tempfile
import shutil
from devsynth.domain.models.memory import MemoryVector
from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter


def test_store_and_retrieve_vector_succeeds():
    """Test that store and retrieve vector succeeds.

    ReqID: N/A"""
    temp_dir = tempfile.mkdtemp()
    adapter = KuzuAdapter(temp_dir)
    vec = MemoryVector(id="v1", content="text", embedding=[0.1, 0.2, 0.3])
    adapter.store_vector(vec)
    retrieved = adapter.retrieve_vector("v1")
    shutil.rmtree(temp_dir)
    assert retrieved is not None
    assert retrieved.id == "v1"


def test_similarity_search_succeeds():
    """Test that similarity search succeeds.

    ReqID: N/A"""
    temp_dir = tempfile.mkdtemp()
    adapter = KuzuAdapter(temp_dir)
    vectors = [
        MemoryVector(id=f"v{i}", content="x", embedding=[i, i, i]) for i in range(3)
    ]
    for v in vectors:
        adapter.store_vector(v)
    res = adapter.similarity_search([0.0, 0.0, 0.0], top_k=2)
    shutil.rmtree(temp_dir)
    assert len(res) == 2
    assert res[0].id == "v0"


def test_persistence_between_instances_succeeds():
    """Vectors should persist to disk across adapter instances."""
    temp_dir = tempfile.mkdtemp()
    adapter1 = KuzuAdapter(temp_dir)
    adapter1.store_vector(
        MemoryVector(id="v1", content="text", embedding=[0.1, 0.2, 0.3])
    )
    # Recreate adapter to trigger loading from disk
    adapter2 = KuzuAdapter(temp_dir)
    retrieved = adapter2.retrieve_vector("v1")
    shutil.rmtree(temp_dir)
    assert retrieved is not None


def test_similarity_search_without_numpy_succeeds(monkeypatch, tmp_path):
    """Fallback distance calculation should work without NumPy."""
    import importlib
    import devsynth.adapters.memory.kuzu_adapter as kuzu_adapter

    monkeypatch.setattr(kuzu_adapter, "np", None)
    importlib.reload(kuzu_adapter)

    adapter = kuzu_adapter.KuzuAdapter(str(tmp_path))
    vectors = [
        MemoryVector(id=f"v{i}", content="x", embedding=[float(i)] * 3)
        for i in range(3)
    ]
    for v in vectors:
        adapter.store_vector(v)
    res = adapter.similarity_search([0.0, 0.0, 0.0], top_k=1)
    assert res[0].id == "v0"
