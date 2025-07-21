"""
Configuration module for DevSynth.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any

import yaml
import toml

from .loader import ConfigModel, config_key_autocomplete, load_config, save_config
from .unified_loader import UnifiedConfig, UnifiedConfigLoader
from .settings import _settings, get_llm_settings, get_settings, load_dotenv

_PROJECT_CONFIG: ConfigModel = load_config()
PROJECT_CONFIG = _PROJECT_CONFIG


def get_project_config(path: Path | None = None) -> ConfigModel:
    """Return the cached project configuration."""
    global _PROJECT_CONFIG
    if path is not None or _PROJECT_CONFIG is None:
        _PROJECT_CONFIG = load_config(path)
    return _PROJECT_CONFIG


# Expose settings as module-level variables for backward compatibility
MEMORY_STORE_TYPE = _settings.memory_store_type
MEMORY_FILE_PATH = _settings.memory_file_path
KUZU_DB_PATH = _settings.kuzu_db_path
KUZU_EMBEDDED = _settings.kuzu_embedded
MAX_CONTEXT_SIZE = _settings.max_context_size
CONTEXT_EXPIRATION_DAYS = _settings.context_expiration_days

# Vector store settings
VECTOR_STORE_ENABLED = _settings.vector_store_enabled
CHROMADB_COLLECTION_NAME = _settings.chromadb_collection_name
CHROMADB_DISTANCE_FUNC = _settings.chromadb_distance_func
ENABLE_CHROMADB = _settings.enable_chromadb

# LLM settings
LLM_PROVIDER = _settings.provider_type
LLM_API_BASE = _settings.lm_studio_endpoint
LLM_MODEL = os.environ.get("DEVSYNTH_LLM_MODEL", "gpt-3.5-turbo")
LLM_MAX_TOKENS = int(os.environ.get("DEVSYNTH_LLM_MAX_TOKENS", "2000"))
LLM_TEMPERATURE = float(os.environ.get("DEVSYNTH_LLM_TEMPERATURE", "0.7"))
LLM_AUTO_SELECT_MODEL = os.environ.get(
    "DEVSYNTH_LLM_AUTO_SELECT_MODEL", "true"
).lower() in ["true", "1", "yes"]

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


@dataclass
class ProjectUnifiedConfig(UnifiedConfig):
    """Configuration wrapper for project.yaml or pyproject.toml."""

    @classmethod
    def load(cls, path: Path | None = None) -> "ProjectUnifiedConfig":
        """Load and validate a project configuration."""
        root = Path(path or os.getcwd())
        yaml_path = root / ".devsynth" / "project.yaml"
        use_pyproject = False
        data: dict[str, Any] = {}

        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            toml_path = root / "pyproject.toml"
            if toml_path.exists():
                tdata = toml.load(toml_path)
                data = tdata.get("tool", {}).get("devsynth", {})
                yaml_path = toml_path
                use_pyproject = True

        schema_file = (
            Path(__file__).resolve().parent.parent / "schemas" / "project_schema.json"
        )
        try:
            import json
            import jsonschema

            with open(schema_file, "r", encoding="utf-8") as sf:
                schema = json.load(sf)

            required_keys = set(schema.get("required", []))
            if required_keys.intersection(data.keys()):
                jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as err:  # type: ignore
            logger.error("Project configuration validation failed: %s", err)
            raise DevSynthError(
                "Configuration issues detected. Run 'devsynth init' to generate defaults."
            ) from err
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not validate project config: %s", exc)

        cfg = ConfigModel(project_root=str(root))
        allowed = cfg.__dataclass_fields__
        subset: dict[str, Any] = {}
        for key, value in data.items():
            if key not in allowed:
                continue
            field = allowed[key]
            if field.type in (str, "str") and not isinstance(value, str):
                continue
            subset[key] = value
        cfg = ConfigModel(**{**cfg.as_dict(), **subset})
        return cls(cfg, yaml_path, use_pyproject)

    def save(self) -> Path:  # type: ignore[override]
        if self.use_pyproject:
            tdata: dict[str, Any] = {}
            if self.path.exists():
                tdata = toml.load(self.path)
            tdata.setdefault("tool", {})["devsynth"] = self.config.as_dict()
            with open(self.path, "w", encoding="utf-8") as f:
                toml.dump(tdata, f)
            return self.path

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.config.as_dict(), f)
        return self.path


def load_project_config(path: Path | None = None) -> ProjectUnifiedConfig:
    """Load project configuration from project.yaml or pyproject.toml."""
    return ProjectUnifiedConfig.load(path)


__all__ = [
    # Functions
    "get_settings",
    "get_llm_settings",
    "load_dotenv",
    "load_config",
    "save_config",
    "get_project_config",
    "load_project_config",
    "config_key_autocomplete",
    "UnifiedConfigLoader",
    "ConfigModel",
    "ProjectUnifiedConfig",
    "PROJECT_CONFIG",
    # Memory settings
    "MEMORY_STORE_TYPE",
    "MEMORY_FILE_PATH",
    "KUZU_DB_PATH",
    "KUZU_EMBEDDED",
    "MAX_CONTEXT_SIZE",
    "CONTEXT_EXPIRATION_DAYS",
    # Vector store settings
    "VECTOR_STORE_ENABLED",
    "CHROMADB_COLLECTION_NAME",
    "CHROMADB_DISTANCE_FUNC",
    "ENABLE_CHROMADB",
    # LLM settings
    "LLM_PROVIDER",
    "LLM_API_BASE",
    "LLM_MODEL",
    "LLM_MAX_TOKENS",
    "LLM_TEMPERATURE",
    "LLM_AUTO_SELECT_MODEL",
]
