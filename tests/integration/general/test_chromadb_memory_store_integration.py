import shutil
import tempfile
from unittest.mock import patch

import pytest

from devsynth.adapters.chromadb_memory_store import ChromaDBMemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType

pytest.importorskip("chromadb")
import chromadb  # noqa: F401

pytestmark = [
    pytest.mark.requires_resource("chromadb"),
    pytest.mark.memory_intensive,
]


@pytest.fixture
def temp_dir():
    path = tempfile.mkdtemp(prefix="chromadb_integ_")
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def enable_chromadb(monkeypatch):
    monkeypatch.setenv("ENABLE_CHROMADB", "true")
    yield


def test_chromadb_memory_store_end_to_end(temp_dir):
    with patch(
        "devsynth.adapters.chromadb_memory_store.embed",
        return_value=[[0.1, 0.2, 0.3, 0.4, 0.5]],
    ):
        store = ChromaDBMemoryStore(
            persist_directory=temp_dir,
            use_provider_system=True,
            collection_name="test_collection",
            max_retries=2,
            retry_delay=0.1,
        )
        item = MemoryItem(
            id="1",
            content="hello world",
            memory_type=MemoryType.WORKING,
            metadata={"index": 1},
        )
        store.store(item)
        retrieved = store.retrieve("1")
        assert retrieved.content == "hello world"
        results = store.search({"query": "hello world", "top_k": 1})
        assert results
        assert results[0].id == "1"
        assert store.delete("1") is True
        with pytest.raises(RuntimeError):
            store.retrieve("1")
