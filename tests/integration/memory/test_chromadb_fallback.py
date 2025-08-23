import pytest

pytest.importorskip("chromadb")

ChromaDBAdapter = pytest.importorskip(
    "devsynth.adapters.memory.chroma_db_adapter"
).ChromaDBAdapter
from devsynth.domain.models.memory import MemoryVector

pytestmark = [pytest.mark.requires_resource("chromadb")]


def test_chromadb_falls_back_to_ephemeral_client(tmp_path, monkeypatch):
    """Adapter should fall back to an in-memory client when LMDB is missing. ReqID: FR-60"""
    ef = pytest.importorskip("chromadb.utils.embedding_functions")
    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5))

    chromadb = pytest.importorskip("chromadb")

    def raise_module_error(*args, **kwargs):
        raise ModuleNotFoundError("lmdb")

    monkeypatch.setattr(chromadb, "PersistentClient", raise_module_error)

    used = {}
    original_ephemeral = chromadb.EphemeralClient

    def spy_ephemeral(*args, **kwargs):
        used["called"] = True
        return original_ephemeral(*args, **kwargs)

    monkeypatch.setattr(chromadb, "EphemeralClient", spy_ephemeral)

    adapter = ChromaDBAdapter(str(tmp_path))
    vec = MemoryVector(id="v1", content="hi", embedding=[0.1] * 5, metadata={})
    adapter.store_vector(vec)
    assert adapter.retrieve_vector("v1") is not None
    assert used.get("called")
