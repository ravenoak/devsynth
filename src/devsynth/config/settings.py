"""
Configuration settings for the DevSynth system.
"""

import os
import re
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


def is_devsynth_managed_project(project_dir: str = None) -> bool:
    """
    Check if the project is managed by DevSynth.

    A project is considered managed by DevSynth if it has a .devsynth/project.yaml file.
    The presence of a .devsynth/ directory is the marker that a project is managed by DevSynth.

    Args:
        project_dir: Path to the project directory. If None, uses the current working directory.

    Returns:
        bool: True if the project is managed by DevSynth, False otherwise.
    """
    if project_dir is None:
        project_dir = os.environ.get('DEVSYNTH_PROJECT_DIR') or os.getcwd()

    # Check for .devsynth/project.yaml
    project_config_path = os.path.join(project_dir, ".devsynth", "project.yaml")

    return os.path.exists(project_config_path)


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

    def __getitem__(self, key):
        """
        Enable dictionary-like access to settings.

        Args:
            key: The setting name to retrieve

        Returns:
            The setting value

        Raises:
            KeyError: If the setting does not exist
        """
        # Map test-expected keys to actual attribute names
        key_mapping = {
            'llm_provider': lambda s: os.environ.get("DEVSYNTH_LLM_PROVIDER", "lmstudio"),
            'llm_api_base': lambda s: os.environ.get("DEVSYNTH_LLM_API_BASE", "http://localhost:1234/v1"),
            'llm_model': lambda s: os.environ.get("DEVSYNTH_LLM_MODEL", "gpt-3.5-turbo"),
            'llm_temperature': lambda s: float(os.environ.get("DEVSYNTH_LLM_TEMPERATURE", "0.7")),
            'llm_auto_select_model': lambda s: os.environ.get("DEVSYNTH_LLM_AUTO_SELECT_MODEL", "true").lower() in ["true", "1", "yes"],
            'serper_api_key': lambda s: os.environ.get("SERPER_API_KEY", None),
            'memory_store_type': lambda s: os.environ.get("DEVSYNTH_MEMORY_STORE", "memory"),
            'openai_api_key': lambda s: os.environ.get("OPENAI_API_KEY", None),
        }

        # Check if we have a mapping for this key
        if key in key_mapping:
            mapped_key = key_mapping[key]
            # If the mapping is a function, call it
            if callable(mapped_key):
                return mapped_key(self)
            # Otherwise, get the attribute
            try:
                return getattr(self, mapped_key)
            except AttributeError:
                # If the mapped attribute doesn't exist, fall through to the original key
                pass

        # Try to get the attribute directly
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(f"Setting '{key}' not found")
    # Memory system settings
    memory_store_type: str = Field(default="memory", json_schema_extra={"env": "DEVSYNTH_MEMORY_STORE"})
    memory_file_path: str = Field(
        default=None,
        json_schema_extra={"env": "DEVSYNTH_MEMORY_PATH"}
    )
    max_context_size: int = Field(default=1000, json_schema_extra={"env": "DEVSYNTH_MAX_CONTEXT_SIZE"})
    context_expiration_days: int = Field(default=7, json_schema_extra={"env": "DEVSYNTH_CONTEXT_EXPIRATION_DAYS"})

    # Vector store settings
    vector_store_enabled: bool = Field(default=True, json_schema_extra={"env": "DEVSYNTH_VECTOR_STORE_ENABLED"})
    chromadb_collection_name: str = Field(default="devsynth_vectors", json_schema_extra={"env": "DEVSYNTH_CHROMADB_COLLECTION"})
    chromadb_distance_func: str = Field(default="cosine", json_schema_extra={"env": "DEVSYNTH_CHROMADB_DISTANCE_FUNC"})

    # Path settings
    log_dir: str = Field(default=None, json_schema_extra={"env": "DEVSYNTH_LOG_DIR"})
    project_dir: str = Field(default=None, json_schema_extra={"env": "DEVSYNTH_PROJECT_DIR"})

    # LLM provider settings
    provider_type: str = Field(default="openai", json_schema_extra={"env": "DEVSYNTH_PROVIDER_TYPE"})
    openai_api_key: Optional[str] = Field(default=None, json_schema_extra={"env": "OPENAI_API_KEY"})
    lm_studio_endpoint: Optional[str] = Field(default=None, json_schema_extra={"env": "LM_STUDIO_ENDPOINT"})

    @field_validator('memory_file_path', mode='before')
    def set_default_memory_path(cls, v, info):
        """
        Set default memory path if not specified.
        First check for project-level config, then fall back to global config.
        Defer path creation to maintain testability.
        """
        values = info.data
        if v is not None:
            return v

        # Check if we're in a test environment with file operations disabled
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in ("1", "true", "yes")

        # Get project directory from values or environment
        project_dir = values.get('project_dir') or os.environ.get('DEVSYNTH_PROJECT_DIR') or os.getcwd()

        # Check if this is a DevSynth-managed project
        if is_devsynth_managed_project(project_dir):
            # Check for project-level config
            project_config_path = os.path.join(project_dir, ".devsynth", "project.yaml")
            config_path = project_config_path if os.path.exists(project_config_path) else None

            if config_path:
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        if config and 'resources' in config and 'project' in config['resources'] and 'memoryDir' in config['resources']['project']:
                            return os.path.join(project_dir, config['resources']['project']['memoryDir'])
                except Exception as e:
                    # Log error but continue with default path
                    logger.error(f"Error reading project config: {e}")
                    pass

            # Fall back to default project path for DevSynth-managed projects
            return os.path.join(project_dir, ".devsynth", "memory")

        # For non-DevSynth-managed projects, use global config
        # Use project_dir for global config if DEVSYNTH_PROJECT_DIR is set (for test isolation)
        if os.environ.get('DEVSYNTH_PROJECT_DIR'):
            global_config_dir = os.path.join(os.environ.get('DEVSYNTH_PROJECT_DIR'), ".devsynth", "config")
            logger.debug(f"Using test environment global config dir: {global_config_dir}")
        else:
            # In test environments with file operations disabled, avoid using home directory
            if no_file_logging:
                # Return a path in the temporary directory that won't be created
                return os.path.join(project_dir, ".devsynth", "memory")

            global_config_dir = os.path.expanduser("~/.devsynth/config")
            logger.debug(f"Using user home global config dir: {global_config_dir}")

        global_config_path = os.path.join(global_config_dir, "global_config.yaml")
        if os.path.exists(global_config_path):
            try:
                import yaml
                with open(global_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'resources' in config and 'global' in config['resources'] and 'memoryDir' in config['resources']['global']:
                        memory_path = os.path.expanduser(config['resources']['global']['memoryDir'])
                        logger.debug(f"Using memory path from global config: {memory_path}")
                        return memory_path
            except Exception as e:
                # Log error but continue with default path
                pass

        # Fall back to global memory path for non-DevSynth-managed projects
        # In test environments with file operations disabled, avoid using home directory
        if no_file_logging:
            # Return a path in the temporary directory that won't be created
            return os.path.join(project_dir, ".devsynth", "memory")

        return os.path.expanduser("~/.devsynth/memory")

    @field_validator('log_dir', mode='before')
    def set_default_log_dir(cls, v, info):
        """
        Set default log directory if not specified.
        First check for project-level config, then fall back to global config.
        Defer directory creation to maintain testability.
        """
        values = info.data
        if v is not None:
            return v

        # Check if we're in a test environment with file operations disabled
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in ("1", "true", "yes")

        # Get project directory from values or environment
        project_dir = values.get('project_dir') or os.environ.get('DEVSYNTH_PROJECT_DIR') or os.getcwd()

        # Check if this is a DevSynth-managed project
        if is_devsynth_managed_project(project_dir):
            # Check for project-level config
            project_config_path = os.path.join(project_dir, ".devsynth", "project.yaml")
            config_path = project_config_path if os.path.exists(project_config_path) else None

            if config_path:
                try:
                    import yaml
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        if config and 'resources' in config and 'project' in config['resources'] and 'logsDir' in config['resources']['project']:
                            return os.path.join(project_dir, config['resources']['project']['logsDir'])
                except Exception as e:
                    # Log error but continue with default path
                    logger.error(f"Error reading project config: {e}")
                    pass

            # Fall back to default project path for DevSynth-managed projects
            return os.path.join(project_dir, ".devsynth", "logs")

        # For non-DevSynth-managed projects, use global config
        # Use project_dir for global config if DEVSYNTH_PROJECT_DIR is set (for test isolation)
        if os.environ.get('DEVSYNTH_PROJECT_DIR'):
            global_config_dir = os.path.join(os.environ.get('DEVSYNTH_PROJECT_DIR'), ".devsynth", "config")
            logger.debug(f"Using test environment global config dir for logs: {global_config_dir}")
        else:
            # In test environments with file operations disabled, avoid using home directory
            if no_file_logging:
                # Return a path in the temporary directory that won't be created
                return os.path.join(project_dir, ".devsynth", "logs")

            global_config_dir = os.path.expanduser("~/.devsynth/config")
            logger.debug(f"Using user home global config dir for logs: {global_config_dir}")

        global_config_path = os.path.join(global_config_dir, "global_config.yaml")
        if os.path.exists(global_config_path):
            try:
                import yaml
                with open(global_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'resources' in config and 'global' in config['resources'] and 'logsDir' in config['resources']['global']:
                        logs_path = os.path.expanduser(config['resources']['global']['logsDir'])
                        logger.debug(f"Using logs path from global config: {logs_path}")
                        return logs_path
            except Exception as e:
                # Log error but continue with default path
                pass

        # Fall back to global logs path for non-DevSynth-managed projects
        # In test environments with file operations disabled, avoid using home directory
        if no_file_logging:
            # Return a path in the temporary directory that won't be created
            return os.path.join(project_dir, ".devsynth", "logs")

        return os.path.expanduser("~/.devsynth/logs")

    @field_validator('project_dir', mode='before')
    def set_default_project_dir(cls, v, info):
        """
        Set default project directory if not specified.
        First check environment variables, then fall back to current working directory.
        """
        values = info.data
        if v is not None:
            return v

        # Check environment variable first
        env_project_dir = os.environ.get('DEVSYNTH_PROJECT_DIR')
        if env_project_dir:
            return env_project_dir

        # Default to current working directory
        return os.getcwd()

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

# Global settings instance for singleton pattern
_settings_instance = None

# Initialize settings for module-level access
_settings = Settings()

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

    # Try to load environment variables from .env file
    load_dotenv()

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

    This function respects test isolation by checking for the DEVSYNTH_NO_FILE_LOGGING
    and DEVSYNTH_PROJECT_DIR environment variables. In test environments, it will
    avoid creating directories in the real filesystem.

    Args:
        path: The path to check/create
        create: If True, create the directory if it doesn't exist

    Returns:
        str: The verified path
    """
    # Check if we're in a test environment
    in_test_env = os.environ.get("DEVSYNTH_PROJECT_DIR") is not None
    no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in ("1", "true", "yes")

    # Debug logging
    print(f"ensure_path_exists called with path={path}, create={create}")
    print(f"in_test_env={in_test_env}, DEVSYNTH_PROJECT_DIR={os.environ.get('DEVSYNTH_PROJECT_DIR')}")

    # If we're in a test environment with DEVSYNTH_PROJECT_DIR set, ensure paths are within the test directory
    if in_test_env:
        test_project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
        path_obj = Path(path)

        print(f"test_project_dir={test_project_dir}, path_obj={path_obj}")
        print(f"path_obj.is_absolute()={path_obj.is_absolute()}")
        print(f"str(path_obj).startswith(test_project_dir)={str(path_obj).startswith(test_project_dir)}")

        # If the path is absolute and not within the test project directory,
        # redirect it to be within the test project directory
        if path_obj.is_absolute() and not str(path_obj).startswith(test_project_dir):
            # For paths starting with home directory
            if str(path_obj).startswith(str(Path.home())):
                relative_path = str(path_obj).replace(str(Path.home()), "")
                new_path = os.path.join(test_project_dir, relative_path.lstrip("/\\"))
                print(f"Redirecting home path {path} to test path {new_path}")
                logger.debug(f"Redirecting home path {path} to test path {new_path}")
                path = new_path
            # For other absolute paths
            else:
                # Extract the path components after the root
                relative_path = str(path_obj.relative_to(path_obj.anchor))
                new_path = os.path.join(test_project_dir, relative_path)
                print(f"Redirecting absolute path {path} to test path {new_path}")
                logger.debug(f"Redirecting absolute path {path} to test path {new_path}")
                path = new_path

    # Only create directories if explicitly requested and not in a test environment with file operations disabled
    if create and not no_file_logging:
        try:
            os.makedirs(path, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Log the error but don't fail
            logger.warning(f"Failed to create directory {path}: {e}")

    return path


def get_llm_settings(reload: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Get LLM-specific settings.

    This function extracts LLM-specific settings from the general settings.

    Args:
        reload: If True, force reload settings even if already initialized
        **kwargs: Optional overrides for specific settings

    Returns:
        Dict[str, Any]: Dictionary containing LLM settings
    """
    settings = get_settings(reload, **kwargs)

    # Extract LLM-specific settings
    llm_settings = {
        "provider": settings["llm_provider"],
        "api_base": settings["llm_api_base"],
        "model": settings["llm_model"],
        "max_tokens": int(os.environ.get("DEVSYNTH_LLM_MAX_TOKENS", "2000")),
        "temperature": settings["llm_temperature"],
        "auto_select_model": settings["llm_auto_select_model"]
    }

    # Add API key if available
    if settings["llm_provider"] == "openai" and settings.openai_api_key:
        llm_settings["api_key"] = settings.openai_api_key

    return llm_settings
