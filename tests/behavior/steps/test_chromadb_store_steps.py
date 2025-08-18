import pytest
from pytest_bdd import given, when, then, scenarios

pytest.importorskip("chromadb")
from devsynth.application.memory.chromadb_store import ChromaDBStore

pytestmark = pytest.mark.requires_resource("chromadb")

scenarios("../features/memory/chromadb_store.feature")


@pytest.fixture
def context():
    class Context:
        store: ChromaDBStore
        optimized: bool
        efficiency: float

    return Context()


@pytest.mark.fast
@given("a ChromaDB memory store")
def given_store(context, tmp_path):
    ChromaDBStore.__abstractmethods__ = set()
    context.store = ChromaDBStore(file_path=str(tmp_path))


@pytest.mark.fast
@when("I check its embedding optimization")
def check_embedding(context):
    context.optimized = context.store.has_optimized_embeddings()
    context.efficiency = context.store.get_embedding_storage_efficiency()


@pytest.mark.fast
@then("it should report optimized embeddings")
def then_optimized(context):
    assert context.optimized is True


@pytest.mark.fast
@then("the embedding storage efficiency is above 0.0")
def then_efficiency(context):
    assert 0.0 < context.efficiency <= 1.0
