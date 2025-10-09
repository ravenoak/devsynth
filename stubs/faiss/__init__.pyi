from typing import Tuple

import numpy as np
from numpy.typing import NDArray

class Index:
    ntotal: int

    def add(self, x: NDArray[np.float32]) -> None: ...
    def search(
        self, x: NDArray[np.float32], k: int
    ) -> Tuple[NDArray[np.float32], NDArray[np.int64]]: ...
    def reset(self) -> None: ...

class IndexFlatL2(Index):
    def __init__(self, dimension: int) -> None: ...

def read_index(path: str) -> Index: ...
def write_index(index: Index, path: str) -> None: ...
def serialize_index(index: Index) -> bytes: ...
def deserialize_index(data: bytes) -> Index: ...

__all__ = [
    "Index",
    "IndexFlatL2",
    "read_index",
    "write_index",
    "serialize_index",
    "deserialize_index",
]
