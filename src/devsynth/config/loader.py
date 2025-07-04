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
        default_factory=lambda: {
            "wsde_collaboration": False,
            "dialectical_reasoning": False,
            "code_generation": False,
            "test_generation": False,
            "documentation_generation": False,
            "experimental_features": False,
            "edrr_framework": False,
            "micro_edrr_cycles": False,
            "recursive_edrr": False,
            "wsde_peer_review": False,
            "wsde_consensus_voting": False,
            "uxbridge_webui": False,
            "uxbridge_agent_api": False,
        }
    )
    memory_store_type: str = "memory"
    offline_mode: bool = False
    resources: Dict[str, Any] | None = None
    edrr_settings: Dict[str, Any] = field(
        default_factory=lambda: {
            "max_recursion_depth": 3,
            "enable_memory_integration": True,
            "termination_threshold": 0.8,
            "phase_weights": {
                "expand": 1.0,
                "differentiate": 1.0,
                "refine": 1.0,
                "retrospect": 1.0,
            },
        }
    )
    wsde_settings: Dict[str, Any] = field(
        default_factory=lambda: {
            "team_size": 5,
            "peer_review_threshold": 0.7,
            "consensus_threshold": 0.6,
            "voting_weights": {
                "expertise": 0.6,
                "historical": 0.3,
                "primus": 0.1,
            },
        }
    )
    uxbridge_settings: Dict[str, Any] = field(
        default_factory=lambda: {
            "default_interface": "cli",
            "webui_port": 8501,
            "api_port": 8000,
            "enable_authentication": False,
        }
    )

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
            "memory_store_type": self.memory_store_type,
            "offline_mode": self.offline_mode,
            "resources": self.resources or {},
            "edrr_settings": self.edrr_settings,
            "wsde_settings": self.wsde_settings,
            "uxbridge_settings": self.uxbridge_settings,
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
        except Exception as exc:
            logger.error("Malformed TOML configuration: %s", exc)
            raise ConfigurationError(
                "Malformed TOML configuration", config_key=str(toml_path)
            ) from exc

    proj_yaml = start / ".devsynth" / "project.yaml"
    if proj_yaml.exists():
        return proj_yaml

    yaml_path = start / ".devsynth" / "devsynth.yml"
    if yaml_path.exists():
        return yaml_path

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
                    f"Malformed YAML configuration in {cfg_path}. Please check the syntax and formatting.",
                    config_key=str(cfg_path)
                ) from exc
        else:
            try:
                tdata = toml.load(cfg_path)
                parsed = tdata.get("tool", {}).get("devsynth", {})
            except Exception as exc:  # pragma: no cover - toml load errors
                logger.error("Malformed TOML configuration: %s", exc)
                raise ConfigurationError(
                    f"Malformed TOML configuration in {cfg_path}. Please check the syntax and formatting.",
                    config_key=str(cfg_path)
                ) from exc

        data.update(parsed)

    # Validate configuration before creating the model
    try:
        config = ConfigModel(**data)
    except Exception as exc:
        logger.error("Invalid configuration values: %s", exc)
        raise ConfigurationError(
            f"Invalid configuration values: {exc}. Please check the configuration documentation for valid options.",
            config_key="validation"
        ) from exc

    # Validate version
    if config.version != ConfigModel.version:
        logger.warning(
            "Configuration version %s does not match expected %s",
            config.version,
            ConfigModel.version,
        )

    # Validate EDRR settings
    if config.features.get("edrr_framework", False):
        if config.edrr_settings.get("max_recursion_depth", 0) < 1:
            logger.warning("max_recursion_depth should be at least 1, setting to default (3)")
            config.edrr_settings["max_recursion_depth"] = 3

        if not isinstance(config.edrr_settings.get("phase_weights", {}), dict):
            logger.warning("phase_weights should be a dictionary, setting to default values")
            config.edrr_settings["phase_weights"] = {
                "expand": 1.0,
                "differentiate": 1.0,
                "refine": 1.0,
                "retrospect": 1.0,
            }

    # Validate WSDE settings
    if config.features.get("wsde_collaboration", False):
        if config.wsde_settings.get("team_size", 0) < 2:
            logger.warning("team_size should be at least 2, setting to default (5)")
            config.wsde_settings["team_size"] = 5

        if not isinstance(config.wsde_settings.get("voting_weights", {}), dict):
            logger.warning("voting_weights should be a dictionary, setting to default values")
            config.wsde_settings["voting_weights"] = {
                "expertise": 0.6,
                "historical": 0.3,
                "primus": 0.1,
            }

    # Validate UXBridge settings
    if config.features.get("uxbridge_webui", False) or config.features.get("uxbridge_agent_api", False):
        if config.uxbridge_settings.get("webui_port", 0) < 1024 or config.uxbridge_settings.get("webui_port", 0) > 65535:
            logger.warning("webui_port should be between 1024 and 65535, setting to default (8501)")
            config.uxbridge_settings["webui_port"] = 8501

        if config.uxbridge_settings.get("api_port", 0) < 1024 or config.uxbridge_settings.get("api_port", 0) > 65535:
            logger.warning("api_port should be between 1024 and 65535, setting to default (8000)")
            config.uxbridge_settings["api_port"] = 8000

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
