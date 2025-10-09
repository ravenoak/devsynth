from __future__ import annotations

from typing import Any, Mapping, MutableMapping

class Response:
    headers: MutableMapping[str, str]

    def __init__(self, content: Any = ..., *, media_type: str | None = ...) -> None: ...

class JSONResponse(Response):
    def __init__(
        self,
        content: Any = ...,
        *,
        status_code: int = ...,
        headers: Mapping[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...

class PlainTextResponse(Response):
    def __init__(
        self,
        content: str = ...,
        *,
        status_code: int = ...,
        headers: Mapping[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...

class StreamingResponse(Response): ...
