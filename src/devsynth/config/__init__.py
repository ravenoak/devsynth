"""
Configuration module for DevSynth.
"""

from .settings import (
    get_settings, get_llm_settings, load_dotenv, _settings
)

# Expose settings as module-level variables for backward compatibility
MEMORY_STORE_TYPE = _settings.memory_store_type
MEMORY_FILE_PATH = _settings.memory_file_path
MAX_CONTEXT_SIZE = _settings.max_context_size
CONTEXT_EXPIRATION_DAYS = _settings.context_expiration_days

# Vector store settings
VECTOR_STORE_ENABLED = _settings.vector_store_enabled
CHROMADB_COLLECTION_NAME = _settings.chromadb_collection_name
CHROMADB_DISTANCE_FUNC = _settings.chromadb_distance_func

# LLM settings
LLM_PROVIDER = _settings.llm_provider
LLM_API_BASE = _settings.llm_api_base
LLM_MODEL = _settings.llm_model
LLM_MAX_TOKENS = _settings.llm_max_tokens
LLM_TEMPERATURE = _settings.llm_temperature
LLM_AUTO_SELECT_MODEL = _settings.llm_auto_select_model

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

__all__ = [
    # Functions
    "get_settings",
    "get_llm_settings",
    "load_dotenv",

    # Memory settings
    "MEMORY_STORE_TYPE",
    "MEMORY_FILE_PATH",
    "MAX_CONTEXT_SIZE",
    "CONTEXT_EXPIRATION_DAYS",
    
    # Vector store settings
    "VECTOR_STORE_ENABLED",
    "CHROMADB_COLLECTION_NAME",
    "CHROMADB_DISTANCE_FUNC",

    # LLM settings
    "LLM_PROVIDER",
    "LLM_API_BASE",
    "LLM_MODEL",
    "LLM_MAX_TOKENS",
    "LLM_TEMPERATURE",
    "LLM_AUTO_SELECT_MODEL",
]
