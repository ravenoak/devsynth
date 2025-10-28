from __future__ import annotations

"""Configuration module for DevSynth."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import toml  # type: ignore[import-untyped]  # TODO(2025-12-20): Adopt typed tomllib or bundle stubs.
import yaml

from .loader import ConfigModel, config_key_autocomplete, load_config, save_config
from .settings import _settings, get_llm_settings, get_settings, load_dotenv
from .unified_loader import UnifiedConfig, UnifiedConfigLoader

_PROJECT_CONFIG: ConfigModel = load_config()
PROJECT_CONFIG: ConfigModel = _PROJECT_CONFIG


def get_project_config(path: Path | None = None) -> ConfigModel:
    """Return the cached project configuration."""
    global _PROJECT_CONFIG, PROJECT_CONFIG
    if path is not None:
        _PROJECT_CONFIG = load_config(path)
        PROJECT_CONFIG = _PROJECT_CONFIG
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
# Default values that can be overridden via ``configure_llm_settings``
LLM_MODEL = "gpt-3.5-turbo"
LLM_MAX_TOKENS = 2000
LLM_TEMPERATURE = 0.7
LLM_AUTO_SELECT_MODEL = True


def configure_llm_settings() -> None:
    """Configure LLM settings from environment variables.

    This helper defers all environment variable reads until explicitly
    invoked, preventing environment leakage at import time and enabling
    tests to control values via ``monkeypatch``.
    """

    global LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE, LLM_AUTO_SELECT_MODEL

    LLM_MODEL = os.environ.get("DEVSYNTH_LLM_MODEL", LLM_MODEL)
    LLM_MAX_TOKENS = int(os.environ.get("DEVSYNTH_LLM_MAX_TOKENS", str(LLM_MAX_TOKENS)))
    LLM_TEMPERATURE = float(
        os.environ.get("DEVSYNTH_LLM_TEMPERATURE", str(LLM_TEMPERATURE))
    )
    LLM_AUTO_SELECT_MODEL = os.environ.get(
        "DEVSYNTH_LLM_AUTO_SELECT_MODEL", "true"
    ).lower() in {"true", "1", "yes"}


# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


@dataclass
class ProjectUnifiedConfig(UnifiedConfig):
    """Configuration wrapper for project.yaml or pyproject.toml."""

    @classmethod
    def load(cls, path: Path | None = None) -> ProjectUnifiedConfig:
        """Load and validate a project configuration."""
        root = Path(path or os.getcwd())
        yaml_path = root / ".devsynth" / "project.yaml"
        use_pyproject = False
        data: dict[str, Any] = {}

        if yaml_path.exists():
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if not isinstance(data, dict):
                    raise DevSynthError(
                        "Configuration file must contain a mapping of keys to values."
                    )
        else:
            toml_path = root / "pyproject.toml"
            if toml_path.exists():
                tdata = toml.load(toml_path)
                data = tdata.get("tool", {}).get("devsynth", {})
                yaml_path = toml_path
                use_pyproject = True
                if not isinstance(data, dict):
                    raise DevSynthError(
                        "[tool.devsynth] must be a table in pyproject.toml."
                    )

        schema_file = (
            Path(__file__).resolve().parent.parent / "schemas" / "project_schema.json"
        )
        try:
            with open(schema_file, encoding="utf-8") as sf:
                schema = json.load(sf)

            required_keys = set(schema.get("required", []))
            if required_keys.intersection(data.keys()):
                jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as err:
            logger.error("Project configuration validation failed: %s", err)
            raise DevSynthError(
                "Configuration issues detected. Run 'devsynth init' to generate defaults."
            ) from err
        except (
            OSError,
            json.JSONDecodeError,
            jsonschema.exceptions.SchemaError,
        ) as exc:  # pragma: no cover - defensive
            logger.warning("Could not validate project config: %s", exc)

        cfg = ConfigModel()
        cfg.project_root = str(root)
        annotations = ConfigModel.__annotations__
        subset: dict[str, Any] = {}
        for key, value in data.items():
            field_type = annotations.get(key)
            if field_type is None:
                continue
            if field_type in (str, "str") and not isinstance(value, str):
                continue
            subset[key] = value
        combined = {**cfg.as_dict(), **subset}
        cfg = ConfigModel(**combined)
        return cls(cfg, yaml_path, use_pyproject)

    def save(self) -> Path:
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
