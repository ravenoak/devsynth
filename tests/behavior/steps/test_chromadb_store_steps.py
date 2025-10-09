import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [
    pytest.mark.fast,
    pytest.mark.requires_resource("chromadb"),
]

pytest.importorskip("chromadb")
from devsynth.application.memory.chromadb_store import ChromaDBStore

scenarios(feature_path(__file__, "general", "chromadb_store.feature"))


@pytest.fixture
def context():
    class Context:
        store: ChromaDBStore
        optimized: bool
        efficiency: float

    return Context()


@given("a ChromaDB memory store")
def given_store(context, tmp_path):
    ChromaDBStore.__abstractmethods__ = set()
    context.store = ChromaDBStore(file_path=str(tmp_path))


@when("I check its embedding optimization")
def check_embedding(context):
    context.optimized = context.store.has_optimized_embeddings()
    context.efficiency = context.store.get_embedding_storage_efficiency()


@then("it should report optimized embeddings")
def then_optimized(context):
    assert context.optimized is True


@then("the embedding storage efficiency is above 0.0")
def then_efficiency(context):
    assert 0.0 < context.efficiency <= 1.0
