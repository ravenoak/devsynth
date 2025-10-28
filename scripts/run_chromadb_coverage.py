"""Run targeted coverage for ChromaDB-related adapters."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List

TESTS: list[str] = [
    "tests/unit/adapters/test_chromadb_memory_store_unit.py",
    "tests/unit/application/memory/test_memory_system_adapter_unit.py",
]
COVERAGE_SOURCES = ",".join(
    [
        "src/devsynth/adapters/chromadb_memory_store.py",
        "src/devsynth/adapters/memory/memory_adapter.py",
    ]
)
REPORT_PATH = Path("test_reports/chromadb_coverage.txt")


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        message = ["Command failed:", " ".join(cmd)]
        if stdout:
            message.append("stdout:\n" + stdout)
        if stderr:
            message.append("stderr:\n" + stderr)
        raise RuntimeError("\n".join(message))
    return result


def _build_memory_adapter_driver(tmp_path: Path) -> str:
    template = """
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

sys.path.insert(0, "src")

from devsynth.adapters.memory import memory_adapter


class DummySettings:
    def __init__(self, base: Path) -> None:
        self.memory_store_type = "memory"
        self.memory_file_path = str(base / "memory.json")
        self.max_context_size = 10
        self.context_expiration_days = 1
        self.vector_store_enabled = False
        self.provider_type = None
        self.chromadb_collection_name = "coverage"
        self.chromadb_host = "localhost"
        self.chromadb_port = 8000
        self.enable_chromadb = True
        self.encryption_at_rest = False
        self.encryption_key = None


settings = DummySettings(Path("__TMP_PATH__"))
memory_adapter.get_settings = lambda: settings
memory_adapter.ensure_path_exists = lambda path, create=True: str(path)


class DummyInMemoryStore:
    def __init__(self) -> None:
        self.vector = SimpleNamespace()
        self.records = {}

    def store(self, item):
        if isinstance(item, dict):
            item_id = item.get("id", "generated")
        else:
            item_id = getattr(item, "id", "generated")
        self.records[item_id] = item
        return item_id

    def query_by_type(self, memory_type):
        return [memory_type]

    def query_by_metadata(self, metadata):
        return [metadata]

    def search(self, query):
        return [query]

    def retrieve(self, item_id):
        return self.records.get(item_id, {"id": item_id})

    def get_all(self):
        return list(self.records.values())

    def get_token_usage(self):
        return 5

    def delete(self, item_id):
        self.records.pop(item_id, None)
        return True

    def begin_transaction(self):
        return "tx" + str(len(self.records))

    def commit_transaction(self, transaction_id):
        return True

    def rollback_transaction(self, transaction_id):
        return True

    def is_transaction_active(self, transaction_id):
        return False

    def flush(self):
        pass


class DummySimpleContextManager:
    def get_token_usage(self):
        return 2

    def flush(self):
        pass


class DummyJSONFileStore:
    def __init__(self, path, *, encryption_enabled=False, encryption_key=None):
        self.path = path
        self.encryption_enabled = encryption_enabled
        self.encryption_key = encryption_key


class DummyPersistentContextManager:
    def __init__(self, path, *, max_context_size, expiration_days):
        self.path = path


class DummyTinyDBStore(DummyJSONFileStore):
    pass


class DummyDuckDBStore:
    def __init__(self, path):
        self.path = path

    def flush(self):
        pass


class DummyFAISSStore:
    def __init__(self, path):
        self.path = path


class DummyRDFLibStore:
    def __init__(self, path):
        self.path = path


class DummyKuzuStore:
    def __init__(self, path, *, provider_type=None):
        self.path = path
        self.provider_type = provider_type
        self.vector = SimpleNamespace()
        self._store = SimpleNamespace(_use_fallback=False)


class FallbackKuzuStore(DummyKuzuStore):
    def __init__(self, path, *, provider_type=None):
        super().__init__(path, provider_type=provider_type)
        self._store = SimpleNamespace(_use_fallback=True)


class DummyTieredCache:
    def __init__(self, max_size):
        self.max_size = max_size
        self.items = {}
        self.removed = []
        self.cleared = False

    def size(self):
        return len(self.items)

    def clear(self):
        self.items.clear()
        self.cleared = True

    def remove(self, item_id):
        self.removed.append(item_id)
        self.items.pop(item_id, None)


memory_adapter.InMemoryStore = DummyInMemoryStore
memory_adapter.SimpleContextManager = DummySimpleContextManager
memory_adapter.JSONFileStore = DummyJSONFileStore
memory_adapter.PersistentContextManager = DummyPersistentContextManager
memory_adapter.TinyDBStore = DummyTinyDBStore
memory_adapter.DuckDBStore = DummyDuckDBStore
memory_adapter.FAISSStore = DummyFAISSStore
memory_adapter.RDFLibStore = DummyRDFLibStore
memory_adapter.KuzuMemoryStore = DummyKuzuStore
memory_adapter.LMDBStore = DummyTinyDBStore
memory_adapter._LMDB_ERROR = RuntimeError("missing")
memory_adapter.TieredCache = DummyTieredCache


adapter = memory_adapter.MemorySystemAdapter(config={"memory_store_type": "memory"}, create_paths=False)

# File branch
adapter.storage_type = "file"
adapter.memory_path = str(Path("__TMP_PATH__") / "file.json")
adapter.encryption_at_rest = True
adapter.encryption_key = "secret"
adapter._initialize_memory_system(create_paths=False)

# Chromadb disabled
adapter.storage_type = "chromadb"
adapter.enable_chromadb = False
adapter._initialize_memory_system(create_paths=False)

# Chromadb enabled
adapter.enable_chromadb = True
adapter.vector_store_enabled = True
store_module = ModuleType("devsynth.application.memory.chromadb_store")
adapter_module = ModuleType("devsynth.adapters.memory.chroma_db_adapter")


class StubChromaDBStore:
    def __init__(self, path, *, host=None, port=None, collection_name=None):
        self.path = path
        self.collection_name = collection_name


class StubChromaDBAdapter:
    def __init__(self, *, persist_directory, collection_name, host=None, port=None):
        self.persist_directory = persist_directory
        self.collection_name = collection_name


store_module.ChromaDBStore = StubChromaDBStore
adapter_module.ChromaDBAdapter = StubChromaDBAdapter
sys.modules["devsynth.application.memory.chromadb_store"] = store_module
sys.modules["devsynth.adapters.memory.chroma_db_adapter"] = adapter_module
adapter.chromadb_collection_name = "coverage"
adapter.chromadb_host = "localhost"
adapter.chromadb_port = 9000
adapter._initialize_memory_system(create_paths=False)

# Kuzu normal and fallback
adapter.storage_type = "kuzu"
adapter.enable_chromadb = False
adapter.vector_store_enabled = True
adapter._initialize_memory_system(create_paths=False)
memory_adapter.KuzuMemoryStore = FallbackKuzuStore
adapter.enable_chromadb = True
adapter._initialize_memory_system(create_paths=False)

# TinyDB
adapter.storage_type = "tinydb"
adapter._initialize_memory_system(create_paths=False)

# DuckDB
adapter.storage_type = "duckdb"
adapter.vector_store_enabled = True
adapter._initialize_memory_system(create_paths=False)

# LMDB missing and present
adapter.storage_type = "lmdb"
memory_adapter.LMDBStore = None
adapter._initialize_memory_system(create_paths=False)
memory_adapter.LMDBStore = DummyTinyDBStore
adapter._initialize_memory_system(create_paths=False)

# FAISS and RDFLib
adapter.storage_type = "faiss"
adapter.vector_store_enabled = True
adapter._initialize_memory_system(create_paths=False)
adapter.storage_type = "rdflib"
adapter._initialize_memory_system(create_paths=False)

# Default fallback
adapter.storage_type = "memory"
adapter._initialize_memory_system(create_paths=False)

# Cache and transaction helpers
adapter.enable_tiered_cache(max_size=3)
adapter.cache.items["item-1"] = {}
adapter.store({"id": "item-1"})
adapter.clear_cache()
adapter.disable_tiered_cache()
adapter.get_cache_stats()
adapter.get_cache_size()
adapter.has_vector_store()
adapter.get_token_usage()
adapter.flush()
adapter.begin_transaction()
adapter.commit_transaction("tx-commit")
adapter.rollback_transaction("tx-rollback")
adapter.is_transaction_active("tx-check")
adapter.execute_in_transaction([lambda: adapter.store({"id": "item-2"})], fallback_operations=[lambda: adapter.store({"id": "fb"})])

testing_adapter = memory_adapter.MemorySystemAdapter.create_for_testing(storage_type="memory")
testing_adapter.enable_tiered_cache(max_size=1)
testing_adapter.disable_tiered_cache()
"""
    return template.replace("__TMP_PATH__", str(tmp_path))


def main() -> int:
    os.makedirs(REPORT_PATH.parent, exist_ok=True)

    for coverage_file in Path.cwd().glob(".coverage*"):
        coverage_file.unlink()

    pytest_cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--include={COVERAGE_SOURCES}",
        "-m",
        "pytest",
        *TESTS,
        "-q",
    ]
    pytest_result = _run(pytest_cmd)

    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        driver_path = Path(handle.name)
        handle.write(_build_memory_adapter_driver(Path(".tmp_chromadb_cov")))

    try:
        driver_cmd = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--append",
            f"--include={COVERAGE_SOURCES}",
            str(driver_path),
        ]
        _run(driver_cmd)
    finally:
        driver_path.unlink(missing_ok=True)

    report_cmd = [
        sys.executable,
        "-m",
        "coverage",
        "report",
        f"--include={COVERAGE_SOURCES}",
        "--show-missing",
    ]
    report = _run(report_cmd)

    REPORT_PATH.write_text(report.stdout, encoding="utf-8")

    print(pytest_result.stdout, end="")
    if pytest_result.stderr:
        print(pytest_result.stderr, file=sys.stderr, end="")
    print(report.stdout, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
