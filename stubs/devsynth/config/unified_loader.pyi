from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from .loader import ConfigModel

ConfigT = TypeVar("ConfigT", bound=ConfigModel)

@dataclass
class UnifiedConfig(Generic[ConfigT]):
    config: ConfigT
    path: Path
    use_pyproject: bool

    def exists(self) -> bool: ...
    def set_root(self, root: str) -> None: ...
    def set_language(self, language: str) -> None: ...
    def set_goals(self, goals: str) -> None: ...
    def set_kuzu_embedded(self, embedded: bool) -> None: ...
    def save(self) -> Path: ...

class UnifiedConfigLoader:
    @staticmethod
    def load(path: str | Path | None = ...) -> UnifiedConfig[ConfigModel]: ...
    @staticmethod
    def save(config: UnifiedConfig[ConfigModel]) -> Path: ...
