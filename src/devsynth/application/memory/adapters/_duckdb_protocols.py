"""Structural typing helpers for optional DuckDB dependency."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class DuckDBResultProtocol(Protocol):
    """Subset of DuckDB result interface used throughout the adapters."""

    def fetchall(self) -> list[tuple[Any, ...]]: ...

    def fetchone(self) -> tuple[Any, ...] | None: ...


class DuckDBConnectionProtocol(DuckDBResultProtocol, Protocol):
    """Structural protocol describing the DuckDB connection object."""

    def execute(
        self, query: str, parameters: Sequence[Any] | None = ...
    ) -> DuckDBResultProtocol: ...

    def close(self) -> None: ...


class DuckDBModuleProtocol(Protocol):
    """Structural protocol for the top-level :mod:`duckdb` module."""

    def connect(
        self,
        database: str | None = ...,
        read_only: bool | None = ...,
    ) -> DuckDBConnectionProtocol: ...


__all__ = [
    "DuckDBConnectionProtocol",
    "DuckDBModuleProtocol",
    "DuckDBResultProtocol",
]
