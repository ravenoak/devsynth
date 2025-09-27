from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, MutableMapping
from typing import Any, Optional, TypeVar


_T = TypeVar("_T")


class _URL:
    path: str


class Request:
    headers: Mapping[str, str]
    url: _URL


class HTTPException(Exception):
    status_code: int
    detail: str | None

    def __init__(self, *, status_code: int, detail: str | None = ...) -> None: ...


def Depends(dependency: Callable[..., _T] | None = ...) -> _T: ...


def Header(
    default: _T | None = ...,
    *,
    alias: str | None = ...,
    convert_underscores: bool = ...,
) -> _T | None: ...


class _StatusModule:
    HTTP_401_UNAUTHORIZED: int


status: _StatusModule


class FastAPI:
    def __init__(self, *, title: str | None = ...) -> None: ...

    def include_router(self, router: Any, *, prefix: str = ...) -> None: ...

    def middleware(
        self, middleware_type: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]: ...

    def get(
        self, path: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]: ...


class APIRouter:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def add_api_route(self, path: str, endpoint: Callable[..., Awaitable[Any]], *, methods: Optional[list[str]] = ...) -> None: ...


class Response:
    def __init__(self, content: Any = ..., *, media_type: str | None = ...) -> None: ...

    headers: MutableMapping[str, str]


class TestClient:
    def __init__(self, app: FastAPI) -> None: ...

    def get(self, url: str, *, headers: Mapping[str, str] | None = ...) -> Response: ...

