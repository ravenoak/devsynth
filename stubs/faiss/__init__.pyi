from typing import Any, Tuple


class IndexFlatL2:
    ntotal: int

    def __init__(self, dimension: int) -> None: ...

    def add(self, x: Any) -> None: ...

    def search(self, x: Any, k: int) -> Tuple[Any, Any]: ...

    def reset(self) -> None: ...


def read_index(path: str) -> IndexFlatL2: ...

def write_index(index: IndexFlatL2, path: str) -> None: ...

def serialize_index(index: IndexFlatL2) -> Any: ...

def deserialize_index(data: Any) -> IndexFlatL2: ...

__all__ = [
    "IndexFlatL2",
    "read_index",
    "write_index",
    "serialize_index",
    "deserialize_index",
]
