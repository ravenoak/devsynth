from __future__ import annotations

"""Unified configuration loader for DevSynth projects."""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from devsynth import __version__ as project_version
from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import ConfigurationError

import yaml
import toml
from pydantic.dataclasses import dataclass
from dataclasses import field


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
    directories: Dict[str, list[str]] = field(
        default_factory=lambda: {
            "source": ["src"],
            "tests": ["tests"],
            "docs": ["docs"],
        }
    )
    features: Dict[str, bool] = field(
        default_factory=lambda: {"code_generation": False, "test_generation": False}
    )
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
            "directories": self.directories,
            "features": self.features,
            "resources": self.resources or {},
        }


# Module level logger
logger = DevSynthLogger(__name__)


def _find_config_path(start: Path) -> Optional[Path]:
    """Return the configuration file path if one exists."""
    yaml_path = start / ".devsynth" / "devsynth.yml"
    if yaml_path.exists():
        return yaml_path

    toml_path = start / "pyproject.toml"
    if toml_path.exists():
        try:
            data = toml.load(toml_path)
            if "devsynth" in data.get("tool", {}):
                return toml_path
        except Exception as exc:
            logger.error("Malformed TOML configuration: %s", exc)
            raise ConfigurationError(
                "Malformed TOML configuration", config_key=str(toml_path)
            ) from exc

    return None


def load_config(path: Optional[Path] = None) -> ConfigModel:
    """Load configuration from YAML or TOML."""
    root = path or Path(os.getcwd())
    cfg_path = _find_config_path(root)

    defaults = ConfigModel(project_root=str(root))
    data: Dict[str, Any] = defaults.as_dict()

    if cfg_path is not None:
        if cfg_path.name.endswith(".yml") or cfg_path.name.endswith(".yaml"):
            try:
                with open(cfg_path, "r") as f:
                    parsed = yaml.safe_load(f) or {}
            except yaml.YAMLError as exc:  # pragma: no cover - protective branch
                logger.error("Malformed YAML configuration: %s", exc)
                raise ConfigurationError(
                    "Malformed YAML configuration", config_key=str(cfg_path)
                ) from exc
        else:
            try:
                tdata = toml.load(cfg_path)
                parsed = tdata.get("tool", {}).get("devsynth", {})
            except Exception as exc:  # pragma: no cover - toml load errors
                logger.error("Malformed TOML configuration: %s", exc)
                raise ConfigurationError(
                    "Malformed TOML configuration", config_key=str(cfg_path)
                ) from exc

        data.update(parsed)

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
