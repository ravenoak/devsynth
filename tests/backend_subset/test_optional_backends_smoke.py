import importlib
from pathlib import Path

import pytest

from tests.fixtures.resources import backend_import_reason, backend_param

BACKENDS = [
    backend_param(
        "tinydb",
        "devsynth.application.memory.tinydb_store",
        "TinyDBStore",
        resource="tinydb",
    ),
    backend_param(
        "duckdb",
        "devsynth.application.memory.duckdb_store",
        "DuckDBStore",
        resource="duckdb",
    ),
    backend_param(
        "lmdb",
        "devsynth.application.memory.lmdb_store",
        "LMDBStore",
        resource="lmdb",
    ),
    backend_param(
        "kuzu",
        "devsynth.application.memory.kuzu_store",
        "KuzuStore",
        resource="kuzu",
    ),
    backend_param(
        "faiss",
        "devsynth.application.memory.faiss_store",
        "FAISSStore",
        resource="faiss",
    ),
    backend_param(
        "chromadb",
        "devsynth.application.memory.chromadb_store",
        "ChromaDBStore",
        resource="chromadb",
    ),
]


@pytest.mark.no_network
@pytest.mark.medium
@pytest.mark.parametrize("pkg, module_path, cls_name", BACKENDS)
def test_optional_memory_backend_imports(
    pkg: str, module_path: str, cls_name: str, tmp_path: Path
):
    pytest.importorskip(pkg, reason=backend_import_reason(pkg))

    # Attempt to import the module and access the class symbol
    mod = importlib.import_module(module_path)
    cls = getattr(mod, cls_name, None)
    assert cls is not None, f"{cls_name} not found in {module_path}"
