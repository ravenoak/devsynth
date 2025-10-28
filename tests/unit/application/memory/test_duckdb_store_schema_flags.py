"""Focused tests for DuckDBStore schema initialization helpers."""

import os
import sys
import types
from typing import Any, List, Tuple

import pytest

from devsynth.application.memory import duckdb_store

pytestmark = [pytest.mark.fast, pytest.mark.requires_resource("duckdb")]


if os.environ.get("DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE", "true").lower() == "false":
    pytest.skip("DuckDB resource not available", allow_module_level=True)


if "duckdb" not in sys.modules:
    stub = types.ModuleType("duckdb")

    def _connect(*args, **kwargs):  # pragma: no cover - defensive stub
        raise RuntimeError("duckdb stub does not support connections in unit tests")

    stub.connect = _connect  # type: ignore[attr-defined]
    sys.modules["duckdb"] = stub


class RecordingCursor:
    """Minimal cursor stub supporting the chained fetch API used by DuckDBStore."""

    def __init__(
        self,
        fetchone_result: Any | None = None,
        fetchall_result: list[Any] | None = None,
    ) -> None:
        self._fetchone_result = fetchone_result
        self._fetchall_result = fetchall_result or []

    def fetchone(self) -> Any:
        return self._fetchone_result

    def fetchall(self) -> list[Any]:
        return list(self._fetchall_result)


class RecordingConnection:
    """Connection stub that records executed SQL statements."""

    def __init__(self, *, fail_vector_extension: bool = False) -> None:
        self.fail_vector_extension = fail_vector_extension
        self.commands: list[tuple[str, Any]] = []

    def execute(
        self, sql: str, params: tuple[Any, ...] | None = None
    ) -> RecordingCursor:
        normalized = " ".join(str(sql).split())
        self.commands.append((normalized, params))
        if self.fail_vector_extension and "INSTALL vector" in normalized:
            raise RuntimeError("vector extension unavailable")
        return RecordingCursor()


def _build_store(
    tmp_path, connection: RecordingConnection, enable_hnsw: bool
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        base_path=str(tmp_path),
        db_file=os.path.join(str(tmp_path), "memory.duckdb"),
        token_count=0,
        enable_hnsw=enable_hnsw,
        hnsw_config={"M": 16, "efConstruction": 120, "efSearch": 60},
        vector_extension_available=False,
        conn=connection,
    )


def test_initialize_schema_without_vector_extension_falls_back(tmp_path):
    """When the vector extension fails the store should create the JSON fallback schema."""

    connection = RecordingConnection(fail_vector_extension=True)
    store = _build_store(tmp_path, connection, enable_hnsw=False)

    duckdb_store.DuckDBStore._initialize_schema(store)

    assert store.vector_extension_available is False
    commands = [cmd for cmd, _ in connection.commands]
    assert any("embedding VARCHAR" in cmd for cmd in commands)
    assert not any("embedding FLOAT[]" in cmd for cmd in commands)


def test_initialize_schema_configures_hnsw_when_enabled(monkeypatch, tmp_path):
    """Enabling HNSW should issue the expected configuration statements."""

    connection = RecordingConnection()
    store = _build_store(tmp_path, connection, enable_hnsw=True)

    monkeypatch.setattr(
        duckdb_store.feature_flags, "experimental_enabled", lambda: True
    )

    duckdb_store.DuckDBStore._initialize_schema(store)

    assert store.vector_extension_available is True
    commands = [cmd for cmd, _ in connection.commands]
    assert any(
        "SET hnsw_enable_experimental_persistence = true;" in cmd for cmd in commands
    )
    assert any(f"SET hnsw_M = {store.hnsw_config['M']};" in cmd for cmd in commands)
    assert any(
        f"SET hnsw_efConstruction = {store.hnsw_config['efConstruction']};" in cmd
        for cmd in commands
    )
    assert any(
        f"SET hnsw_efSearch = {store.hnsw_config['efSearch']};" in cmd
        for cmd in commands
    )
