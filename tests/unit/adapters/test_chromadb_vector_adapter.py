import os
import tempfile
import uuid
from unittest.mock import patch, MagicMock, create_autospec

import pytest

from devsynth.application.memory.adapters.chromadb_vector_adapter import (
    ChromaDBVectorAdapter,
)
from devsynth.domain.models.memory import MemoryVector

pytest.importorskip("chromadb")
import chromadb
from chromadb.api.models.Collection import Collection

pytestmark = pytest.mark.requires_resource("chromadb")


@pytest.fixture
def mock_chromadb_client():
    client = create_autospec(chromadb.Client if chromadb else object)
    collection = create_autospec(Collection)
    client.get_or_create_collection.return_value = collection
    return client, collection


@pytest.fixture
def temp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def vector_adapter(temp_dir, mock_chromadb_client):
    mock_client, mock_collection = mock_chromadb_client
    with patch(
        "devsynth.application.memory.adapters.chromadb_vector_adapter.chromadb.PersistentClient",
        return_value=mock_client,
    ):
        adapter = ChromaDBVectorAdapter(
            collection_name="test", persist_directory=temp_dir
        )
        adapter.collection = mock_collection
        yield adapter


def test_store_and_retrieve_vector(vector_adapter, mock_chromadb_client):
    _, collection = mock_chromadb_client
    collection.get.return_value = {
        "ids": ["v1"],
        "embeddings": [[0.1, 0.2]],
        "metadatas": [{"foo": "bar"}],
        "documents": ["content"],
    }
    vec = MemoryVector(
        id="v1", content="content", embedding=[0.1, 0.2], metadata={"foo": "bar"}
    )
    vid = vector_adapter.store_vector(vec)
    assert vid == "v1"
    collection.add.assert_called_once_with(
        ids=["v1"],
        embeddings=[[0.1, 0.2]],
        metadatas=[{"foo": "bar"}],
        documents=["content"],
    )
    out = vector_adapter.retrieve_vector("v1")
    collection.get.assert_called_with(
        ids=["v1"], include=["embeddings", "metadatas", "documents"]
    )
    assert out is not None and out.id == "v1"
    assert out.content == "content"


def test_similarity_search(vector_adapter, mock_chromadb_client):
    _, collection = mock_chromadb_client
    collection.query.return_value = {
        "ids": [["v1", "v2"]],
        "embeddings": [
            [
                [0.1, 0.2],
                [0.2, 0.3],
            ]
        ],
        "metadatas": [[{"a": 1}, {"a": 2}]],
        "documents": [["c1", "c2"]],
    }
    results = vector_adapter.similarity_search([0.1, 0.2], top_k=2)
    collection.query.assert_called_once()
    assert len(results) == 2
    assert {r.id for r in results} == {"v1", "v2"}


def test_delete_vector(vector_adapter, mock_chromadb_client):
    _, collection = mock_chromadb_client
    collection.get.return_value = {"ids": ["v1"]}
    assert vector_adapter.delete_vector("v1") is True
    collection.delete.assert_called_with(ids=["v1"])
    collection.get.return_value = {"ids": []}
    assert vector_adapter.delete_vector("v1") is False
