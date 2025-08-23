import pytest

from tests.lightweight_imports import apply_lightweight_imports


@pytest.mark.fast
def test_chromadb_store_import() -> None:
    """ChromaDBStore should import when chromadb extras are installed.

    ReqID: CDS-001
    """
    pytest.importorskip("chromadb")
    apply_lightweight_imports()
    from devsynth.application.memory.chromadb_store import ChromaDBStore  # noqa: F401
