from __future__ import annotations

from typing import Any, IO


def safe_load(stream: str | IO[str]) -> Any: ...


def safe_dump(data: Any, stream: IO[str] | None = ..., **kwargs: Any) -> str: ...

