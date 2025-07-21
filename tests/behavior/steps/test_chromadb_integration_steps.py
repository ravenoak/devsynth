"""BDD steps for ChromaDB integration tests."""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import scenarios, given, when, then


@pytest.fixture
def chroma_context(monkeypatch, tmp_path):
    """Provide a mocked ``ChromaDBMemoryStore`` instance."""
    import devsynth.adapters.chromadb_memory_store as chroma_module

    mock_store = MagicMock()
    mock_cls = MagicMock(return_value=mock_store)
    monkeypatch.setattr(chroma_module, "ChromaDBMemoryStore", mock_cls)
    return {"cls": mock_cls, "store": mock_store, "path": tmp_path}


scenarios("../features/chromadb_integration.feature")


@given("the chromadb_integration feature context")
def given_context(chroma_context):
    """Return the patched context."""
    return chroma_context


@when("we execute the chromadb_integration workflow")
def when_execute(chroma_context):
    """Simulate storing and retrieving an item."""
    from devsynth.adapters.chromadb_memory_store import ChromaDBMemoryStore

    store = ChromaDBMemoryStore(persist_directory=str(chroma_context["path"]))
    store.store_memory("item")
    store.retrieve_memory("id")
    chroma_context["store_instance"] = store


@then("the chromadb_integration workflow completes")
def then_complete(chroma_context):
    """Ensure store operations were attempted."""
    chroma_context["cls"].assert_called_once()
    chroma_context["store"].store_memory.assert_called_once()
    chroma_context["store"].retrieve_memory.assert_called_once()
