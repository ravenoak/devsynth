from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Optional, ParamSpec, Protocol, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

class StepParser(Protocol):
    def __call__(self, step: str) -> Mapping[str, Any]: ...

StepExpression = str | StepParser

class _ParsersModule:
    def parse(
        self,
        expression: str,
        converters: Mapping[str, Callable[[str], Any]] | None = ...,
    ) -> StepParser: ...
    def cfparse(
        self,
        expression: str,
        converters: Mapping[str, Callable[[str], Any]] | None = ...,
    ) -> StepParser: ...

parsers: _ParsersModule

def scenario(
    feature: str,
    name: str,
    *,
    example_converters: Mapping[str, Callable[[str], Any]] | None = ...,
    encoding: str = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def scenarios(
    feature_paths: str | Sequence[str],
    *,
    example_converters: Mapping[str, Callable[[str], Any]] | None = ...,
    encoding: str = ...,
) -> None: ...
def given(
    step: StepExpression,
    *,
    target_fixture: str | None = ...,
    converters: Mapping[str, Callable[[str], Any]] | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def when(
    step: StepExpression,
    *,
    target_fixture: str | None = ...,
    converters: Mapping[str, Callable[[str], Any]] | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def then(
    step: StepExpression,
    *,
    target_fixture: str | None = ...,
    converters: Mapping[str, Callable[[str], Any]] | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...
def step(
    step: StepExpression,
    *,
    target_fixture: str | None = ...,
    converters: Mapping[str, Callable[[str], Any]] | None = ...,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...

__all__ = [
    "given",
    "when",
    "then",
    "step",
    "scenario",
    "scenarios",
    "parsers",
]
