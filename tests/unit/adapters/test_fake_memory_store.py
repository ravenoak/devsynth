import pytest

from devsynth.adapters.fakes import FakeMemoryStore, FakeVectorStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


@pytest.mark.fast
@pytest.mark.unit
def test_fake_memory_store_store_retrieve_search_delete_and_txn():
    """ReqID: UT-ADAPTERS-FAKE-MEMORY-01
    Validate FakeMemoryStore end-to-end operations: store, retrieve, search,
    delete, and transaction visibility/commit semantics.
    """
    store = FakeMemoryStore()
    # Store two items
    id1 = store.store(
        MemoryItem(id="", memory_type=MemoryType.WORKING, content="Hello World")
    )
    id2 = store.store(
        MemoryItem(
            id="", memory_type=MemoryType.WORKING, content="Another note about World"
        )
    )

    # Retrieve
    assert store.retrieve(id1).content == "Hello World"

    # Search
    hits = store.search({"text": "world", "type": MemoryType.WORKING})
    assert {h.id for h in hits} == {id1, id2}

    # Transactions
    tx = store.begin_transaction()
    id3 = store.store(
        MemoryItem(id="", memory_type=MemoryType.WORKING, content="Temp"),
        transaction_id=tx,
    )
    assert store.retrieve(id3) is None  # not visible until commit
    assert store.is_transaction_active(tx)
    store.commit_transaction(tx)
    assert store.retrieve(id3) is not None

    # Delete
    assert store.delete(id1)
    assert store.retrieve(id1) is None


@pytest.mark.fast
@pytest.mark.unit
def test_fake_vector_store_similarity_and_stats():
    """ReqID: UT-ADAPTERS-FAKE-VECTOR-01
    Validate FakeVectorStore similarity ordering, retrieval, and stats.
    """
    vs = FakeVectorStore()
    # Insert three vectors
    v1 = MemoryVector(
        id="", content="x", embedding=[1.0, 0.0, 0.0], metadata={"name": "x"}
    )
    v2 = MemoryVector(
        id="", content="y", embedding=[0.0, 1.0, 0.0], metadata={"name": "y"}
    )
    v3 = MemoryVector(
        id="", content="x+y", embedding=[1.0, 1.0, 0.0], metadata={"name": "x+y"}
    )
    _ = vs.store_vector(v1)
    id2 = vs.store_vector(v2)
    id3 = vs.store_vector(v3)

    # Similarity to [1,0,0] should prefer v1 then v3
    results = vs.similarity_search([1.0, 0.0, 0.0], top_k=2)
    assert results[0].metadata["name"] == "x"
    assert results[1].metadata["name"] == "x+y"

    # Stats and retrieve
    stats = vs.get_collection_stats()
    assert stats["count"] == 3
    assert vs.retrieve_vector(id2).metadata["name"] == "y"

    # Delete
    assert vs.delete_vector(id3)
    assert vs.get_collection_stats()["count"] == 2
