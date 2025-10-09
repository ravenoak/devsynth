import pytest

from tests.fixtures.resources import backend_import_reason, skip_if_missing_backend
from tests.lightweight_imports import apply_lightweight_imports

pytestmark = [
    *skip_if_missing_backend("chromadb"),
]


@pytest.mark.fast
def test_chromadb_store_import() -> None:
    """ChromaDBStore should import when chromadb extras are installed.

    ReqID: CDS-001
    """
    pytest.importorskip(
        "chromadb",
        reason=backend_import_reason("chromadb"),
    )
    apply_lightweight_imports()
    from devsynth.application.memory.chromadb_store import ChromaDBStore  # noqa: F401
