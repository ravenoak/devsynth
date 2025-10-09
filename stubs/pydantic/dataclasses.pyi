from __future__ import annotations

from typing import Any, Callable, TypeVar

_T = TypeVar("_T")

def dataclass(
    __cls: type[_T] | None = ..., **kwargs: Any
) -> Callable[[type[_T]], type[_T]] | type[_T]: ...
