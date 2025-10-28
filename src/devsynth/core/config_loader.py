"""Unified configuration loader for DevSynth core modules."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import NotRequired, Optional, Protocol, TypedDict, TypeGuard, cast
from collections.abc import Mapping

try:  # pragma: no cover - optional dependency
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore[assignment]

try:  # pragma: no cover - standard library TOML (Python 3.11+)
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback if stdlib missing
    tomllib = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import toml as _toml_module
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    _toml_module = None  # type: ignore[assignment]


class TyperContextProtocol(Protocol):
    """Subset of the Typer context API used for autocompletion."""

    params: Mapping[str, object]


try:  # pragma: no cover - typer is optional at runtime
    from typer import Context as TyperContext  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - typer is optional at runtime
    TyperContext = TyperContextProtocol


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
    goals: str | None = None
    constraints: str | None = None
    priority: str | None = None
    directories: DirectoryMap | None = None
    features: FeatureFlags | None = None
    resources: JsonObject | None = None
    mvuu: MVUUConfig | None = None

    def __post_init__(self) -> None:
        if self.directories is not None and not _is_directory_map(self.directories):
            raise ValueError(
                "directories must be a mapping of string keys to lists of strings"
            )
        if self.features is not None and not _is_feature_flags(self.features):
            raise ValueError("features must map string keys to boolean flags")
        if self.resources is not None:
            normalized = _coerce_json_object(self.resources)
            if normalized is None:
                raise ValueError(
                    "resources must be a JSON-compatible mapping with bounded depth"
                )
            self.resources = normalized
        if self.mvuu is not None:
            normalized_mvuu = _coerce_mvuu_config(self.mvuu)
            self.mvuu = normalized_mvuu or {}

    def as_dict(self) -> CoreConfigData:
        directories: DirectoryMap = (
            {key: list(value) for key, value in self.directories.items()}
            if self.directories is not None
            else {
                "source": ["src"],
                "tests": ["tests"],
                "docs": ["docs"],
            }
        )
        features: FeatureFlags = (
            dict(self.features) if self.features is not None else {}
        )
        resources: JsonObject = (
            _clone_json_object(self.resources) if self.resources is not None else {}
        )
        mvuu: MVUUConfig = dict(self.mvuu) if self.mvuu is not None else {}
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


_MAX_JSON_DEPTH = 32


def _load_toml_mapping(path: Path) -> Mapping[str, object]:
    if _toml_module is not None:
        return _toml_module.load(path)
    if tomllib is not None:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    raise RuntimeError(
        "TOML parsing requires the 'toml' package or Python 3.11+'s tomllib"
    )


def _dump_toml_mapping(data: Mapping[str, object], handle) -> None:
    if _toml_module is None:
        raise RuntimeError("Writing TOML requires the optional 'toml' dependency")
    _toml_module.dump(data, handle)


def _is_json_value(
    value: object, *, _depth: int = 0, _max_depth: int = _MAX_JSON_DEPTH
) -> TypeGuard[JsonValue]:
    if _depth > _max_depth:
        return False
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(
            _is_json_value(item, _depth=_depth + 1, _max_depth=_max_depth)
            for item in value
        )
    if isinstance(value, dict):
        return _is_json_object(value, _depth=_depth + 1, _max_depth=_max_depth)
    return False


def _is_json_object(
    value: object, *, _depth: int = 0, _max_depth: int = _MAX_JSON_DEPTH
) -> TypeGuard[JsonObject]:
    if _depth > _max_depth or not isinstance(value, dict):
        return False
    for key, item in value.items():
        if not isinstance(key, str) or not _is_json_value(
            item, _depth=_depth + 1, _max_depth=_max_depth
        ):
            return False
    return True


def _is_directory_map(value: object) -> TypeGuard[DirectoryMap]:
    if not isinstance(value, dict):
        return False
    for key, entries in value.items():
        if not isinstance(key, str) or not isinstance(entries, list):
            return False
        if not all(isinstance(entry, str) for entry in entries):
            return False
    return True


def _is_feature_flags(value: object) -> TypeGuard[FeatureFlags]:
    if not isinstance(value, dict):
        return False
    for key, enabled in value.items():
        if not isinstance(key, str) or not isinstance(enabled, bool):
            return False
    return True


def _clone_json_value(
    value: JsonValue, *, _depth: int = 0, _max_depth: int = _MAX_JSON_DEPTH
) -> JsonValue:
    if _depth > _max_depth:
        raise ValueError("JSON value exceeds maximum supported depth")
    if isinstance(value, list):
        return [
            _clone_json_value(item, _depth=_depth + 1, _max_depth=_max_depth)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _clone_json_value(item, _depth=_depth + 1, _max_depth=_max_depth)
            for key, item in value.items()
        }
    return value


def _clone_json_object(
    value: Mapping[str, JsonValue],
    *,
    _depth: int = 0,
    _max_depth: int = _MAX_JSON_DEPTH,
) -> JsonObject:
    if _depth > _max_depth:
        raise ValueError("JSON object exceeds maximum supported depth")
    result: JsonObject = {}
    for key, item in value.items():
        result[key] = _clone_json_value(item, _depth=_depth + 1, _max_depth=_max_depth)
    return result


def _coerce_json_object(value: object) -> JsonObject | None:
    if not _is_json_object(value):
        return None
    mapping = cast(Mapping[str, JsonValue], value)
    try:
        return _clone_json_object(mapping)
    except ValueError:
        return None


def _coerce_issue_provider_config(
    value: object,
) -> IssueProviderConfig | None:
    if not isinstance(value, Mapping):
        return None
    config: IssueProviderConfig = {}
    base_url = value.get("base_url")
    if isinstance(base_url, str):
        config["base_url"] = base_url
    token = value.get("token")
    if isinstance(token, str):
        config["token"] = token
    return config or None


def _coerce_mvuu_issues(value: object) -> MVUUIssuesConfig | None:
    if not isinstance(value, Mapping):
        return None
    issues: MVUUIssuesConfig = {}
    github = _coerce_issue_provider_config(value.get("github"))
    if github is not None:
        issues["github"] = github
    jira = _coerce_issue_provider_config(value.get("jira"))
    if jira is not None:
        issues["jira"] = jira
    return issues or None


def _coerce_mvuu_config(value: object) -> MVUUConfig | None:
    if not isinstance(value, Mapping):
        return None
    config: MVUUConfig = {}
    issues = _coerce_mvuu_issues(value.get("issues"))
    if issues is not None:
        config["issues"] = issues
    return config


def _coerce_core_config_data(raw: Mapping[str, object]) -> CoreConfigData:
    config: CoreConfigData = {}
    project_root = raw.get("project_root")
    if isinstance(project_root, str):
        config["project_root"] = project_root
    structure = raw.get("structure")
    if isinstance(structure, str):
        config["structure"] = structure
    language = raw.get("language")
    if isinstance(language, str):
        config["language"] = language
    goals = raw.get("goals")
    if isinstance(goals, str):
        config["goals"] = goals
    elif goals is None:
        config["goals"] = None
    constraints = raw.get("constraints")
    if isinstance(constraints, str):
        config["constraints"] = constraints
    elif constraints is None:
        config["constraints"] = None
    priority = raw.get("priority")
    if isinstance(priority, str):
        config["priority"] = priority
    elif priority is None:
        config["priority"] = None
    directories = raw.get("directories")
    if _is_directory_map(directories):
        config["directories"] = {key: list(value) for key, value in directories.items()}
    features = raw.get("features")
    if _is_feature_flags(features):
        config["features"] = dict(features)
    resources = raw.get("resources")
    coerced_resources = _coerce_json_object(resources)
    if coerced_resources is not None:
        config["resources"] = coerced_resources
    if "mvuu" in raw:
        mvuu_config = _coerce_mvuu_config(raw.get("mvuu"))
        config["mvuu"] = mvuu_config if mvuu_config is not None else {}
    return config


def _parse_env(cfg: CoreConfig) -> CoreConfigData:
    overrides: CoreConfigData = {}
    for field in (
        "project_root",
        "structure",
        "language",
        "goals",
        "constraints",
        "priority",
    ):
        env_key = f"{_ENV_PREFIX}{field.upper()}"
        value = os.environ.get(env_key)
        if value is not None:
            overrides[field] = value
    return overrides


def _read_yaml_mapping(path: Path) -> dict[str, object] | None:
    if yaml is None or not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return None
    result: dict[str, object] = {}
    for key, value in data.items():
        if isinstance(key, str):
            result[key] = value
    return result


def _load_yaml(path: Path) -> CoreConfigData:
    data = _read_yaml_mapping(path)
    if data is None:
        return {}
    return _coerce_core_config_data(data)


def _load_mvuu_yaml(path: Path) -> MVUUConfig:
    data = _read_yaml_mapping(path)
    if data is None:
        return {}
    mvuu = _coerce_mvuu_config(data)
    return mvuu or {}


def _load_toml(path: Path) -> CoreConfigData:
    if not path.exists():
        return {}
    data: Mapping[str, object] = _load_toml_mapping(path)
    sections: list[Mapping[str, object]] = []
    tool_section = data.get("tool")
    if isinstance(tool_section, Mapping):
        devsynth_section = tool_section.get("devsynth")
        if isinstance(devsynth_section, Mapping):
            sections.append(devsynth_section)
    root_section = data.get("devsynth")
    if isinstance(root_section, Mapping):
        sections.append(root_section)
    for section in sections:
        config = _coerce_core_config_data(section)
        if config:
            return config
    return {}


def _find_project_config(start: Path) -> Path | None:
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
            data = _load_toml_mapping(pyproject)
            if "devsynth" in data.get("tool", {}):
                return pyproject
        except Exception:
            return None
    return None


def load_config(start_path: str | None = None) -> CoreConfig:
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
        config_data.update(_load_yaml(global_yaml))
    elif global_toml.exists():
        config_data.update(_load_toml(global_toml))

    # Project configuration
    project_cfg = _find_project_config(root)
    if project_cfg:
        if project_cfg.suffix in {".yaml", ".yml"}:
            config_data.update(_load_yaml(project_cfg))
        else:
            config_data.update(_load_toml(project_cfg))

    # MVUU configuration
    mvu_cfg = root / ".devsynth" / "mvu.yml"
    if not mvu_cfg.exists():
        mvu_cfg = root / ".devsynth" / "mvu.yaml"
    if mvu_cfg.exists():
        mvuu = _load_mvuu_yaml(mvu_cfg)
        if mvuu:
            config_data["mvuu"] = mvuu

    # Environment overrides
    env_overrides = _parse_env(defaults)
    if env_overrides:
        config_data.update(env_overrides)

    return CoreConfig(**config_data)


def save_global_config(config: CoreConfig, use_toml: bool = False) -> Path:
    """Persist global configuration to the user's home directory."""
    home = Path(os.path.expanduser("~"))
    cfg_dir = home / ".devsynth" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    if use_toml:
        path = cfg_dir / "devsynth.toml"
        with open(path, "w", encoding="utf-8") as f:
            _dump_toml_mapping({"devsynth": config.as_dict()}, f)
    else:
        if yaml is None:
            raise RuntimeError("PyYAML is required to write YAML configuration files")
        path = cfg_dir / "global_config.yaml"
        with open(path, "w") as f:
            yaml.safe_dump(config.as_dict(), f)
    return path


# ---- Typer integration ----
typer: ModuleType | None
try:  # pragma: no cover - optional import
    import typer as _typer_module
except Exception:  # pragma: no cover - optional import
    typer = None
else:
    typer = _typer_module


def config_key_autocomplete(ctx: TyperContext, incomplete: str) -> list[str]:
    """Return config keys matching the partial input for Typer."""
    keys = CoreConfig().__dataclass_fields__.keys()
    return [k for k in keys if k.startswith(incomplete)]
