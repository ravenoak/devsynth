from __future__ import annotations

"""Unified configuration loader for DevSynth projects."""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from devsynth import __version__ as project_version
from devsynth.logging_setup import DevSynthLogger

import yaml
import toml
from pydantic.dataclasses import dataclass


@dataclass
class ConfigModel:
    """Dataclass representing project configuration."""

    project_root: Optional[str] = None
    version: str = "1.0"
    structure: str = "single_package"
    language: str = "python"
    goals: Optional[str] = None
    constraints: Optional[str] = None
    priority: Optional[str] = None
    directories: Dict[str, list[str]] | None = None
    features: Dict[str, bool] | None = None
    resources: Dict[str, Any] | None = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "project_root": self.project_root,
            "version": self.version,
            "structure": self.structure,
            "language": self.language,
            "goals": self.goals,
            "constraints": self.constraints,
            "priority": self.priority,
            "directories": self.directories
            or {
                "source": ["src"],
                "tests": ["tests"],
                "docs": ["docs"],
            },
            "features": self.features or {},
            "resources": self.resources or {},
        }


# Module level logger
logger = DevSynthLogger(__name__)


def _find_config_path(start: Path) -> Optional[Path]:
    """Return the configuration file path if one exists."""
    toml_path = start / "pyproject.toml"
    if toml_path.exists():
        try:
            data = toml.load(toml_path)
            if "devsynth" in data.get("tool", {}):
                return toml_path
        except Exception:
            return None

    yaml_path = start / ".devsynth" / "devsynth.yml"
    if yaml_path.exists():
        return yaml_path

    return None


def load_config(path: Optional[Path] = None) -> ConfigModel:
    """Load configuration from YAML or TOML."""
    root = path or Path(os.getcwd())
    cfg_path = _find_config_path(root)

    data: Dict[str, Any] = {}
    if cfg_path is None:
        return ConfigModel(project_root=str(root))

    if cfg_path.name.endswith(".yml") or cfg_path.name.endswith(".yaml"):
        with open(cfg_path, "r") as f:
            data = yaml.safe_load(f) or {}
    else:
        tdata = toml.load(cfg_path)
        data = tdata.get("tool", {}).get("devsynth", {})
    if "project_root" not in data:
        data["project_root"] = str(root)

    config = ConfigModel(**data)
    if config.version != ConfigModel.version:
        logger.warning(
            "Configuration version %s does not match expected %s",
            config.version,
            ConfigModel.version,
        )
    return config


def save_config(
    config: ConfigModel,
    use_pyproject: bool = False,
    path: Optional[str] = None,
) -> Path:
    """Persist configuration to disk."""
    root = Path(path or config.project_root or os.getcwd())
    if use_pyproject:
        pyproject = root / "pyproject.toml"
        tdata: Dict[str, Any] = {}
        if pyproject.exists():
            tdata = toml.load(pyproject)
        tdata.setdefault("tool", {})["devsynth"] = config.as_dict()
        with open(pyproject, "w") as f:
            toml.dump(tdata, f)
        return pyproject
    else:
        dev_dir = root / ".devsynth"
        os.makedirs(dev_dir, exist_ok=True)
        cfg_path = dev_dir / "devsynth.yml"
        with open(cfg_path, "w") as f:
            yaml.safe_dump(config.as_dict(), f)
        return cfg_path


try:  # pragma: no cover - optional dependency
    import typer
except Exception:  # pragma: no cover - optional dependency
    typer = None


def config_key_autocomplete(ctx: "typer.Context", incomplete: str):
    """Autocomplete configuration keys for Typer CLI."""
    keys = ConfigModel().__dataclass_fields__.keys()
    return [k for k in keys if k.startswith(incomplete)]
