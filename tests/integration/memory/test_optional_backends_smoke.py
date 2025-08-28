import importlib
from pathlib import Path

import pytest

BACKENDS = [
    ("tinydb", "devsynth.application.memory.tinydb_store", "TinyDBStore"),
    ("duckdb", "devsynth.application.memory.duckdb_store", "DuckDBStore"),
    ("lmdb", "devsynth.application.memory.lmdb_store", "LMDBStore"),
    ("kuzu", "devsynth.application.memory.kuzu_store", "KuzuStore"),
    ("faiss", "devsynth.application.memory.faiss_store", "FAISSStore"),
    ("chromadb", "devsynth.application.memory.chromadb_store", "ChromaDBStore"),
]


@pytest.mark.no_network
@pytest.mark.medium
@pytest.mark.parametrize("pkg, module_path, cls_name", BACKENDS)
def test_optional_memory_backend_imports(
    pkg: str, module_path: str, cls_name: str, tmp_path: Path
):
    # Skip when the optional package for the backend is not installed
    try:
        pytest.importorskip(pkg)
    except Exception:
        pytest.skip(f"optional backend {pkg} not installed")

    # Attempt to import the module and access the class symbol
    mod = importlib.import_module(module_path)
    cls = getattr(mod, cls_name, None)
    assert cls is not None, f"{cls_name} not found in {module_path}"
