"""Utilities that preserve typing information when applying third-party decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")


def ensure_typed_decorator(
    decorator: Callable[[Callable[P, R]], Any],
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap a decorator that would otherwise erase typing information."""

    def wrapper(func: Callable[P, R]) -> Callable[P, R]:
        return cast(Callable[P, R], decorator(func))

    return wrapper


def typed_freeze_time(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Return a typed ``freeze_time`` decorator for use on pytest tests."""

    from freezegun import freeze_time

    raw = freeze_time(*args, **kwargs)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        return cast(Callable[P, R], raw(func))

    return decorator
