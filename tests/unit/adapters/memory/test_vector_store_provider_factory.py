import pytest

from devsynth.application.memory.dto import VectorStoreStats
from devsynth.application.memory.vector_providers import (
    SimpleVectorStoreProviderFactory,
)
from devsynth.domain.interfaces.memory import MemoryVector, VectorStore
from devsynth.exceptions import ValidationError

pytestmark = [pytest.mark.memory_intensive, pytest.mark.isolation]


class StubStore(VectorStore[MemoryVector]):

    def __init__(self, **config):
        self.config = config

    def store_vector(self, vector: MemoryVector) -> str:
        return "id"

    def retrieve_vector(self, vector_id: str) -> MemoryVector | None:
        return None

    def similarity_search(self, query_embedding, top_k: int = 5) -> list[MemoryVector]:
        return []

    def delete_vector(self, vector_id: str) -> bool:
        return True

    def get_collection_stats(self) -> VectorStoreStats:
        return {"collection_name": "stub", "vector_count": 0}


@pytest.mark.medium
def test_register_and_create_succeeds():
    """Test that register and create succeeds.

    ReqID: N/A"""
    factory = SimpleVectorStoreProviderFactory()
    factory.register_provider_type("stub", StubStore)
    provider = factory.create_provider("stub", {"foo": "bar"})
    assert isinstance(provider, StubStore)
    assert provider.config["foo"] == "bar"


@pytest.mark.medium
def test_unknown_type_succeeds():
    """Test that unknown type succeeds.

    ReqID: N/A"""
    factory = SimpleVectorStoreProviderFactory()
    with pytest.raises(ValidationError):
        factory.create_provider("missing")
