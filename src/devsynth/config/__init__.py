"""
Configuration module for DevSynth.
"""

import os
from pathlib import Path

from .loader import ConfigModel, config_key_autocomplete, load_config, save_config
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

__all__ = [
    # Functions
    "get_settings",
    "get_llm_settings",
    "load_dotenv",
    "load_config",
    "save_config",
    "get_project_config",
    "config_key_autocomplete",
    "ConfigModel",
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
