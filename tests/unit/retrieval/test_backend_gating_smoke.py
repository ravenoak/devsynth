import importlib

import pytest

from tests.fixtures.resources import backend_import_reason, backend_param

# Minimal smoke tests for retrieval/memory backends. These are skipped by default
# unless DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=true and the backend is importable.
# ReqID: B4

BACKENDS = [
    backend_param("chromadb", resource="chromadb"),
    backend_param("faiss", resource="faiss"),
    backend_param("kuzu", resource="kuzu"),
    backend_param("tinydb", resource="tinydb"),
]


@pytest.mark.fast
@pytest.mark.parametrize("module_name", BACKENDS)
def test_backend_importable_when_enabled(module_name: str) -> None:
    pytest.importorskip(
        module_name,
        reason=backend_import_reason(module_name),
    )
    mod = importlib.import_module(module_name)
    assert hasattr(mod, "__name__")
