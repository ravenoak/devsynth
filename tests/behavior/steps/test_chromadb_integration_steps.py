"""BDD steps for ChromaDB integration tests."""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Register CLI installation step used in feature backgrounds
from .cli_commands_steps import check_workflow_success  # noqa: F401

pytestmark = [pytest.mark.fast]


@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    """Placeholder for CLI availability."""
    return True


@given("I have a valid DevSynth project")
def valid_devsynth_project(tmp_project_dir):
    """Create a minimal DevSynth project for tests."""
    manifest = tmp_project_dir / "devsynth.yaml"
    manifest.write_text("projectName: test\nversion: 1.0.0\n")
    return tmp_project_dir


@pytest.fixture
def chroma_context(monkeypatch, tmp_path):
    """Provide a mocked ``ChromaDBMemoryStore`` instance."""
    import devsynth.adapters.chromadb_memory_store as chroma_module

    mock_store = MagicMock()
    mock_cls = MagicMock(return_value=mock_store)
    monkeypatch.setattr(chroma_module, "ChromaDBMemoryStore", mock_cls)
    return {"cls": mock_cls, "store": mock_store, "path": tmp_path}


scenarios(feature_path(__file__, "general", "chromadb_integration.feature"))


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


@when(parsers.parse('I configure the memory store type as "{store}"'))
def configure_store(store, chroma_context):
    """Configure the memory store type."""
    from devsynth.adapters.chromadb_memory_store import ChromaDBMemoryStore

    chroma_context["store_instance"] = ChromaDBMemoryStore(
        persist_directory=str(chroma_context["path"])
    )


@given(parsers.parse('the memory store type is configured as "{store}"'))
def given_store_configured(store, chroma_context):
    configure_store(store, chroma_context)


@then("the chromadb_integration workflow completes")
def then_complete(chroma_context):
    """Ensure store operations were attempted."""
    chroma_context["cls"].assert_called_once()
    chroma_context["store"].store_memory.assert_called_once()
    chroma_context["store"].retrieve_memory.assert_called_once()


@then("a ChromaDB memory store should be initialized")
def check_store_initialized(chroma_context):
    """Placeholder check for store initialization."""
    assert "store_instance" in chroma_context
