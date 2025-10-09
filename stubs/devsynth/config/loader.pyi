from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

class ConfigModel:
    project_root: Optional[str]
    version: str
    structure: str
    language: str
    goals: Optional[str]
    constraints: Optional[str]
    priority: Optional[str]
    directories: Dict[str, list[str]]
    features: Dict[str, bool]
    memory_store_type: str
    kuzu_embedded: bool
    offline_mode: bool
    resources: Dict[str, Any] | None
    edrr_settings: Dict[str, Any]
    wsde_settings: Dict[str, Any]
    uxbridge_settings: Dict[str, Any]

    def __init__(
        self,
        project_root: Optional[str] = ...,
        *,
        version: str = ...,
        structure: str = ...,
        language: str = ...,
        goals: Optional[str] = ...,
        constraints: Optional[str] = ...,
        priority: Optional[str] = ...,
        directories: Dict[str, list[str]] | None = ...,
        features: Dict[str, bool] | None = ...,
        memory_store_type: str = ...,
        kuzu_embedded: bool = ...,
        offline_mode: bool = ...,
        resources: Dict[str, Any] | None = ...,
        edrr_settings: Dict[str, Any] | None = ...,
        wsde_settings: Dict[str, Any] | None = ...,
        uxbridge_settings: Dict[str, Any] | None = ...,
    ) -> None: ...
    def as_dict(self) -> Dict[str, Any]: ...

def _find_config_path(start: Path) -> Path | None: ...
def load_config(path: str | Path | None = ...) -> ConfigModel: ...
def save_config(
    config: ConfigModel,
    use_pyproject: bool = ...,
    path: Optional[str] = ...,
) -> Path: ...
def config_key_autocomplete(ctx: object, incomplete: str) -> list[str]: ...
