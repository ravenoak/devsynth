from __future__ import annotations

from collections.abc import Callable
from typing import Any, Iterable, Mapping, ParamSpec, Pattern, Protocol, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

GET: Any
POST: Any
PUT: Any
DELETE: Any
HEAD: Any
PATCH: Any
OPTIONS: Any

class BaseResponse: ...
class Response(BaseResponse): ...

class Request(Protocol):
    body: bytes | str | None

class Call(Protocol):
    request: Request

class RequestsMock:
    calls: list[Call]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __call__(self, func: Callable[P, R]) -> Callable[P, R]: ...
    def __enter__(self) -> RequestsMock: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> bool: ...
    def add(
        self,
        method: Any,
        url: str,
        body: Any | None = ...,
        headers: Mapping[str, str] | None = ...,
        stream: Iterable[bytes] | None = ...,
        status: int = ...,
        content_type: str | None = ...,
        match_querystring: bool = ...,
        **kwargs: Any,
    ) -> Response: ...
    def add_passthru(self, url: str | Pattern[str]) -> None: ...
    def remove_passthru(self, url: str | Pattern[str]) -> None: ...
    def reset(self) -> None: ...
    def assert_call_count(self, url: str, count: int) -> None: ...

def activate(
    func: Callable[P, R] | None = None,
    registry: RequestsMock | None = ...,
    assert_all_requests_are_fired: bool = ...,
    **kwargs: Any,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def requests_mock(**kwargs: Any) -> RequestsMock: ...

__all__ = [
    "RequestsMock",
    "Response",
    "Call",
    "activate",
    "requests_mock",
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "HEAD",
    "PATCH",
    "OPTIONS",
]
