from __future__ import annotations

from pathlib import Path

from .loader import ConfigModel, config_key_autocomplete, load_config, save_config
from .unified_loader import UnifiedConfig, UnifiedConfigLoader

__all__ = [
    "ConfigModel",
    "UnifiedConfig",
    "UnifiedConfigLoader",
    "ProjectUnifiedConfig",
    "load_config",
    "save_config",
    "get_project_config",
    "load_project_config",
    "config_key_autocomplete",
    "PROJECT_CONFIG",
]

PROJECT_CONFIG: ConfigModel

def get_project_config(path: Path | None = ...) -> ConfigModel: ...

class ProjectUnifiedConfig(UnifiedConfig[ConfigModel]):
    config: ConfigModel
    path: Path
    use_pyproject: bool

    @classmethod
    def load(cls, path: Path | None = ...) -> ProjectUnifiedConfig: ...
    def save(self) -> Path: ...

def load_project_config(path: Path | None = ...) -> ProjectUnifiedConfig: ...
