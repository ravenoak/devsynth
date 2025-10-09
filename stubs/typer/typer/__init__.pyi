from __future__ import annotations

from typing import Any, Callable

class Context:
    info_name: str | None
    parent: Context | None
    params: dict[str, Any]

class Typer:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

class Exit(SystemExit):
    def __init__(self, *, code: int | None = ...) -> None: ...

def Option(default: Any = ..., *names: str, **kwargs: Any) -> Any: ...
