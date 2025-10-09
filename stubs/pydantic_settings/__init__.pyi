from __future__ import annotations

from typing import Any, Mapping, MutableMapping, TypeVar

__all__ = ["BaseSettings", "SettingsConfigDict"]

_T = TypeVar("_T")

SettingsConfigDict = MutableMapping[str, Any]

class BaseSettings:
    model_config: SettingsConfigDict

    def __init__(self, **values: Any) -> None: ...
    def model_dump(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]: ...
