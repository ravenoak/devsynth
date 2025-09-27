"""Unified configuration loader for DevSynth core modules."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, Optional, TypedDict, cast

import toml
import yaml

if TYPE_CHECKING:  # pragma: no cover - used for typing only
    from dataclasses import dataclass
else:  # pragma: no cover - runtime validation uses Pydantic dataclass
    from pydantic.dataclasses import dataclass


JsonPrimitive = str | int | float | bool | None
JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
DirectoryMap = dict[str, list[str]]
FeatureFlags = dict[str, bool]


class IssueProviderConfig(TypedDict, total=False):
    """Configuration describing how to authenticate with an issue provider."""

    base_url: str
    token: str


class MVUUIssuesConfig(TypedDict, total=False):
    """Mapping of MVUU issue providers that may be configured."""

    github: IssueProviderConfig
    jira: IssueProviderConfig


class MVUUConfig(TypedDict, total=False):
    """MVUU-specific configuration options."""

    issues: NotRequired[MVUUIssuesConfig]


class CoreConfigData(TypedDict, total=False):
    """Dictionary representation of :class:`CoreConfig`."""

    project_root: str
    structure: str
    language: str
    goals: str | None
    constraints: str | None
    priority: str | None
    directories: DirectoryMap
    features: FeatureFlags
    resources: JsonObject
    mvuu: MVUUConfig


@dataclass
class CoreConfig:
    """Dataclass representing configuration options."""

    project_root: str = "."
    structure: str = "single_package"
    language: str = "python"
    goals: Optional[str] = None
    constraints: Optional[str] = None
    priority: Optional[str] = None
    directories: DirectoryMap | None = None
    features: FeatureFlags | None = None
    resources: JsonObject | None = None
    mvuu: MVUUConfig | None = None

    def as_dict(self) -> CoreConfigData:
        directories: DirectoryMap = self.directories or {
            "source": ["src"],
            "tests": ["tests"],
            "docs": ["docs"],
        }
        features: FeatureFlags = self.features or {}
        resources: JsonObject = self.resources or {}
        mvuu: MVUUConfig = self.mvuu or {}
        return {
            "project_root": self.project_root,
            "structure": self.structure,
            "language": self.language,
            "goals": self.goals,
            "constraints": self.constraints,
            "priority": self.priority,
            "directories": directories,
            "features": features,
            "resources": resources,
            "mvuu": mvuu,
        }


_ENV_PREFIX = "DEVSYNTH_"


def _parse_env(cfg: CoreConfig) -> CoreConfigData:
    updates: JsonObject = {}
    for field in cfg.as_dict().keys():
        env_key = f"{_ENV_PREFIX}{field.upper()}"
        value = os.environ.get(env_key)
        if value is not None:
            if isinstance(getattr(cfg, field), bool):
                updates[field] = value.strip().lower() in {"1", "true", "yes"}
            else:
                updates[field] = value
    return cast(CoreConfigData, updates)


def _load_yaml(path: Path) -> JsonObject:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict):
        return cast(JsonObject, data)
    return {}


def _load_toml(path: Path) -> JsonObject:
    if not path.exists():
        return {}
    data = toml.load(path)
    tool_section = data.get("tool")
    if isinstance(tool_section, dict):
        devsynth_section = tool_section.get("devsynth")
        if isinstance(devsynth_section, dict):
            return cast(JsonObject, devsynth_section)
    root_section = data.get("devsynth")
    if isinstance(root_section, dict):
        return cast(JsonObject, root_section)
    return {}


def _find_project_config(start: Path) -> Optional[Path]:
    yaml_path = start / ".devsynth" / "project.yaml"
    if yaml_path.exists():
        return yaml_path
    legacy_yaml = start / ".devsynth" / "devsynth.yml"
    if legacy_yaml.exists():
        return legacy_yaml
    toml_path = start / "devsynth.toml"
    if toml_path.exists():
        return toml_path
    pyproject = start / "pyproject.toml"
    if pyproject.exists():
        try:
            data = toml.load(pyproject)
            if "devsynth" in data.get("tool", {}):
                return pyproject
        except Exception:
            return None
    return None


def load_config(start_path: Optional[str] = None) -> CoreConfig:
    """Load configuration merging global, project and environment settings."""

    root = Path(start_path or os.getcwd())

    defaults = CoreConfig(project_root=str(root))
    config_data: CoreConfigData = defaults.as_dict()

    # Global configuration
    home = Path(os.path.expanduser("~"))
    global_dir = home / ".devsynth" / "config"
    global_yaml = global_dir / "global_config.yaml"
    global_toml = global_dir / "devsynth.toml"
    if global_yaml.exists():
        config_data.update(cast(CoreConfigData, _load_yaml(global_yaml)))
    elif global_toml.exists():
        config_data.update(cast(CoreConfigData, _load_toml(global_toml)))

    # Project configuration
    project_cfg = _find_project_config(root)
    if project_cfg:
        if project_cfg.suffix in {".yaml", ".yml"}:
            config_data.update(cast(CoreConfigData, _load_yaml(project_cfg)))
        else:
            config_data.update(cast(CoreConfigData, _load_toml(project_cfg)))

    # MVUU configuration
    mvu_cfg = root / ".devsynth" / "mvu.yml"
    if not mvu_cfg.exists():
        mvu_cfg = root / ".devsynth" / "mvu.yaml"
    if mvu_cfg.exists():
        config_data["mvuu"] = cast(MVUUConfig, _load_yaml(mvu_cfg))

    # Environment overrides
    config_data.update(_parse_env(defaults))

    return CoreConfig(**config_data)


def save_global_config(config: CoreConfig, use_toml: bool = False) -> Path:
    """Persist global configuration to the user's home directory."""
    home = Path(os.path.expanduser("~"))
    cfg_dir = home / ".devsynth" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    if use_toml:
        path = cfg_dir / "devsynth.toml"
        with open(path, "w") as f:
            toml.dump({"devsynth": config.as_dict()}, f)
    else:
        path = cfg_dir / "global_config.yaml"
        with open(path, "w") as f:
            yaml.safe_dump(config.as_dict(), f)
    return path


# ---- Typer integration ----
try:  # pragma: no cover - optional import
    import typer
except Exception:  # pragma: no cover - optional import
    typer = None


def config_key_autocomplete(ctx: "typer.Context", incomplete: str) -> list[str]:
    """Return config keys matching the partial input for Typer."""
    keys = CoreConfig().__dataclass_fields__.keys()
    return [k for k in keys if k.startswith(incomplete)]
