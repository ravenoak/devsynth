from typing import Any

class ndarray:
    shape: tuple[int, ...]
    dtype: Any

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def astype(self, dtype: Any) -> ndarray: ...

    def copy(self) -> ndarray: ...

    def tolist(self) -> list[Any]: ...

    def all(self) -> bool: ...


def array(object: Any, dtype: Any | None = ...) -> ndarray: ...

def dot(a: Any, b: Any) -> Any: ...

def isfinite(x: Any) -> ndarray: ...

float32: Any

from . import linalg

__all__ = ["ndarray", "array", "dot", "isfinite", "float32", "linalg"]
