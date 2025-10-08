import pytest

from tests.conftest import is_resource_available
from tests.fixtures.resources import (
    OPTIONAL_BACKEND_REQUIREMENTS,
    backend_import_reason,
    backend_skip_reason,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("kuzu")

_KUZU_EXTRAS = tuple(OPTIONAL_BACKEND_REQUIREMENTS["kuzu"]["extras"])

pytest.importorskip("kuzu", reason=backend_import_reason("kuzu", _KUZU_EXTRAS))

if not is_resource_available("kuzu"):
    pytest.skip(
        backend_skip_reason("kuzu", _KUZU_EXTRAS),
        allow_module_level=True,
    )

from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
from devsynth.domain.models.memory import MemoryVector

# Transactions require kuzu and run a bit longer than unit tests

pytestmark = [pytest.mark.requires_resource("kuzu")]


@pytest.mark.medium
def test_kuzu_adapter_transaction_persistence(tmp_path):
    """KuzuAdapter should commit and rollback vector operations with persistence."""

    adapter = KuzuAdapter(str(tmp_path))
    vec = MemoryVector(
        id="v1", content="persist", embedding=[0.1, 0.2, 0.3], metadata={}
    )

    tid = adapter.begin_transaction()
    adapter.store_vector(vec)
    adapter.commit_transaction(tid)
    assert adapter.retrieve_vector("v1") is not None

    adapter2 = KuzuAdapter(str(tmp_path))
    assert adapter2.retrieve_vector("v1") is not None

    tid = adapter2.begin_transaction()
    adapter2.delete_vector("v1")
    adapter2.rollback_transaction(tid)
    assert adapter2.retrieve_vector("v1") is not None
