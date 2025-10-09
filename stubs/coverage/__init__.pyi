from __future__ import annotations

from typing import Any, Iterable, Sequence, Tuple, TypeVar

__all__ = ["Coverage", "CoverageException"]

class CoverageException(Exception): ...

class Coverage:
    data_file: str | None

    def __init__(
        self, data_file: str | None = ..., config_file: str | None = ..., **kwargs: Any
    ) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def save(self) -> None: ...
    def combine(
        self,
        data_paths: Sequence[str] | None = ...,
        *,
        strict: bool = ...,
        keep: bool = ...,
    ) -> None: ...
    @classmethod
    def current(cls) -> Coverage | None: ...
