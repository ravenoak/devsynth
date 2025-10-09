from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Mapping, Sequence, Tuple, TypeVar

__all__ = [
    "BaseModel",
    "Field",
    "FieldValidationInfo",
    "ValidationError",
    "conint",
    "field_validator",
]

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])

def Field(
    default: Any = ...,
    *,
    default_factory: Callable[[], Any] | None = ...,
    alias: str | None = ...,
    title: str | None = ...,
    description: str | None = ...,
    examples: Sequence[Any] | None = ...,
    min_length: int | None = ...,
    max_length: int | None = ...,
    ge: float | None = ...,
    gt: float | None = ...,
    le: float | None = ...,
    lt: float | None = ...,
    pattern: str | None = ...,
) -> Any: ...

class BaseModel:
    """Minimal stub of pydantic.BaseModel for type-checking."""

    model_config: Mapping[str, Any]

    def __init__(self, **data: Any) -> None: ...
    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...
    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...

class FieldValidationInfo:
    """Validation context passed to field validators."""

    data: Mapping[str, Any] | None
    field_name: str | None
    config: Mapping[str, Any] | None

class ValidationError(Exception):
    def errors(self) -> Sequence[Mapping[str, Any]]: ...

def field_validator(*fields: str, **kwargs: Any) -> Callable[[_F], _F]: ...
def conint(
    *,
    ge: int | None = ...,
    gt: int | None = ...,
    le: int | None = ...,
    lt: int | None = ...,
) -> type[int]: ...
