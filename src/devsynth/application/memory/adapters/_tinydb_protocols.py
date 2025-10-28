"""Structural protocols for optional TinyDB dependencies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class TinyDBQueryLike(Protocol):
    """Subset of TinyDB's ``Query`` API used by the adapters."""

    def __getattr__(self, name: str) -> TinyDBQueryLike: ...

    def __getitem__(self, item: str) -> TinyDBQueryLike: ...

    def __and__(self, other: TinyDBQueryLike) -> TinyDBQueryLike: ...


class TinyDBQueryFactory(Protocol):
    """Callable that produces :class:`TinyDBQueryLike` objects."""

    def __call__(self) -> TinyDBQueryLike: ...


class TinyDBTableLike(Protocol):
    """Subset of TinyDB table operations relied upon by the adapter."""

    def get(self, cond: TinyDBQueryLike) -> Mapping[str, Any] | None: ...

    def insert(self, item: Mapping[str, Any]) -> int: ...

    def update(self, fields: Mapping[str, Any], cond: TinyDBQueryLike) -> list[int]: ...

    def remove(self, cond: TinyDBQueryLike) -> list[int]: ...

    def all(self) -> list[Mapping[str, Any]]: ...

    def search(self, cond: TinyDBQueryLike) -> list[Mapping[str, Any]]: ...

    def truncate(self) -> None: ...


class TinyDBFactory(Protocol):
    """Callable returning TinyDB-like database instances."""

    def __call__(self, *args: Any, **kwargs: Any) -> TinyDBLike: ...


class TinyDBLike(Protocol):
    """Structural protocol describing the TinyDB database object."""

    def table(self, name: str) -> TinyDBTableLike: ...

    def close(self) -> None: ...


__all__ = [
    "TinyDBFactory",
    "TinyDBLike",
    "TinyDBQueryFactory",
    "TinyDBQueryLike",
    "TinyDBTableLike",
]
