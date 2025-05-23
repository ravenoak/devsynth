"""
Configuration settings for the DevSynth system.
"""

import os
import re
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator

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
        default=None,
        env="DEVSYNTH_MEMORY_PATH"
    )
    max_context_size: int = Field(default=1000, env="DEVSYNTH_MAX_CONTEXT_SIZE")
    context_expiration_days: int = Field(default=7, env="DEVSYNTH_CONTEXT_EXPIRATION_DAYS")

    # Vector store settings
    vector_store_enabled: bool = Field(default=True, env="DEVSYNTH_VECTOR_STORE_ENABLED")
    chromadb_collection_name: str = Field(default="devsynth_vectors", env="DEVSYNTH_CHROMADB_COLLECTION")
    chromadb_distance_func: str = Field(default="cosine", env="DEVSYNTH_CHROMADB_DISTANCE_FUNC")

    # Path settings
    log_dir: str = Field(default=None, env="DEVSYNTH_LOG_DIR")
    project_dir: str = Field(default=None, env="DEVSYNTH_PROJECT_DIR")

    # LLM provider settings
    provider_type: str = Field(default="openai", env="DEVSYNTH_PROVIDER_TYPE")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    lm_studio_endpoint: Optional[str] = Field(default=None, env="LM_STUDIO_ENDPOINT")

    @validator('memory_file_path', pre=True)
    def set_default_memory_path(cls, v, values):
        """
        Set default memory path if not specified.
        First check for project-level config, then fall back to global config.
        Defer path creation to maintain testability.
        """
        if v is not None:
            return v

        # Check for project-level config
        project_config_path = os.path.join(os.getcwd(), "manifest.yaml")
        if os.path.exists(project_config_path):
            try:
                import yaml
                with open(project_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'resources' in config and 'project' in config['resources'] and 'memoryDir' in config['resources']['project']:
                        return os.path.join(os.getcwd(), config['resources']['project']['memoryDir'])
            except Exception as e:
                # Log error but continue with default path
                logger.error(f"Error reading manifest.yaml: {e}")
                pass

        # Check for global config
        global_config_dir = os.path.expanduser("~/.devsynth/config")
        global_config_path = os.path.join(global_config_dir, "global_config.yaml")
        if os.path.exists(global_config_path):
            try:
                import yaml
                with open(global_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'resources' in config and 'global' in config['resources'] and 'memoryDir' in config['resources']['global']:
                        return os.path.expanduser(config['resources']['global']['memoryDir'])
            except Exception as e:
                # Log error but continue with default path
                pass

        # Fall back to default path
        return os.path.join(os.getcwd(), ".devsynth", "memory")

    @validator('log_dir', pre=True)
    def set_default_log_dir(cls, v, values):
        """
        Set default log directory if not specified.
        First check for project-level config, then fall back to global config.
        Defer directory creation to maintain testability.
        """
        if v is not None:
            return v

        # Check for project-level config
        project_config_path = os.path.join(os.getcwd(), "manifest.yaml")
        if os.path.exists(project_config_path):
            try:
                import yaml
                with open(project_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'resources' in config and 'project' in config['resources'] and 'logsDir' in config['resources']['project']:
                        return os.path.join(os.getcwd(), config['resources']['project']['logsDir'])
            except Exception as e:
                # Log error but continue with default path
                logger.error(f"Error reading manifest.yaml: {e}")
                pass

        # Check for global config
        global_config_dir = os.path.expanduser("~/.devsynth/config")
        global_config_path = os.path.join(global_config_dir, "global_config.yaml")
        if os.path.exists(global_config_path):
            try:
                import yaml
                with open(global_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'resources' in config and 'global' in config['resources'] and 'logsDir' in config['resources']['global']:
                        return os.path.expanduser(config['resources']['global']['logsDir'])
            except Exception as e:
                # Log error but continue with default path
                pass

        # Fall back to default path
        return "logs"

    @validator('project_dir', pre=True)
    def set_default_project_dir(cls, v, values):
        """
        Set default project directory if not specified.
        First check for project-level config, then fall back to global config.
        """
        if v is not None:
            return v

        # Default to current working directory
        return os.getcwd()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Global settings instance for singleton pattern
_settings_instance = None

def get_settings(reload: bool = False, **kwargs) -> Settings:
    """
    Get settings instance with lazy initialization.

    This function implements a singleton pattern for settings, allowing for
    overrides via keyword arguments for testing purposes.

    Args:
        reload: If True, force reload settings even if already initialized
        **kwargs: Optional overrides for specific settings

    Returns:
        Settings: The settings instance
    """
    global _settings_instance

    if _settings_instance is None or reload:
        # Load settings from environment or .env
        _settings_instance = Settings(**kwargs)

    elif kwargs:
        # If we have kwargs but don't want to reload entirely,
        # update the existing instance with the provided values
        for key, value in kwargs.items():
            setattr(_settings_instance, key, value)

    return _settings_instance

def ensure_path_exists(path: str, create: bool = True) -> str:
    """
    Ensure the specified path exists.

    Args:
        path: The path to check/create
        create: If True, create the directory if it doesn't exist

    Returns:
        str: The verified path
    """
    if create:
        os.makedirs(path, exist_ok=True)
    return path
