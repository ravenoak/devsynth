from __future__ import annotations

from typing import Any, MutableMapping


class Response:
    headers: MutableMapping[str, str]

    def __init__(self, content: Any = ..., *, media_type: str | None = ...) -> None: ...


class JSONResponse(Response):
    ...


class PlainTextResponse(Response):
    ...


class StreamingResponse(Response):
    ...

