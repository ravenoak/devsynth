"""
Configuration settings for the DevSynth system.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import toml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import ConfigurationError, DevSynthError

from .loader import load_config


def _parse_bool_env(value: Any, field: str) -> bool:
    """Parse a boolean environment variable securely."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    str_val = str(value).strip().lower()
    if str_val in {"1", "true", "yes"}:
        return True
    if str_val in {"0", "false", "no"}:
        return False
    raise ConfigurationError(
        f"Invalid boolean value for {field}", config_key=field, config_value=value
    )


import toml

from .loader import load_config


def is_devsynth_managed_project(project_dir: str = None) -> bool:
    """
    Check if the project is managed by DevSynth.

    A project is considered managed by DevSynth if it has a .devsynth/devsynth.yml
    file or a pyproject.toml with a [tool.devsynth] section. The presence of a
    .devsynth/ directory is still treated as the primary marker.

    Args:
        project_dir: Path to the project directory. If None, uses the current working directory.

    Returns:
        bool: True if the project is managed by DevSynth, False otherwise.
    """
    if project_dir is None:
        project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR") or os.getcwd()
    yaml_path = os.path.join(project_dir, ".devsynth", "devsynth.yml")
    if os.path.exists(yaml_path):
        return True

    toml_path = os.path.join(project_dir, "pyproject.toml")
    if os.path.exists(toml_path):
        try:
            data = toml.load(toml_path)
            return "devsynth" in data.get("tool", {})
        except Exception:
            return False

    return False


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
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            match = re.match(r"^([A-Za-z0-9_]+)=(.*)$", line)
            if match:
                key, value = match.groups()
                if key not in os.environ:
                    os.environ[key] = value
                    logger.debug(f"Set environment variable: {key}")
            else:
                logger.warning(f"Ignoring invalid line in .env: {line}")


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
            "llm_provider": lambda s: os.environ.get(
                "DEVSYNTH_LLM_PROVIDER", "lmstudio"
            ),
            "llm_api_base": lambda s: os.environ.get(
                "DEVSYNTH_LLM_API_BASE", "http://localhost:1234/v1"
            ),
            "llm_model": lambda s: os.environ.get(
                "DEVSYNTH_LLM_MODEL", "gpt-3.5-turbo"
            ),
            "llm_temperature": lambda s: float(
                os.environ.get("DEVSYNTH_LLM_TEMPERATURE", "0.7")
            ),
            "llm_auto_select_model": lambda s: os.environ.get(
                "DEVSYNTH_LLM_AUTO_SELECT_MODEL", "true"
            ).lower()
            in ["true", "1", "yes"],
            "serper_api_key": lambda s: os.environ.get("SERPER_API_KEY", None),
            "memory_store_type": lambda s: os.environ.get(
                "DEVSYNTH_MEMORY_STORE", "memory"
            ),
            "kuzu_db_path": lambda s: os.environ.get("DEVSYNTH_KUZU_DB_PATH", None),
            "kuzu_embedded": lambda s: os.environ.get(
                "DEVSYNTH_KUZU_EMBEDDED", "true"
            ).lower()
            in ["true", "1", "yes"],
            "openai_api_key": lambda s: os.environ.get("OPENAI_API_KEY", None),
            "access_token": lambda s: os.environ.get("DEVSYNTH_ACCESS_TOKEN", None),
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
    memory_store_type: str = Field(
        default="memory", json_schema_extra={"env": "DEVSYNTH_MEMORY_STORE"}
    )
    memory_file_path: str = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_MEMORY_PATH"}
    )
    kuzu_db_path: Optional[str] = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_KUZU_DB_PATH"}
    )
    kuzu_embedded: bool = Field(
        default=True, json_schema_extra={"env": "DEVSYNTH_KUZU_EMBEDDED"}
    )
    max_context_size: int = Field(
        default=1000, json_schema_extra={"env": "DEVSYNTH_MAX_CONTEXT_SIZE"}
    )
    context_expiration_days: int = Field(
        default=7, json_schema_extra={"env": "DEVSYNTH_CONTEXT_EXPIRATION_DAYS"}
    )

    # Vector store settings
    vector_store_enabled: bool = Field(
        default=True, json_schema_extra={"env": "DEVSYNTH_VECTOR_STORE_ENABLED"}
    )
    chromadb_collection_name: str = Field(
        default="devsynth_vectors",
        json_schema_extra={"env": "DEVSYNTH_CHROMADB_COLLECTION"},
    )
    chromadb_distance_func: str = Field(
        default="cosine", json_schema_extra={"env": "DEVSYNTH_CHROMADB_DISTANCE_FUNC"}
    )

    enable_chromadb: bool = Field(
        default=False,
        validation_alias="ENABLE_CHROMADB",
        json_schema_extra={"env": "ENABLE_CHROMADB"},
    )

    # Path settings
    log_dir: str = Field(default=None, json_schema_extra={"env": "DEVSYNTH_LOG_DIR"})
    project_dir: str = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_PROJECT_DIR"}
    )

    # LLM provider settings
    provider_type: str = Field(
        default="openai", json_schema_extra={"env": "DEVSYNTH_PROVIDER_TYPE"}
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        json_schema_extra={"env": "OPENAI_API_KEY"},
    )
    lm_studio_endpoint: Optional[str] = Field(
        default=None, json_schema_extra={"env": "LM_STUDIO_ENDPOINT"}
    )

    # LLM provider retry settings
    provider_max_retries: int = Field(
        default=3, json_schema_extra={"env": "DEVSYNTH_PROVIDER_MAX_RETRIES"}
    )
    provider_initial_delay: float = Field(
        default=1.0, json_schema_extra={"env": "DEVSYNTH_PROVIDER_INITIAL_DELAY"}
    )
    provider_exponential_base: float = Field(
        default=2.0, json_schema_extra={"env": "DEVSYNTH_PROVIDER_EXPONENTIAL_BASE"}
    )
    provider_max_delay: float = Field(
        default=60.0, json_schema_extra={"env": "DEVSYNTH_PROVIDER_MAX_DELAY"}
    )
    provider_jitter: bool = Field(
        default=True, json_schema_extra={"env": "DEVSYNTH_PROVIDER_JITTER"}
    )

    # LLM provider fallback settings
    provider_fallback_enabled: bool = Field(
        default=True, json_schema_extra={"env": "DEVSYNTH_PROVIDER_FALLBACK_ENABLED"}
    )
    provider_fallback_order: str = Field(
        default="openai,lm_studio", json_schema_extra={"env": "DEVSYNTH_PROVIDER_FALLBACK_ORDER"}
    )

    # LLM provider circuit breaker settings
    provider_circuit_breaker_enabled: bool = Field(
        default=True, json_schema_extra={"env": "DEVSYNTH_PROVIDER_CIRCUIT_BREAKER_ENABLED"}
    )
    provider_failure_threshold: int = Field(
        default=5, json_schema_extra={"env": "DEVSYNTH_PROVIDER_FAILURE_THRESHOLD"}
    )
    provider_recovery_timeout: float = Field(
        default=60.0, json_schema_extra={"env": "DEVSYNTH_PROVIDER_RECOVERY_TIMEOUT"}
    )

    @field_validator("openai_api_key", mode="before")
    def validate_api_key(cls, v):
        if v is not None and not v.strip():
            raise ConfigurationError(
                "OPENAI_API_KEY cannot be empty",
                config_key="OPENAI_API_KEY",
                config_value=v,
            )
        return v

    # Security feature toggles
    authentication_enabled: bool = Field(
        default=True,
        validation_alias="DEVSYNTH_AUTHENTICATION_ENABLED",
        json_schema_extra={"env": "DEVSYNTH_AUTHENTICATION_ENABLED"},
    )
    authorization_enabled: bool = Field(
        default=True,
        validation_alias="DEVSYNTH_AUTHORIZATION_ENABLED",
        json_schema_extra={"env": "DEVSYNTH_AUTHORIZATION_ENABLED"},
    )
    sanitization_enabled: bool = Field(
        default=True,
        validation_alias="DEVSYNTH_SANITIZATION_ENABLED",
        json_schema_extra={"env": "DEVSYNTH_SANITIZATION_ENABLED"},
    )
    input_validation_enabled: bool = Field(
        default=True,
        validation_alias="DEVSYNTH_INPUT_VALIDATION_ENABLED",
        json_schema_extra={"env": "DEVSYNTH_INPUT_VALIDATION_ENABLED"},
    )
    encryption_at_rest: bool = Field(
        default=False,
        validation_alias="DEVSYNTH_ENCRYPTION_AT_REST",
        json_schema_extra={"env": "DEVSYNTH_ENCRYPTION_AT_REST"},
    )
    encryption_key: Optional[str] = Field(
        default=None,
        validation_alias="DEVSYNTH_ENCRYPTION_KEY",
        json_schema_extra={"env": "DEVSYNTH_ENCRYPTION_KEY"},
    )
    access_token: Optional[str] = Field(
        default=None,
        validation_alias="DEVSYNTH_ACCESS_TOKEN",
        json_schema_extra={"env": "DEVSYNTH_ACCESS_TOKEN"},
    )
    tls_verify: bool = Field(
        default=True,
        validation_alias="DEVSYNTH_TLS_VERIFY",
        json_schema_extra={"env": "DEVSYNTH_TLS_VERIFY"},
    )
    tls_cert_file: Optional[str] = Field(
        default=None,
        validation_alias="DEVSYNTH_TLS_CERT_FILE",
        json_schema_extra={"env": "DEVSYNTH_TLS_CERT_FILE"},
    )
    tls_key_file: Optional[str] = Field(
        default=None,
        validation_alias="DEVSYNTH_TLS_KEY_FILE",
        json_schema_extra={"env": "DEVSYNTH_TLS_KEY_FILE"},
    )
    tls_ca_file: Optional[str] = Field(
        default=None,
        validation_alias="DEVSYNTH_TLS_CA_FILE",
        json_schema_extra={"env": "DEVSYNTH_TLS_CA_FILE"},
    )

    @field_validator(
        "authentication_enabled",
        "authorization_enabled",
        "sanitization_enabled",
        "input_validation_enabled",
        "encryption_at_rest",
        "tls_verify",
        mode="before",
    )
    def validate_security_bool(cls, v, info):
        return _parse_bool_env(v, info.field_name)

    @field_validator("kuzu_embedded", "provider_jitter", "provider_fallback_enabled", "provider_circuit_breaker_enabled", mode="before")
    def validate_bool_settings(cls, v, info):
        return _parse_bool_env(v, info.field_name)

    @field_validator("provider_max_retries", "provider_failure_threshold", mode="after")
    def validate_positive_int(cls, v, info):
        if v is not None and v < 0:
            logger.warning(f"{info.field_name} must be a non-negative integer, got {v}. Using default value.")
            return getattr(cls, info.field_name).default
        return v

    @field_validator("provider_initial_delay", "provider_max_delay", "provider_recovery_timeout", mode="after")
    def validate_positive_float(cls, v, info):
        if v is not None and v <= 0:
            logger.warning(f"{info.field_name} must be a positive number, got {v}. Using default value.")
            return getattr(cls, info.field_name).default
        return v

    @field_validator("provider_exponential_base", mode="after")
    def validate_exponential_base(cls, v, info):
        if v is not None and v <= 1.0:
            logger.warning(f"{info.field_name} must be greater than 1.0, got {v}. Using default value.")
            return getattr(cls, info.field_name).default
        return v

    @field_validator("provider_fallback_order", mode="after")
    def validate_fallback_order(cls, v, info):
        if v is not None:
            providers = v.split(",")
            valid_providers = ["openai", "lm_studio"]
            for provider in providers:
                if provider.strip().lower() not in valid_providers:
                    logger.warning(f"Invalid provider in fallback order: {provider}. Valid providers are: {valid_providers}")
            if not providers:
                logger.warning(f"{info.field_name} must not be empty. Using default value.")
                return getattr(cls, info.field_name).default
        return v

    @field_validator("memory_file_path", mode="before")
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
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        # Get project directory from values or environment
        project_dir = (
            values.get("project_dir")
            or os.environ.get("DEVSYNTH_PROJECT_DIR")
            or os.getcwd()
        )

        # Check if this is a DevSynth-managed project
        if is_devsynth_managed_project(project_dir):
            try:
                cfg = load_config(project_dir)
                mem_dir = (
                    cfg.resources.get("project", {}).get("memoryDir")
                    if cfg.resources
                    else None
                )
                if mem_dir:
                    return os.path.join(project_dir, mem_dir)
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Error reading project config: {e}")

            # Fall back to default project path for DevSynth-managed projects
            return os.path.join(project_dir, ".devsynth", "memory")

        # For non-DevSynth-managed projects, use global config
        # Use project_dir for global config if DEVSYNTH_PROJECT_DIR is set (for test isolation)
        if os.environ.get("DEVSYNTH_PROJECT_DIR"):
            global_config_dir = os.path.join(
                os.environ.get("DEVSYNTH_PROJECT_DIR"), ".devsynth", "config"
            )
            logger.debug(
                f"Using test environment global config dir: {global_config_dir}"
            )
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

                with open(global_config_path, "r") as f:
                    config = yaml.safe_load(f)
                    if (
                        config
                        and "resources" in config
                        and "global" in config["resources"]
                        and "memoryDir" in config["resources"]["global"]
                    ):
                        memory_path = os.path.expanduser(
                            config["resources"]["global"]["memoryDir"]
                        )
                        logger.debug(
                            f"Using memory path from global config: {memory_path}"
                        )
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

    @field_validator("log_dir", mode="before")
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
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        # Get project directory from values or environment
        project_dir = (
            values.get("project_dir")
            or os.environ.get("DEVSYNTH_PROJECT_DIR")
            or os.getcwd()
        )

        # Check if this is a DevSynth-managed project
        if is_devsynth_managed_project(project_dir):
            try:
                cfg = load_config(project_dir)
                logs_dir = (
                    cfg.resources.get("project", {}).get("logsDir")
                    if cfg.resources
                    else None
                )
                if logs_dir:
                    return os.path.join(project_dir, logs_dir)
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Error reading project config: {e}")

            # Fall back to default project path for DevSynth-managed projects
            return os.path.join(project_dir, ".devsynth", "logs")

        # For non-DevSynth-managed projects, use global config
        # Use project_dir for global config if DEVSYNTH_PROJECT_DIR is set (for test isolation)
        if os.environ.get("DEVSYNTH_PROJECT_DIR"):
            global_config_dir = os.path.join(
                os.environ.get("DEVSYNTH_PROJECT_DIR"), ".devsynth", "config"
            )
            logger.debug(
                f"Using test environment global config dir for logs: {global_config_dir}"
            )
        else:
            # In test environments with file operations disabled, avoid using home directory
            if no_file_logging:
                # Return a path in the temporary directory that won't be created
                return os.path.join(project_dir, ".devsynth", "logs")

            global_config_dir = os.path.expanduser("~/.devsynth/config")
            logger.debug(
                f"Using user home global config dir for logs: {global_config_dir}"
            )

        global_config_path = os.path.join(global_config_dir, "global_config.yaml")
        if os.path.exists(global_config_path):
            try:
                import yaml

                with open(global_config_path, "r") as f:
                    config = yaml.safe_load(f)
                    if (
                        config
                        and "resources" in config
                        and "global" in config["resources"]
                        and "logsDir" in config["resources"]["global"]
                    ):
                        logs_path = os.path.expanduser(
                            config["resources"]["global"]["logsDir"]
                        )
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

    @field_validator("project_dir", mode="before")
    def set_default_project_dir(cls, v, info):
        """
        Set default project directory if not specified.
        First check environment variables, then fall back to current working directory.
        """
        values = info.data
        if v is not None:
            return v

        # Check environment variable first
        env_project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
        if env_project_dir:
            return env_project_dir

        # Default to current working directory
        return os.getcwd()

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
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
    no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
        "1",
        "true",
        "yes",
    )

    # Debug logging
    logger.debug("ensure_path_exists called with path=%s, create=%s", path, create)
    logger.debug(
        "in_test_env=%s, DEVSYNTH_PROJECT_DIR=%s",
        in_test_env,
        os.environ.get("DEVSYNTH_PROJECT_DIR"),
    )

    # If we're in a test environment with DEVSYNTH_PROJECT_DIR set, ensure paths are within the test directory
    if in_test_env:
        test_project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
        path_obj = Path(path)

        logger.debug("test_project_dir=%s, path_obj=%s", test_project_dir, path_obj)
        logger.debug("path_obj.is_absolute()=%s", path_obj.is_absolute())
        logger.debug(
            "str(path_obj).startswith(test_project_dir)=%s",
            str(path_obj).startswith(test_project_dir),
        )

        if not path_obj.is_absolute():
            path = os.path.join(test_project_dir, str(path_obj))
            path_obj = Path(path)
        # If the path is absolute and not within the test project directory,
        # redirect it to be within the test project directory
        if path_obj.is_absolute() and not str(path_obj).startswith(test_project_dir):
            # For paths starting with home directory
            if str(path_obj).startswith(str(Path.home())):
                relative_path = str(path_obj).replace(str(Path.home()), "")
                new_path = os.path.join(test_project_dir, relative_path.lstrip("/\\"))
                logger.debug("Redirecting home path %s to test path %s", path, new_path)
                path = new_path
            # For other absolute paths
            else:
                # Extract the path components after the root
                relative_path = str(path_obj.relative_to(path_obj.anchor))
                new_path = os.path.join(test_project_dir, relative_path)
                logger.debug(
                    "Redirecting absolute path %s to test path %s", path, new_path
                )
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
        "auto_select_model": settings["llm_auto_select_model"],
    }

    # Add API key if available
    if settings["llm_provider"] == "openai" and settings.openai_api_key:
        llm_settings["api_key"] = settings.openai_api_key

    return llm_settings
