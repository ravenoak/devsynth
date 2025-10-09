from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence
from typing import (
    Any,
    Generic,
    Literal,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    overload,
)

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")

ScopeName = Literal["function", "class", "module", "package", "session"]

MarkDecorator: TypeAlias = Callable[[Callable[..., Any]], Callable[..., Any]]

class _MarkProxy:
    def __call__(self, *args: Any, **kwargs: Any) -> MarkDecorator: ...
    def __getattr__(self, name: str) -> MarkDecorator: ...
    def parametrize(
        self,
        argnames: str | Sequence[str],
        argvalues: Sequence[Any],
        *,
        indirect: bool | Sequence[str] = ...,
        ids: Sequence[str] | Callable[[Any], str] | None = ...,
        scope: ScopeName | None = ...,
    ) -> MarkDecorator: ...

mark: _MarkProxy

def fixture(
    function: Callable[P, R] | None = ...,
    *,
    scope: ScopeName | None = ...,
    params: Sequence[Any] | None = ...,
    autouse: bool = ...,
    ids: Sequence[str] | Callable[[Any], str] | None = ...,
    name: str | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def hookimpl(
    *,
    hookwrapper: bool | None = ...,
    optionalhook: bool | None = ...,
    tryfirst: bool | None = ...,
    trylast: bool | None = ...,
    specname: str | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def hookimpl_check(func: Callable[P, R]) -> Callable[P, R]: ...
def hookspec(
    *,
    firstresult: bool | None = ...,
    historic: bool | None = ...,
    warn_on_impl: bool | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def raises(
    expected_exception: type[BaseException] | tuple[type[BaseException], ...],
    *args: Any,
    **kwargs: Any,
) -> Any: ...
def skip(reason: str | None = None) -> None: ...
def skipif(condition: bool, reason: str | None = None) -> None: ...
def fail(msg: str, pytrace: bool = ...) -> None: ...
def param(
    *values: Any,
    marks: MarkDecorator | Sequence[MarkDecorator] | None = ...,
    id: str | None = ...,
) -> Any: ...
def approx(
    expected: Any,
    *,
    rel: float | None = ...,
    abs: float | None = ...,
    nan_ok: bool = ...,
) -> Any: ...
def register_assert_rewrite(*modules: str) -> None: ...

class MonkeyPatch:
    def setattr(
        self,
        target: Any,
        name: str | None = None,
        value: Any = ...,
        raising: bool = ...,
    ) -> None: ...
    def delattr(
        self, target: Any, name: str | None = None, raising: bool = ...
    ) -> None: ...
    def setitem(
        self,
        mapping: MutableMapping[Any, Any],
        name: Any,
        value: Any,
    ) -> None: ...
    def delitem(
        self, mapping: MutableMapping[Any, Any], name: Any, raising: bool = ...
    ) -> None: ...
    def setenv(self, name: str, value: str, prepend: bool = ...) -> None: ...
    def delenv(self, name: str, raising: bool = ...) -> None: ...
    def syspath_prepend(self, path: str) -> None: ...
    def chdir(self, path: str | bytes) -> None: ...

class CaptureFixture(Generic[T]):
    def readouterr(self) -> tuple[T, T]: ...

class LogCaptureFixture:
    def clear(self) -> None: ...
    @property
    def text(self) -> str: ...

class FixtureRequest:
    config: Config
    fspath: Any
    node: Any

    def getfixturevalue(self, name: str) -> Any: ...

class TempPathFactory:
    def mktemp(self, basename: str, numbered: bool = ...) -> Any: ...

class Pytester:
    path: Any

    def makepyfile(self, *args: Any, **kwargs: Any) -> Any: ...

class Config:
    invocation_params: Any

    def getoption(self, name: str, default: Any = ...) -> Any: ...
    def getini(self, name: str) -> Any: ...
    def addinivalue_line(self, name: str, line: str) -> None: ...

class Parser:
    def addoption(self, *args: Any, **kwargs: Any) -> None: ...

class CallInfo(Generic[T]):
    excinfo: Any
    result: T

class Item:
    config: Config
    nodeid: str

    def add_marker(self, mark: MarkDecorator, append: bool = ...) -> None: ...

class CollectReport:
    result: Sequence[Item]

class Collector:
    config: Config

    def collect(self) -> Sequence[Item]: ...

class Session:
    items: list[Item]
    config: Config

class ExitCode(int):
    OK: int
    TESTS_FAILED: int
    INTERRUPTED: int
    INTERNAL_ERROR: int
    USAGE_ERROR: int

def main(args: Sequence[str] | None = None) -> ExitCode: ...
def console_main() -> ExitCode: ...

collect = ...
ItemType = Item

__all__ = [
    "MarkDecorator",
    "MarkGenerator",
    "CaptureFixture",
    "FixtureRequest",
    "MonkeyPatch",
    "LogCaptureFixture",
    "TempPathFactory",
    "Config",
    "Parser",
    "CallInfo",
    "Item",
    "Collector",
    "Session",
    "ExitCode",
    "approx",
    "fail",
    "fixture",
    "hookimpl",
    "hookimpl_check",
    "hookspec",
    "main",
    "mark",
    "param",
    "raises",
    "register_assert_rewrite",
    "skip",
    "skipif",
]
