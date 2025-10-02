from typing import Any, Protocol


class Storage(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class JSONStorage:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def read(self) -> Any: ...

    def write(self, data: Any) -> None: ...

    def close(self) -> None: ...


def touch(filename: str, create_dirs: bool = ...) -> str: ...


__all__ = ["Storage", "JSONStorage", "touch"]
