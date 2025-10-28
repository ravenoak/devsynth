from __future__ import annotations

"""Configuration settings for the DevSynth system."""

import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, TypeVar, Union, cast
from collections.abc import Callable

import toml  # type: ignore[import-untyped]  # TODO(2025-12-20): Adopt typed tomllib or bundle stubs.
import yaml
from pydantic import Field, ValidationInfo
from pydantic_settings import SettingsConfigDict

if TYPE_CHECKING:
    from pydantic import BaseModel as _BaseModel

    F = TypeVar("F", bound=Callable[..., Any])

    class BaseSettings(_BaseModel):
        model_config: SettingsConfigDict

    def field_validator(*args: Any, **kwargs: Any) -> Callable[[F], F]: ...

else:
    from pydantic import field_validator as _field_validator
    from pydantic_settings import BaseSettings as _BaseSettings

    BaseSettings = (
        _BaseSettings  # TODO(2025-12-20): Drop once upstream ships typed BaseSettings.
    )
    field_validator = _field_validator

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import ConfigurationError, DevSynthError

from .loader import load_config

# Default settings
# Ephemeral memory stores should prefer the embedded backend, so make that
# behaviour explicit via a shared constant.
DEFAULT_KUZU_EMBEDDED = True

# Module-level defaults for Kuzu integration
kuzu_db_path: str | None = None
# Whether to use the embedded KuzuDB backend by default. Tests and runtime
# environments may override this via the ``DEVSYNTH_KUZU_EMBEDDED``
# environment variable. ``KUZU_EMBEDDED`` mirrors ``kuzu_embedded`` and
# is maintained for backward compatibility.
kuzu_embedded: bool = DEFAULT_KUZU_EMBEDDED
KUZU_EMBEDDED: bool = DEFAULT_KUZU_EMBEDDED


def _uninitialised_get_settings(*_args: Any, **_kwargs: Any) -> Any:
    """Placeholder used while the module is still initialising."""

    raise RuntimeError(
        "devsynth.config.settings.get_settings called before initialisation "
        "completed. Reload the module once imports settle."
    )


_get_settings_impl: Callable[..., Any] = _uninitialised_get_settings


def _install_get_settings_impl(func: Callable[..., Any]) -> Callable[..., Any]:
    """Rebind the active ``get_settings`` implementation during module import."""

    global _get_settings_impl
    _get_settings_impl = func
    globals()["get_settings"] = get_settings
    return func


def get_settings(reload: bool = False, **kwargs: Any) -> Settings:
    """Return cached settings, delegating to the active implementation."""

    return _get_settings_impl(reload=reload, **kwargs)


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


def is_devsynth_managed_project(project_dir: str | None = None) -> bool:
    """
    Check if the project is managed by DevSynth.

    A project is considered managed by DevSynth if it has a .devsynth/project.yaml
    file (or the legacy .devsynth/devsynth.yml) or a pyproject.toml with a [tool.devsynth] section. The presence of a
    .devsynth/ directory is still treated as the primary marker.

    Args:
        project_dir: Path to the project directory. If None, uses the current working directory.

    Returns:
        bool: True if the project is managed by DevSynth, False otherwise.
    """
    if project_dir is None:
        project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR") or os.getcwd()
    yaml_path = os.path.join(project_dir, ".devsynth", "project.yaml")
    if os.path.exists(yaml_path):
        return True
    legacy_yaml = os.path.join(project_dir, ".devsynth", "devsynth.yml")
    if os.path.exists(legacy_yaml):
        return True

    toml_path = os.path.join(project_dir, "pyproject.toml")
    if os.path.exists(toml_path):
        try:
            data = toml.load(toml_path)
            return "devsynth" in data.get("tool", {})
        except (OSError, toml.TomlDecodeError):
            return False

    return False


def load_dotenv(dotenv_path: str | None = None) -> None:
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
    with open(dotenv_path) as f:
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


# TODO(2025-12-20): Extract typed config DTOs for resource and LLM overrides
# so BaseSettings no longer needs runtime casting in validators.


class Settings(BaseSettings):
    """
    Configuration settings for the DevSynth system.
    """

    def __getitem__(self, key: str) -> Any:
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
        key_mapping: dict[str, Callable[[Settings], Any]] = {
            "llm_provider": lambda s: os.environ.get(
                "DEVSYNTH_LLM_PROVIDER", "lmstudio"
            ),
            "llm_api_base": lambda s: os.environ.get(
                "DEVSYNTH_LLM_API_BASE", "http://localhost:1234"
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
            "s3_bucket_name": lambda s: os.environ.get(
                "DEVSYNTH_S3_BUCKET", s.s3_bucket_name
            ),
            # Expose configurable Kuzu settings with environment overrides
            "kuzu_db_path": lambda s: os.environ.get(
                "DEVSYNTH_KUZU_DB_PATH", s.kuzu_db_path
            ),
            "kuzu_embedded": lambda s: _parse_bool_env(
                os.environ.get("DEVSYNTH_KUZU_EMBEDDED", str(s.kuzu_embedded)),
                "kuzu_embedded",
            ),
            "openai_api_key": lambda s: os.environ.get("OPENAI_API_KEY", None),
            "access_token": lambda s: os.environ.get("DEVSYNTH_ACCESS_TOKEN", None),
        }

        # Check if we have a mapping for this key
        if key in key_mapping:
            mapped_key = key_mapping[key]
            return mapped_key(self)

        # Try to get the attribute directly
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(f"Setting '{key}' not found")

    # Memory system settings
    memory_store_type: str = Field(
        default="memory", json_schema_extra={"env": "DEVSYNTH_MEMORY_STORE"}
    )
    memory_file_path: str | None = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_MEMORY_PATH"}
    )
    s3_bucket_name: str | None = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_S3_BUCKET"}
    )
    kuzu_db_path: str | None = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_KUZU_DB_PATH"}
    )
    # Enable or disable the embedded KuzuDB backend. When ``False`` the system
    # falls back to a lightweight in-memory implementation. The value can be
    # overridden via the ``DEVSYNTH_KUZU_EMBEDDED`` environment variable.
    kuzu_embedded: bool = Field(
        default=DEFAULT_KUZU_EMBEDDED,
        description="Use embedded KuzuDB backend instead of in-memory fallback",
        validation_alias="DEVSYNTH_KUZU_EMBEDDED",
        json_schema_extra={"env": "DEVSYNTH_KUZU_EMBEDDED"},
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
    chromadb_host: str | None = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_CHROMADB_HOST"}
    )
    chromadb_port: int = Field(
        default=8000, json_schema_extra={"env": "DEVSYNTH_CHROMADB_PORT"}
    )

    enable_chromadb: bool = Field(
        default=False,
        validation_alias="ENABLE_CHROMADB",
        json_schema_extra={"env": "ENABLE_CHROMADB"},
    )

    # GUI settings
    gui_enabled: bool = Field(
        default=False, json_schema_extra={"env": "DEVSYNTH_GUI_ENABLED"}
    )

    # Path settings
    log_dir: str | None = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_LOG_DIR"}
    )
    project_dir: str | None = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_PROJECT_DIR"}
    )

    # LLM provider settings
    provider_type: str = Field(
        default="openai", json_schema_extra={"env": "DEVSYNTH_PROVIDER_TYPE"}
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        json_schema_extra={"env": "OPENAI_API_KEY"},
    )
    lm_studio_endpoint: str | None = Field(
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

    # Retry metrics and conditional settings
    provider_retry_metrics: bool = Field(
        default=True, json_schema_extra={"env": "DEVSYNTH_PROVIDER_RETRY_METRICS"}
    )
    provider_retry_conditions: str | None = Field(
        default=None, json_schema_extra={"env": "DEVSYNTH_PROVIDER_RETRY_CONDITIONS"}
    )

    @field_validator("provider_retry_conditions", mode="after")
    def _normalize_conditions(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return ",".join(part.strip() for part in str(v).split(",") if part.strip())

    # LLM provider fallback settings
    provider_fallback_enabled: bool = Field(
        default=True, json_schema_extra={"env": "DEVSYNTH_PROVIDER_FALLBACK_ENABLED"}
    )
    provider_fallback_order: str = Field(
        default="openai,lmstudio",
        json_schema_extra={"env": "DEVSYNTH_PROVIDER_FALLBACK_ORDER"},
    )

    # LLM provider circuit breaker settings
    provider_circuit_breaker_enabled: bool = Field(
        default=True,
        json_schema_extra={"env": "DEVSYNTH_PROVIDER_CIRCUIT_BREAKER_ENABLED"},
    )
    provider_failure_threshold: int = Field(
        default=5, json_schema_extra={"env": "DEVSYNTH_PROVIDER_FAILURE_THRESHOLD"}
    )
    provider_recovery_timeout: float = Field(
        default=60.0, json_schema_extra={"env": "DEVSYNTH_PROVIDER_RECOVERY_TIMEOUT"}
    )

    @field_validator("openai_api_key", mode="before")
    def validate_api_key(cls, v: str | None) -> str | None:
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
    encryption_key: str | None = Field(
        default=None,
        validation_alias="DEVSYNTH_ENCRYPTION_KEY",
        json_schema_extra={"env": "DEVSYNTH_ENCRYPTION_KEY"},
    )
    access_token: str | None = Field(
        default=None,
        validation_alias="DEVSYNTH_ACCESS_TOKEN",
        json_schema_extra={"env": "DEVSYNTH_ACCESS_TOKEN"},
    )
    tls_verify: bool = Field(
        default=True,
        validation_alias="DEVSYNTH_TLS_VERIFY",
        json_schema_extra={"env": "DEVSYNTH_TLS_VERIFY"},
    )
    tls_cert_file: str | None = Field(
        default=None,
        validation_alias="DEVSYNTH_TLS_CERT_FILE",
        json_schema_extra={"env": "DEVSYNTH_TLS_CERT_FILE"},
    )
    tls_key_file: str | None = Field(
        default=None,
        validation_alias="DEVSYNTH_TLS_KEY_FILE",
        json_schema_extra={"env": "DEVSYNTH_TLS_KEY_FILE"},
    )
    tls_ca_file: str | None = Field(
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
    def validate_security_bool(
        cls,
        v: object,
        info: ValidationInfo,
    ) -> bool:
        return _parse_bool_env(v, info.field_name)

    @field_validator(
        "kuzu_embedded",
        "provider_jitter",
        "provider_retry_metrics",
        "provider_fallback_enabled",
        "provider_circuit_breaker_enabled",
        mode="before",
    )
    def validate_bool_settings(
        cls,
        v: object,
        info: ValidationInfo,
    ) -> bool:
        return _parse_bool_env(v, info.field_name)

    @field_validator("provider_max_retries", "provider_failure_threshold", mode="after")
    def validate_positive_int(cls, v: int, info: ValidationInfo) -> int:
        if v < 0:
            logger.warning(
                f"{info.field_name} must be a non-negative integer, got {v}. Using default value."
            )
            default_value = cls.model_fields[info.field_name].default
            return cast(int, default_value)
        return v

    @field_validator(
        "provider_initial_delay",
        "provider_max_delay",
        "provider_recovery_timeout",
        mode="after",
    )
    def validate_positive_float(cls, v: float, info: ValidationInfo) -> float:
        if v <= 0:
            logger.warning(
                f"{info.field_name} must be a positive number, got {v}. Using default value."
            )
            default_value = cls.model_fields[info.field_name].default
            return cast(float, default_value)
        return v

    @field_validator("provider_exponential_base", mode="after")
    def validate_exponential_base(cls, v: float, info: ValidationInfo) -> float:
        if v <= 1.0:
            logger.warning(
                f"{info.field_name} must be greater than 1.0, got {v}. Using default value."
            )
            default_value = cls.model_fields[info.field_name].default
            return cast(float, default_value)
        return v

    @field_validator("provider_fallback_order", mode="after")
    def validate_fallback_order(cls, v: str, info: ValidationInfo) -> str:
        providers = [provider for provider in v.split(",") if provider.strip()]
        valid_providers = ["openai", "lmstudio"]
        for provider in providers:
            if provider.strip().lower() not in valid_providers:
                logger.warning(
                    f"Invalid provider in fallback order: {provider}. Valid providers are: {valid_providers}"
                )
        if not providers:
            logger.warning(f"{info.field_name} must not be empty. Using default value.")
            default_value = cls.model_fields[info.field_name].default
            return cast(str, default_value)
        return v

    @field_validator("memory_file_path", mode="before")
    def set_default_memory_path(
        cls,
        v: str | None,
        info: ValidationInfo,
    ) -> str | None:
        """
        Set default memory path if not specified.
        First check for project-level config, then fall back to global config.
        Defer path creation to maintain testability.
        """
        values = cast(dict[str, Any], info.data)
        if v is not None:
            return v

        # Check if we're in a test environment with file operations disabled
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        # Get project directory from values or environment
        project_dir = cast(
            str,
            values.get("project_dir")
            or os.environ.get("DEVSYNTH_PROJECT_DIR")
            or os.getcwd(),
        )

        # Check if this is a DevSynth-managed project
        if is_devsynth_managed_project(project_dir):
            try:
                cfg = load_config(project_dir)
                mem_dir = None
                if cfg.resources:
                    project_resources = cfg.resources.get("project", {})
                    mem_candidate = project_resources.get("memoryDir")
                    if isinstance(mem_candidate, str):
                        mem_dir = mem_candidate
                if mem_dir:
                    return os.path.join(project_dir, mem_dir)
            except ConfigurationError as e:  # pragma: no cover - defensive
                logger.error(f"Error reading project config: {e}")

            # Fall back to default project path for DevSynth-managed projects
            return os.path.join(project_dir, ".devsynth", "memory")

        # For non-DevSynth-managed projects, use global config
        # Use project_dir for global config if DEVSYNTH_PROJECT_DIR is set (for test isolation)
        project_dir_env = os.environ.get("DEVSYNTH_PROJECT_DIR")
        if project_dir_env:
            global_config_dir = os.path.join(project_dir_env, ".devsynth", "config")
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
                with open(global_config_path) as f:
                    config = yaml.safe_load(f)
                    if (
                        isinstance(config, dict)
                        and isinstance(config.get("resources"), dict)
                        and isinstance(config["resources"].get("global"), dict)
                    ):
                        raw_memory_dir = config["resources"]["global"].get("memoryDir")
                        if isinstance(raw_memory_dir, str):
                            memory_path = os.path.expanduser(raw_memory_dir)
                            logger.debug(
                                "Using memory path from global config: %s",
                                memory_path,
                            )
                            return memory_path
            except (OSError, yaml.YAMLError, ImportError) as e:
                # Log error but continue with default path
                logger.debug(f"Error reading global config: {e}")

        # Fall back to global memory path for non-DevSynth-managed projects
        # In test environments with file operations disabled, avoid using home directory
        if no_file_logging:
            # Return a path in the temporary directory that won't be created
            return os.path.join(project_dir, ".devsynth", "memory")

        return os.path.expanduser("~/.devsynth/memory")

    @field_validator("log_dir", mode="before")
    def set_default_log_dir(
        cls,
        v: str | None,
        info: ValidationInfo,
    ) -> str | None:
        """
        Set default log directory if not specified.
        First check for project-level config, then fall back to global config.
        Defer directory creation to maintain testability.
        """
        values = cast(dict[str, Any], info.data)
        if v is not None:
            return v

        # Check if we're in a test environment with file operations disabled
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        # Get project directory from values or environment
        project_dir = cast(
            str,
            values.get("project_dir")
            or os.environ.get("DEVSYNTH_PROJECT_DIR")
            or os.getcwd(),
        )

        # Check if this is a DevSynth-managed project
        if is_devsynth_managed_project(project_dir):
            try:
                cfg = load_config(project_dir)
                logs_dir = None
                if cfg.resources:
                    project_resources = cfg.resources.get("project", {})
                    logs_candidate = project_resources.get("logsDir")
                    if isinstance(logs_candidate, str):
                        logs_dir = logs_candidate
                if logs_dir:
                    return os.path.join(project_dir, logs_dir)
            except ConfigurationError as e:  # pragma: no cover - defensive
                logger.error(f"Error reading project config: {e}")

            # Fall back to default project path for DevSynth-managed projects
            return os.path.join(project_dir, ".devsynth", "logs")

        # For non-DevSynth-managed projects, use global config
        # Use project_dir for global config if DEVSYNTH_PROJECT_DIR is set (for test isolation)
        project_dir_env = os.environ.get("DEVSYNTH_PROJECT_DIR")
        if project_dir_env:
            global_config_dir = os.path.join(project_dir_env, ".devsynth", "config")
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
                with open(global_config_path) as f:
                    config = yaml.safe_load(f)
                    if (
                        isinstance(config, dict)
                        and isinstance(config.get("resources"), dict)
                        and isinstance(config["resources"].get("global"), dict)
                    ):
                        raw_logs_dir = config["resources"]["global"].get("logsDir")
                        if isinstance(raw_logs_dir, str):
                            logs_path = os.path.expanduser(raw_logs_dir)
                            logger.debug(
                                "Using logs path from global config: %s", logs_path
                            )
                            return logs_path
            except (OSError, yaml.YAMLError, ImportError) as e:
                # Log error but continue with default path
                logger.debug(f"Error reading global config: {e}")

        # Fall back to global logs path for non-DevSynth-managed projects
        # In test environments with file operations disabled, avoid using home directory
        if no_file_logging:
            # Return a path in the temporary directory that won't be created
            return os.path.join(project_dir, ".devsynth", "logs")

        return os.path.expanduser("~/.devsynth/logs")

    @field_validator("project_dir", mode="before")
    def set_default_project_dir(
        cls,
        v: str | None,
        info: ValidationInfo,
    ) -> str:
        """
        Set default project directory if not specified.
        First check environment variables, then fall back to current working directory.
        """
        values = cast(dict[str, Any], info.data)
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
_settings_instance: Settings | None = None


@_install_get_settings_impl
def _compute_settings(reload: bool = False, **kwargs: Any) -> Settings:
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
    global _settings_instance, kuzu_db_path, kuzu_embedded, KUZU_EMBEDDED

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

    # Expose mutable values at module level for tests that import them
    kuzu_db_path = _settings_instance.kuzu_db_path
    kuzu_embedded = _settings_instance.kuzu_embedded
    KUZU_EMBEDDED = kuzu_embedded

    return _settings_instance


get_settings.__doc__ = _compute_settings.__doc__


# Initialize settings for module-level access
_settings: Settings = get_settings()

# Expose commonly used settings at module level
kuzu_db_path = _settings.kuzu_db_path
kuzu_embedded = _settings.kuzu_embedded
# Backward-compatible constant for older imports
KUZU_EMBEDDED = kuzu_embedded


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
    project_dir_env = os.environ.get("DEVSYNTH_PROJECT_DIR")
    in_test_env = project_dir_env is not None
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
        assert project_dir_env is not None
        test_project_dir = project_dir_env
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


def get_llm_settings(reload: bool = False, **kwargs: Any) -> dict[str, Any]:
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


__all__ = [
    "Settings",
    "get_settings",
    "get_llm_settings",
    "load_dotenv",
    "is_devsynth_managed_project",
    "ensure_path_exists",
    "DEFAULT_KUZU_EMBEDDED",
    "kuzu_db_path",
    "kuzu_embedded",
    "KUZU_EMBEDDED",
]
