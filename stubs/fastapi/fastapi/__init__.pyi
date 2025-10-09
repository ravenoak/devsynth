from __future__ import annotations

from typing import (
    Any,
    Awaitable,
    Callable,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    TypeVar,
)

from typing_extensions import ParamSpec

_P = ParamSpec("_P")
_R = TypeVar("_R")
_T = TypeVar("_T")

class _URL:
    path: str

class Request:
    headers: Mapping[str, str]
    url: _URL
    client: Any

class HTTPException(Exception):
    status_code: int
    detail: Any

    def __init__(self, *, status_code: int, detail: Any = ...) -> None: ...

def Depends(dependency: Callable[..., _T] | None = ...) -> _T: ...
def Header(
    default: _T | None = ...,
    *,
    alias: str | None = ...,
    convert_underscores: bool = ...,
) -> _T | None: ...

class _StatusModule:
    HTTP_401_UNAUTHORIZED: int
    HTTP_429_TOO_MANY_REQUESTS: int
    HTTP_500_INTERNAL_SERVER_ERROR: int

status: _StatusModule

class Response:
    def __init__(self, content: Any = ..., *, media_type: str | None = ...) -> None: ...

    headers: MutableMapping[str, str]

class FastAPI:
    def __init__(
        self,
        *,
        title: str | None = ...,
        description: str | None = ...,
        version: str | None = ...,
        docs_url: str | None = ...,
        redoc_url: str | None = ...,
    ) -> None: ...
    def include_router(self, router: APIRouter, *, prefix: str = ...) -> None: ...
    def middleware(
        self, middleware_type: str
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]: ...
    def get(self, path: str) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...
    def exception_handler(self, exc_class: type[Exception]) -> Callable[
        [Callable[[Request, Exception], Awaitable[Any]]],
        Callable[[Request, Exception], Awaitable[Any]],
    ]: ...

class APIRouter:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Awaitable[Any]],
        *,
        methods: Optional[Sequence[str]] = ...,
    ) -> None: ...
    def get(
        self,
        path: str,
        *,
        response_model: type[Any] | None = ...,
        responses: Mapping[int, Any] | None = ...,
        tags: Sequence[str] | None = ...,
        summary: str | None = ...,
        description: str | None = ...,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...
    def post(
        self,
        path: str,
        *,
        response_model: type[Any] | None = ...,
        responses: Mapping[int, Any] | None = ...,
        tags: Sequence[str] | None = ...,
        summary: str | None = ...,
        description: str | None = ...,
    ) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...

class TestClient:
    def __init__(self, app: FastAPI) -> None: ...
    def get(self, url: str, *, headers: Mapping[str, str] | None = ...) -> Response: ...
