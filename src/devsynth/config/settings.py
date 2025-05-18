
"""
Configuration settings for the DevSynth system.
"""

import os
import re
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


def load_dotenv(dotenv_path: Optional[str] = None) -> None:
    """
    Load environment variables from a .env file.

    Args:
        dotenv_path: Path to the .env file. If not provided, looks for a .env file in the current directory.
    """
    # Default to .env in the current directory if not specified
    if dotenv_path is None:
        dotenv_path = os.path.join(os.getcwd(), ".env")

    # Check if the file exists
    if not os.path.exists(dotenv_path):
        logger.debug(f"No .env file found at {dotenv_path}")
        return

    logger.debug(f"Loading environment variables from {dotenv_path}")

    # Read the .env file
    with open(dotenv_path, "r") as f:
        for line in f:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse the line (key=value)
            match = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line)
            if match:
                key, value = match.groups()
                # Set the environment variable if it's not already set
                if key not in os.environ:
                    os.environ[key] = value
                    logger.debug(f"Set environment variable: {key}")


class Settings(BaseSettings):
    """
    Configuration settings for the DevSynth system.
    """
    # Memory system settings
    memory_store_type: str = Field(default="memory", env="DEVSYNTH_MEMORY_STORE")
    memory_file_path: str = Field(
        default=os.path.join(os.getcwd(), ".devsynth", "memory"), 
        env="DEVSYNTH_MEMORY_PATH"
    )
    max_context_size: int = Field(default=1000, env="DEVSYNTH_MAX_CONTEXT_SIZE")
    context_expiration_days: int = Field(default=7, env="DEVSYNTH_CONTEXT_EXPIRATION_DAYS")
    
    # Vector store settings
    vector_store_enabled: bool = Field(default=True, env="DEVSYNTH_VECTOR_STORE_ENABLED")
    chromadb_collection_name: str = Field(default="devsynth_vectors", env="DEVSYNTH_CHROMADB_COLLECTION")
    chromadb_distance_func: str = Field(default="cosine", env="DEVSYNTH_CHROMADB_DISTANCE_FUNC")

    # LLM settings
    llm_provider: str = Field(default="lmstudio", env="DEVSYNTH_LLM_PROVIDER")
    llm_api_base: str = Field(default="http://localhost:1234/v1", env="DEVSYNTH_LLM_API_BASE")
    llm_model: str = Field(default="", env="DEVSYNTH_LLM_MODEL")
    llm_max_tokens: int = Field(default=1024, env="DEVSYNTH_LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.7, env="DEVSYNTH_LLM_TEMPERATURE")
    llm_auto_select_model: bool = Field(default=True, env="DEVSYNTH_LLM_AUTO_SELECT_MODEL")

    # OpenAI specific settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="DEVSYNTH_OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", env="DEVSYNTH_OPENAI_EMBEDDING_MODEL")
    
    # Other API keys
    serper_api_key: Optional[str] = Field(default=None, env="SERPER_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Load environment variables from .env file at module import time
load_dotenv()

# Create a function to get a fresh settings instance
def _get_settings_instance() -> Settings:
    """Get a fresh settings instance that reflects the current environment variables."""
    return Settings()

# Initialize settings
_settings = _get_settings_instance()

def get_settings() -> Dict[str, Any]:
    """Get all settings as a dictionary."""
    return {
        # Memory settings
        "memory_store_type": _settings.memory_store_type,
        "memory_file_path": _settings.memory_file_path,
        "max_context_size": _settings.max_context_size,
        "context_expiration_days": _settings.context_expiration_days,
        
        # Vector store settings
        "vector_store_enabled": _settings.vector_store_enabled,
        "chromadb_collection_name": _settings.chromadb_collection_name,
        "chromadb_distance_func": _settings.chromadb_distance_func,

        # LLM settings
        "llm_provider": _settings.llm_provider,
        "llm_api_base": _settings.llm_api_base,
        "llm_model": _settings.llm_model,
        "llm_max_tokens": _settings.llm_max_tokens,
        "llm_temperature": _settings.llm_temperature,
        "llm_auto_select_model": _settings.llm_auto_select_model,

        # OpenAI specific settings
        "openai_api_key": _settings.openai_api_key,
        "openai_model": _settings.openai_model,
        "openai_embedding_model": _settings.openai_embedding_model,

        # API keys
        "serper_api_key": _settings.serper_api_key,
    }

def get_llm_settings() -> Dict[str, Any]:
    """Get LLM-specific settings as a dictionary."""
    return {
        "provider": _settings.llm_provider,
        "api_base": _settings.llm_api_base,
        "model": _settings.llm_model,
        "max_tokens": _settings.llm_max_tokens,
        "temperature": _settings.llm_temperature,
        "auto_select_model": _settings.llm_auto_select_model,
        "openai_api_key": _settings.openai_api_key,
        "openai_model": _settings.openai_model,
        "openai_embedding_model": _settings.openai_embedding_model,
    }
