"""
Provider System for abstracting LLM providers (OpenAI, LM Studio).

This module implements a unified interface for different LLM providers with
automatic fallback and selection based on configuration.

Proof of fallback correctness:
    docs/implementation/provider_system_invariants.md
Issue: issues/edrr-integration-with-real-llm-providers.md
"""

import asyncio
import importlib
import os
from collections.abc import Callable
from enum import Enum
from functools import lru_cache
from types import ModuleType, SimpleNamespace
from typing import Any

from devsynth.exceptions import ConfigurationError, ProviderError
from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import inc_provider
from devsynth.security.tls import TLSConfig

# Optional imports for HTTP clients; guard to avoid hard deps during tests/offline modes
httpx: Any | None
try:  # pragma: no cover - optional dependency
    import httpx
except Exception:  # pragma: no cover - absent when [llm] extra not installed
    httpx = None
requests: Any | None
try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - absent when [llm] extra not installed
    requests = None

# Create a logger for this module
logger = DevSynthLogger(__name__)

_SETTINGS_MODULE = "devsynth.config.settings"


def _load_settings_module() -> ModuleType:
    """Return a fully initialised settings module.

    ``importlib.reload`` is invoked when ``get_settings`` has not yet been
    exported—something that can happen during ``importlib.reload`` of modules
    that depend on :mod:`devsynth.config.settings`.  The helper guarantees a
    callable ``get_settings`` before returning the module.
    """

    module = importlib.import_module(_SETTINGS_MODULE)
    try:
        get_settings_attr = getattr(module, "get_settings", None)
    except AttributeError:
        get_settings_attr = None
    if callable(get_settings_attr):
        return module

    logger.debug(
        "Reloading %%s because get_settings was not yet available", _SETTINGS_MODULE
    )
    module = importlib.reload(module)
    try:
        get_settings_attr = getattr(module, "get_settings", None)
    except AttributeError:
        get_settings_attr = None
    if not callable(get_settings_attr):
        raise ImportError(
            "devsynth.config.settings does not expose get_settings after reload"
        )
    return module


def get_settings(*, reload: bool = False, **kwargs: Any) -> Any:
    """Proxy to :func:`devsynth.config.settings.get_settings` with reload safety."""

    module = _load_settings_module()
    get_settings_fn = getattr(module, "get_settings")
    return get_settings_fn(reload=reload, **kwargs)


def _env_flag_is_truthy(env_var: str, *, default: str = "") -> bool:
    """Return ``True`` when the environment variable represents a truthy flag."""

    value = os.environ.get(env_var, default)
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class ProviderType(Enum):
    """Enum for supported LLM providers."""

    OPENAI = "openai"
    LMSTUDIO = "lmstudio"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    STUB = "stub"


def get_env_or_default(env_var: str, default: str = None) -> str | None:
    """Get environment variable or return default value."""
    return os.environ.get(env_var, default)


def _load_env_file(config: dict[str, Any]) -> dict[str, Any]:
    """Load values from a local ``.env`` file into the provided config."""
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return config

    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value

                    if key == "OPENAI_API_KEY":
                        config["openai"]["api_key"] = value
                    elif key == "OPENAI_MODEL":
                        config["openai"]["model"] = value
                    elif key == "LM_STUDIO_ENDPOINT":
                        config["lmstudio"]["endpoint"] = value
                    elif key == "LM_STUDIO_MODEL":
                        config["lmstudio"]["model"] = value
                    elif key == "DEVSYNTH_PROVIDER":
                        config["default_provider"] = value
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(f"Error loading .env file: {exc}")

    return config


def _create_tls_config(settings: Any) -> TLSConfig:
    """Create a :class:`TLSConfig` from settings."""
    return TLSConfig(
        verify=getattr(settings, "tls_verify", True),
        cert_file=getattr(settings, "tls_cert_file", None),
        key_file=getattr(settings, "tls_key_file", None),
        ca_file=getattr(settings, "tls_ca_file", None),
    )


def _is_network_guard_error(exc: Exception) -> bool:
    """Return ``True`` when ``exc`` was raised by the network guard fixtures."""

    message = str(exc)
    if "Network access disabled during tests" in message:
        return True

    cause = getattr(exc, "__cause__", None)
    if cause is not None and _is_network_guard_error(cause):
        return True

    context = getattr(exc, "__context__", None)
    if context is not None and _is_network_guard_error(context):
        return True

    return False


@lru_cache(maxsize=1)
def get_provider_config() -> dict[str, Any]:
    """
    Get provider configuration from environment variables or .env file.

    Returns:
        Dict[str, Any]: Provider configuration
    """
    settings = get_settings()

    config = {
        "default_provider": get_env_or_default("DEVSYNTH_PROVIDER", "openai"),
        "openai": {
            "api_key": get_env_or_default("OPENAI_API_KEY"),
            "model": get_env_or_default("OPENAI_MODEL", "gpt-4"),
            "base_url": get_env_or_default(
                "OPENAI_BASE_URL", "https://api.openai.com/v1"
            ),
        },
        "lmstudio": {
            "endpoint": get_env_or_default(
                "LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234"
            ),
            "model": get_env_or_default("LM_STUDIO_MODEL", "default"),
        },
        "openrouter": {
            "api_key": get_env_or_default("OPENROUTER_API_KEY"),
            "model": get_env_or_default("OPENROUTER_MODEL"),
            "base_url": get_env_or_default(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
        },
        "retry": {
            "max_retries": getattr(settings, "provider_max_retries", 3),
            "initial_delay": getattr(settings, "provider_initial_delay", 1.0),
            "exponential_base": getattr(settings, "provider_exponential_base", 2.0),
            "max_delay": getattr(settings, "provider_max_delay", 60.0),
            "jitter": getattr(settings, "provider_jitter", True),
            "track_metrics": getattr(settings, "provider_retry_metrics", True),
            "conditions": [
                c.strip()
                for c in (
                    getattr(settings, "provider_retry_conditions", "") or ""
                ).split(",")
                if c.strip()
            ],
        },
        "fallback": {
            "enabled": getattr(settings, "provider_fallback_enabled", True),
            "order": getattr(
                settings, "provider_fallback_order", "openai,lmstudio"
            ).split(","),
        },
        "circuit_breaker": {
            "enabled": getattr(settings, "provider_circuit_breaker_enabled", True),
            "failure_threshold": getattr(settings, "provider_failure_threshold", 5),
            "recovery_timeout": getattr(settings, "provider_recovery_timeout", 60.0),
        },
    }

    return _load_env_file(config)


class ProviderFactory:
    """Factory class for creating provider instances."""

    @staticmethod
    def create_provider(
        provider_type: str | None = None,
        *,
        config: dict[str, Any] | None = None,
        tls_config: TLSConfig | None = None,
        retry_config: dict[str, Any] | None = None,
    ) -> "BaseProvider":
        """
        Create a provider instance based on the specified type or config.

        Args:
            provider_type: Optional provider type, defaults to config value

        Returns:
            BaseProvider: A provider instance

        Raises:
            ProviderError: If provider creation fails
        """
        # Reload provider configuration to respect updated environment variables
        if hasattr(get_provider_config, "cache_clear"):
            get_provider_config.cache_clear()
        config = config or get_provider_config()
        try:
            tls_settings = get_settings()
        except ConfigurationError:
            old_key = os.environ.pop("OPENAI_API_KEY", None)
            tls_settings = get_settings(reload=True)
            if old_key is not None:
                os.environ["OPENAI_API_KEY"] = old_key
        except (ImportError, RuntimeError) as exc:
            if config is None:
                raise
            logger.warning(
                "Settings unavailable; using default TLS configuration: %s", exc
            )
            tls_settings = SimpleNamespace(
                tls_verify=True,
                tls_cert_file=None,
                tls_key_file=None,
                tls_ca_file=None,
            )
        tls_conf = tls_config or _create_tls_config(tls_settings)

        # Global kill-switch for providers (useful in CI/tests)
        if _env_flag_is_truthy("DEVSYNTH_DISABLE_PROVIDERS"):
            logger.warning("Providers disabled via DEVSYNTH_DISABLE_PROVIDERS.")
            return NullProvider(reason="Disabled by DEVSYNTH_DISABLE_PROVIDERS")

        explicit_request = provider_type is not None
        if provider_type is None:
            provider_type = config["default_provider"]

        # Allow ProviderType enum values as well as strings
        if isinstance(provider_type, ProviderType):
            provider_type_value = provider_type.value
        else:
            provider_type_value = str(provider_type)

        # Helper to choose safe default (stub/null)
        safe_default = (
            os.environ.get("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub").strip().lower()
        )

        def _safe_provider(reason: str) -> "BaseProvider":
            if safe_default == ProviderType.STUB.value:
                logger.info("Falling back to Stub provider: %s", reason)
                return StubProvider(
                    tls_config=tls_conf,
                    retry_config=retry_config or config.get("retry"),
                )
            logger.info("Falling back to Null provider: %s", reason)
            return NullProvider(reason=reason)

        # Global offline guard to prevent accidental network calls
        if _env_flag_is_truthy("DEVSYNTH_OFFLINE"):
            if provider_type_value.lower() not in {ProviderType.STUB.value, "offline"}:
                return _safe_provider("DEVSYNTH_OFFLINE active; using safe provider")

        try:
            pt = provider_type_value.lower()
            if pt == ProviderType.OPENAI.value:
                if not config["openai"].get("api_key"):
                    if explicit_request:
                        logger.error(
                            "OpenAI API key is missing for explicitly "
                            "requested OpenAI provider. "
                            "Set OPENAI_API_KEY or choose a safe provider "
                            "via DEVSYNTH_PROVIDER=stub."
                        )
                        raise ProviderError(
                            "Missing OPENAI_API_KEY for OpenAI provider. "
                            "Set OPENAI_API_KEY or use DEVSYNTH_PROVIDER="
                            "stub."
                        )
                    # Attempt LM Studio only when explicitly marked available
                    # to avoid network calls by default
                    if _env_flag_is_truthy(
                        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", default="false"
                    ):
                        logger.warning(
                            "OPENAI_API_KEY not found; attempting LM Studio as fallback"
                        )
                        try:
                            return ProviderFactory.create_provider(
                                ProviderType.LMSTUDIO.value
                            )
                        except Exception as exc:
                            logger.warning("LM Studio unavailable: %s", exc)
                            return _safe_provider(
                                "No OPENAI_API_KEY and LM Studio unreachable. "
                                "Hint: export OPENAI_API_KEY, or export "
                                "DEVSYNTH_PROVIDER=stub for offline runs."
                            )
                    else:
                        return _safe_provider(
                            "No OPENAI_API_KEY; LM Studio not marked available. "
                            "Hint: export OPENAI_API_KEY, export "
                            "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true, "
                            "or set DEVSYNTH_PROVIDER=stub for offline runs."
                        )
                logger.info("Using OpenAI provider")
                return OpenAIProvider(
                    api_key=config["openai"]["api_key"],
                    model=config["openai"]["model"],
                    base_url=config["openai"]["base_url"],
                    tls_config=tls_conf,
                    retry_config=retry_config or config.get("retry"),
                )
            elif pt == ProviderType.LMSTUDIO.value:
                # Respect availability flag to avoid network calls when not desired
                if (
                    not _env_flag_is_truthy(
                        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", default="false"
                    )
                    and not explicit_request
                ):
                    return _safe_provider("LM Studio not marked available")
                logger.info("Using LM Studio provider")
                try:
                    return LMStudioProvider(
                        endpoint=config["lmstudio"]["endpoint"],
                        model=config["lmstudio"]["model"],
                        tls_config=tls_conf,
                        retry_config=retry_config or config.get("retry"),
                    )
                except Exception as exc:
                    logger.warning("LM Studio unavailable: %s", exc)
                    return _safe_provider("LM Studio unreachable")
            elif pt == ProviderType.ANTHROPIC.value:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    if explicit_request:
                        logger.error(
                            "Anthropic API key is missing for explicitly "
                            "requested Anthropic provider"
                        )
                        raise ProviderError(
                            "Anthropic API key is required for Anthropic provider"
                        )
                    return _safe_provider(
                        "No ANTHROPIC_API_KEY; falling back to safe default"
                    )
                # Anthropic not implemented in this adapter layer yet
                raise ProviderError(
                    "Anthropic provider is not supported in "
                    "adapters.provider_system; use application.llm.providers "
                    "or configure OpenAI/LM Studio."
                )
            elif pt == ProviderType.OPENROUTER.value:
                api_key = os.environ.get("OPENROUTER_API_KEY")
                if not api_key:
                    if explicit_request:
                        logger.error(
                            "OpenRouter API key is missing for explicitly "
                            "requested OpenRouter provider"
                        )
                        raise ProviderError(
                            "OpenRouter API key is required for OpenRouter provider"
                        )
                    return _safe_provider(
                        "No OPENROUTER_API_KEY; falling back to safe default"
                    )
                logger.info("Using OpenRouter provider")
                return OpenRouterProvider(
                    api_key=api_key,
                    base_url=config["openrouter"]["base_url"],
                    model=config["openrouter"].get("model"),
                    tls_config=tls_conf,
                    retry_config=retry_config or config.get("retry"),
                )
            elif pt == ProviderType.STUB.value:
                logger.info("Using Stub provider (deterministic, offline)")
                return StubProvider(
                    tls_config=tls_conf,
                    retry_config=retry_config or config.get("retry"),
                )
            else:
                logger.warning(
                    "Unknown provider type '%s', falling back to safe default",
                    provider_type,
                )
                return _safe_provider("Unknown provider type")
        except Exception as e:
            logger.error(f"Failed to create provider {provider_type}: {e}")
            return NullProvider(reason=f"Provider creation failed: {e}")


class BaseProvider:
    """Base class for all LLM providers."""

    def __init__(
        self,
        *,
        tls_config: TLSConfig | None = None,
        retry_config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the provider with implementation-specific kwargs."""
        self.kwargs = kwargs
        self.tls_config = tls_config or TLSConfig()

        config = retry_config or get_provider_config().get(
            "retry",
            {
                "max_retries": 3,
                "initial_delay": 1.0,
                "exponential_base": 2.0,
                "max_delay": 60.0,
                "jitter": True,
                "track_metrics": True,
                "conditions": [],
            },
        )
        self.retry_config = config

    def _emit_retry_telemetry(self, exc: Exception, attempt: int, delay: float) -> None:
        """Emit telemetry for a retry attempt."""
        logger.warning(
            "Retrying %s due to %s (attempt %d, delay %.2fs)",
            self.__class__.__name__,
            exc,
            attempt,
            delay,
        )
        inc_provider("retry")

    def get_retry_decorator(
        self,
        retryable_exceptions: tuple[Exception, ...] = (Exception,),
        *,
        should_retry: Callable[[Exception], bool] | None = None,
    ):
        """
        Get a retry decorator configured with the provider's retry settings.

        Args:
            retryable_exceptions: Tuple of exception types to retry on

        Returns:
            Callable: A configured retry decorator
        """
        return retry_with_exponential_backoff(
            max_retries=self.retry_config["max_retries"],
            initial_delay=self.retry_config["initial_delay"],
            exponential_base=self.retry_config["exponential_base"],
            max_delay=self.retry_config["max_delay"],
            jitter=self.retry_config["jitter"],
            retry_conditions=self.retry_config.get("conditions"),
            track_metrics=self.retry_config.get("track_metrics", True),
            retryable_exceptions=retryable_exceptions,
            should_retry=should_retry,
            on_retry=self._emit_retry_telemetry,
        )

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a completion from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            str: Generated completion

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement complete()")

    def complete_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Generate a completion given a chat ``context``."""
        raise NotImplementedError("Subclasses must implement complete_with_context()")

    def embed(self, text: str | list[str]) -> list[list[float]]:
        """
        Generate embeddings for input text.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement embed()")

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Asynchronous version of :meth:`complete`."""
        raise NotImplementedError("Subclasses must implement acomplete()")

    async def aembed(self, text: str | list[str]) -> list[list[float]]:
        """Asynchronous version of :meth:`embed`."""
        raise NotImplementedError("Subclasses must implement aembed()")


class NullProvider(BaseProvider):
    """A no-op provider that fails fast with a clear message.

    Used when remote providers are not configured or unavailable to avoid hangs.
    """

    def __init__(self, reason: str = "Provider disabled", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.reason = reason

    def complete(self, *args, **kwargs) -> str:  # pragma: no cover - simple guard
        message = (
            f"LLM provider is disabled: {self.reason}. "
            "Set OPENAI_API_KEY or start LM Studio."
        )
        raise ProviderError(message)

    async def acomplete(
        self, *args, **kwargs
    ) -> str:  # pragma: no cover - simple guard
        message = (
            f"LLM provider is disabled: {self.reason}. "
            "Set OPENAI_API_KEY or start LM Studio."
        )
        raise ProviderError(message)

    def embed(self, *args, **kwargs):  # pragma: no cover - simple guard
        raise ProviderError(
            f"Embeddings unavailable because provider is disabled: {self.reason}."
        )

    async def aembed(self, *args, **kwargs):  # pragma: no cover - simple guard
        raise ProviderError(
            f"Embeddings unavailable because provider is disabled: {self.reason}."
        )


class StubProvider(BaseProvider):
    """Deterministic local stub for tests and offline development.

    - No network calls.
    - Deterministic outputs based on SHA-256 of input.
    - Useful when DEVSYNTH_PROVIDER=stub or in tests.
    """

    def __init__(self, *, name: str = "stub-llm", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.name = name

    @staticmethod
    def _to_deterministic_floats(data: str | bytes, *, size: int = 8) -> list[float]:
        import hashlib

        if isinstance(data, str):
            data = data.encode("utf-8")
        digest = hashlib.sha256(data).digest()
        # Map first `size` bytes into floats in [0,1)
        return [b / 255.0 for b in digest[:size]]

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        sys = f"[sys:{system_prompt}] " if system_prompt else ""
        return f"{sys}[stub:{self.name}] {prompt}"[: max_tokens or 10_000]

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        return self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            parameters=parameters,
        )

    def embed(self, text: str | list[str]) -> list[list[float]]:
        if isinstance(text, str):
            texts = [text]
        else:
            texts = list(text)
        return [self._to_deterministic_floats(t) for t in texts]

    async def aembed(self, text: str | list[str]) -> list[list[float]]:
        return self.embed(text)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        base_url: str = "https://api.openai.com/v1",
        tls_config: TLSConfig | None = None,
        retry_config: dict[str, Any] | None = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
            base_url: Base URL for API (default: OpenAI's API)
        """
        if requests is None:
            # Avoid import-time hard dependency when [llm] extra is not installed
            raise ProviderError(
                "The 'requests' package is required for OpenAI provider. "
                "Install the 'devsynth[llm]' extra or set "
                "DEVSYNTH_SAFE_DEFAULT_PROVIDER=stub."
            )
        super().__init__(
            tls_config=tls_config,
            retry_config=retry_config,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        if retry_config is not None:
            self.retry_config = retry_config

    def _should_retry(self, exc: Exception) -> bool:
        """Return ``True`` if the exception should trigger a retry."""
        status = getattr(exc.response, "status_code", None)
        if status is None:
            status = getattr(exc, "status_code", None)
        if status is not None and 400 <= int(status) < 500 and int(status) != 429:
            return False
        return True

    def _get_retry_config(self):
        """Get the retry configuration for OpenAI API calls."""
        return {
            "max_retries": self.retry_config["max_retries"],
            "initial_delay": self.retry_config["initial_delay"],
            "exponential_base": self.retry_config["exponential_base"],
            "max_delay": self.retry_config["max_delay"],
            "jitter": self.retry_config["jitter"],
            "track_metrics": self.retry_config.get("track_metrics", True),
            "conditions": self.retry_config.get("conditions"),
        }

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a completion using OpenAI API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            str: Generated completion

        Raises:
            ProviderError: If API call fails
        """

        # Define the actual API call function
        if parameters:
            temperature = parameters.get("temperature", temperature)
            max_tokens = parameters.get("max_tokens", max_tokens)
            top_p = parameters.get("top_p")

            if not 0 <= temperature <= 2:
                raise ProviderError("temperature must be between 0 and 2")
            if max_tokens <= 0:
                raise ProviderError("max_tokens must be positive")
            if top_p is not None and not 0 <= top_p <= 1:
                raise ProviderError("top_p must be between 0 and 1")

        def _api_call():
            url = f"{self.base_url}/chat/completions"

            if parameters and "messages" in parameters:
                messages = list(parameters["messages"])
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if parameters:
                extra = {
                    k: v
                    for k, v in parameters.items()
                    if k not in {"temperature", "max_tokens"}
                }
                payload.update(extra)

            kwargs = self.tls_config.as_requests_kwargs()
            timeout = kwargs.pop("timeout")
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            response_data = response.json()

            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            else:
                raise ProviderError(f"Invalid response format: {response_data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()
            return retry_with_exponential_backoff(
                max_retries=retry_config["max_retries"],
                initial_delay=retry_config["initial_delay"],
                exponential_base=retry_config["exponential_base"],
                max_delay=retry_config["max_delay"],
                jitter=retry_config["jitter"],
                retry_conditions=retry_config.get("conditions"),
                track_metrics=retry_config.get("track_metrics", True),
                should_retry=self._should_retry,
                retryable_exceptions=(requests.exceptions.RequestException,),
                on_retry=self._emit_retry_telemetry,
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API error: {e}")
            raise ProviderError(f"OpenAI API error: {e}")

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Asynchronously generate a completion using the OpenAI API."""
        if httpx is None:
            raise ProviderError(
                "The 'httpx' package is required for async OpenAI operations. "
                "Install 'devsynth[llm]' or use synchronous methods."
            )

        # Define the actual API call function
        async def _api_call():
            url = f"{self.base_url}/chat/completions"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            raise ProviderError(f"Invalid response format: {data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()

            # For async functions, create a wrapper that handles the async nature
            async def _retry_async_wrapper():
                decorator = retry_with_exponential_backoff(
                    max_retries=retry_config["max_retries"],
                    initial_delay=retry_config["initial_delay"],
                    exponential_base=retry_config["exponential_base"],
                    max_delay=retry_config["max_delay"],
                    jitter=retry_config["jitter"],
                    should_retry=self._should_retry,
                    retryable_exceptions=(httpx.HTTPError,),
                )

                # Create a sync function that awaits the async function
                def _sync_wrapper():
                    import asyncio

                    return asyncio.run(_api_call())

                # Apply the decorator to the sync wrapper
                decorated_sync = decorator(_sync_wrapper)

                # Call the decorated sync function
                return decorated_sync()

            # Since we can't easily decorate async functions with retry,
            # we'll just implement a simple retry loop here
            max_retries = retry_config["max_retries"]
            initial_delay = retry_config["initial_delay"]
            exponential_base = retry_config["exponential_base"]
            max_delay = retry_config["max_delay"]
            jitter = retry_config["jitter"]

            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return await _api_call()
                except httpx.HTTPError as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count > max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (retry_count - 1)),
                        max_delay,
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    self._emit_retry_telemetry(e, retry_count, delay)
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            logger.error(
                f"OpenAI API error after {max_retries} retries: {last_exception}"
            )
            raise ProviderError(
                f"OpenAI API error after {max_retries} retries: {last_exception}"
            )

        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ProviderError(f"OpenAI API error: {e}")

    def complete_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Generate a completion using provided chat ``context`` messages."""
        messages = list(context) + [{"role": "user", "content": prompt}]

        system_msg = None
        if messages and messages[0].get("role") == "system":
            system_msg = messages.pop(0)["content"]

        return self.complete(
            prompt,
            system_prompt=system_msg,
            parameters={**(parameters or {}), "messages": messages},
        )

    def embed(self, text: str | list[str]) -> list[list[float]]:
        """
        Generate embeddings using OpenAI API.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            ProviderError: If API call fails
        """

        # Define the actual API call function
        def _api_call():
            url = f"{self.base_url}/embeddings"

            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            payload = {
                "model": "text-embedding-3-small",  # Use appropriate embedding model
                "input": text_list,
            }

            kwargs = self.tls_config.as_requests_kwargs()
            timeout = kwargs.pop("timeout")
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            response_data = response.json()

            if "data" in response_data and len(response_data["data"]) > 0:
                return [item["embedding"] for item in response_data["data"]]
            else:
                raise ProviderError(
                    f"Invalid embedding response format: {response_data}"
                )

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()
            return retry_with_exponential_backoff(
                max_retries=retry_config["max_retries"],
                initial_delay=retry_config["initial_delay"],
                exponential_base=retry_config["exponential_base"],
                max_delay=retry_config["max_delay"],
                jitter=retry_config["jitter"],
                retry_conditions=retry_config.get("conditions"),
                track_metrics=retry_config.get("track_metrics", True),
                should_retry=self._should_retry,
                retryable_exceptions=(requests.exceptions.RequestException,),
                on_retry=self._emit_retry_telemetry,
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI embedding API error: {e}")
            raise ProviderError(f"OpenAI embedding API error: {e}")

    async def aembed(self, text: str | list[str]) -> list[list[float]]:
        """Asynchronously generate embeddings using the OpenAI API."""
        if httpx is None:
            raise ProviderError(
                "The 'httpx' package is required for async OpenAI operations. "
                "Install 'devsynth[llm]' or use synchronous methods."
            )

        # Define the actual API call function
        async def _api_call():
            url = f"{self.base_url}/embeddings"

            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            payload = {
                "model": "text-embedding-3-small",
                "input": text_list,
            }

            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "data" in data and len(data["data"]) > 0:
                return [item["embedding"] for item in data["data"]]
            raise ProviderError(f"Invalid embedding response format: {data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()

            # Since we can't easily decorate async functions with retry,
            # we'll just implement a simple retry loop here
            max_retries = retry_config["max_retries"]
            initial_delay = retry_config["initial_delay"]
            exponential_base = retry_config["exponential_base"]
            max_delay = retry_config["max_delay"]
            jitter = retry_config["jitter"]

            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return await _api_call()
                except httpx.HTTPError as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count > max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (retry_count - 1)),
                        max_delay,
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    self._emit_retry_telemetry(e, retry_count, delay)
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            message = (
                "OpenAI embedding API error after "
                f"{max_retries} retries: {last_exception}"
            )
            logger.error(message)
            raise ProviderError(message)

        except httpx.HTTPError as e:
            logger.error(f"OpenAI embedding API error: {e}")
            raise ProviderError(f"OpenAI embedding API error: {e}")


class LMStudioProvider(BaseProvider):
    """LM Studio local provider implementation."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:1234",
        model: str = "default",
        tls_config: TLSConfig | None = None,
        retry_config: dict[str, Any] | None = None,
    ):
        """
        Initialize LM Studio provider.

        Args:
            endpoint: LM Studio API endpoint
            model: Model name (ignored in LM Studio, uses loaded model)
        """
        if requests is None:
            # Avoid import-time hard dependency when [llm] extra is not installed
            raise ProviderError(
                "The 'requests' package is required for LM Studio provider. "
                "Install the 'devsynth[llm]' extra or set "
                "DEVSYNTH_SAFE_DEFAULT_PROVIDER=stub."
            )
        super().__init__(
            tls_config=tls_config,
            retry_config=retry_config,
            endpoint=endpoint,
            model=model,
        )
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.headers = {"Content-Type": "application/json"}

        if retry_config is not None:
            self.retry_config = retry_config

        # Fast short-circuit: if LM Studio is unreachable, fail fast to avoid
        # hangs
        try:
            # Use a very small connect timeout to avoid test hangs; allow a
            # slightly larger read timeout
            # Ping a lightweight endpoint to verify availability
            health_url = f"{self.endpoint}/api/v0/models"
            # Get TLS config kwargs but override timeout for this specific check
            tls_kwargs = self.tls_config.as_requests_kwargs()
            tls_kwargs["timeout"] = (0.2, 1.0)  # Override timeout for health check
            requests.get(health_url, **tls_kwargs)
        except Exception as exc:
            if _is_network_guard_error(exc):
                logger.info(
                    "Skipping LM Studio health check because network access is "
                    "disabled: %s",
                    exc,
                )
            else:
                raise ProviderError(
                    "LM Studio endpoint is not reachable; provider disabled. "
                    "Set OPENAI_API_KEY for OpenAI or start LM Studio at "
                    "LM_STUDIO_ENDPOINT."
                ) from exc

    def _should_retry(self, exc: Exception) -> bool:
        """Return ``True`` if the exception should trigger a retry."""
        status = getattr(exc.response, "status_code", None)
        if status is None:
            status = getattr(exc, "status_code", None)
        if status is not None and 400 <= int(status) < 500 and int(status) != 429:
            return False
        return True

    def _get_retry_config(self):
        """Get the retry configuration for LM Studio API calls."""
        return {
            "max_retries": self.retry_config["max_retries"],
            "initial_delay": self.retry_config["initial_delay"],
            "exponential_base": self.retry_config["exponential_base"],
            "max_delay": self.retry_config["max_delay"],
            "jitter": self.retry_config["jitter"],
            "track_metrics": self.retry_config.get("track_metrics", True),
            "conditions": self.retry_config.get("conditions"),
        }

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a completion using LM Studio API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            str: Generated completion

        Raises:
            ProviderError: If API call fails
        """

        # Define the actual API call function
        if parameters:
            temperature = parameters.get("temperature", temperature)
            max_tokens = parameters.get("max_tokens", max_tokens)
            top_p = parameters.get("top_p")

            if not 0 <= temperature <= 2:
                raise ProviderError("temperature must be between 0 and 2")
            if max_tokens <= 0:
                raise ProviderError("max_tokens must be positive")
            if top_p is not None and not 0 <= top_p <= 1:
                raise ProviderError("top_p must be between 0 and 1")

        def _api_call():
            url = f"{self.endpoint}/v1/chat/completions"

            if parameters and "messages" in parameters:
                messages = list(parameters["messages"])
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

            payload = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if parameters:
                extra = {
                    k: v
                    for k, v in parameters.items()
                    if k not in {"temperature", "max_tokens", "messages"}
                }
                payload.update(extra)

            kwargs = self.tls_config.as_requests_kwargs()
            timeout = kwargs.pop("timeout")
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            response_data = response.json()

            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if isinstance(choice, dict):
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    if "text" in choice:
                        return choice["text"]
            raise ProviderError(f"Invalid LM Studio response format: {response_data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()
            return retry_with_exponential_backoff(
                max_retries=retry_config["max_retries"],
                initial_delay=retry_config["initial_delay"],
                exponential_base=retry_config["exponential_base"],
                max_delay=retry_config["max_delay"],
                jitter=retry_config["jitter"],
                retry_conditions=retry_config.get("conditions"),
                track_metrics=retry_config.get("track_metrics", True),
                should_retry=self._should_retry,
                retryable_exceptions=(requests.exceptions.RequestException,),
                on_retry=self._emit_retry_telemetry,
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            msg = (
                f"LM Studio endpoint {self.endpoint} is unreachable. "
                "Ensure the server is running."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Asynchronously generate a completion using LM Studio."""
        if httpx is None:
            raise ProviderError(
                "The 'httpx' package is required for async LM Studio operations. "
                "Install 'devsynth[llm]' or use synchronous methods."
            )
        # Define the actual API call function
        if parameters:
            temperature = parameters.get("temperature", temperature)
            max_tokens = parameters.get("max_tokens", max_tokens)
            top_p = parameters.get("top_p")

            if not 0 <= temperature <= 2:
                raise ProviderError("temperature must be between 0 and 2")
            if max_tokens <= 0:
                raise ProviderError("max_tokens must be positive")
            if top_p is not None and not 0 <= top_p <= 1:
                raise ProviderError("top_p must be between 0 and 1")

        async def _api_call():
            url = f"{self.endpoint}/v1/chat/completions"

            if parameters and "messages" in parameters:
                messages = list(parameters["messages"])
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

            payload = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if parameters:
                extra = {
                    k: v
                    for k, v in parameters.items()
                    if k not in {"temperature", "max_tokens", "messages"}
                }
                payload.update(extra)

            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if isinstance(choice, dict):
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    if "text" in choice:
                        return choice["text"]
            raise ProviderError(f"Invalid LM Studio response format: {data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()

            # Since we can't easily decorate async functions with retry,
            # we'll just implement a simple retry loop here
            max_retries = retry_config["max_retries"]
            initial_delay = retry_config["initial_delay"]
            exponential_base = retry_config["exponential_base"]
            max_delay = retry_config["max_delay"]
            jitter = retry_config["jitter"]

            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return await _api_call()
                except httpx.HTTPError as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count > max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (retry_count - 1)),
                        max_delay,
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    self._emit_retry_telemetry(e, retry_count, delay)
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            msg = (
                f"LM Studio endpoint {self.endpoint} is unreachable after "
                f"{max_retries} retries: {last_exception}"
            )
            logger.error(msg)
            raise ProviderError(msg)

        except httpx.HTTPError as e:
            msg = (
                f"LM Studio endpoint {self.endpoint} is unreachable. "
                "Ensure the server is running."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e

    def complete_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Generate a completion using chat ``context``."""
        messages = list(context) + [{"role": "user", "content": prompt}]

        system_msg = None
        if messages and messages[0].get("role") == "system":
            system_msg = messages.pop(0)["content"]

        return self.complete(
            prompt,
            system_prompt=system_msg,
            parameters={**(parameters or {}), "messages": messages},
        )

    def embed(self, text: str | list[str]) -> list[list[float]]:
        """
        Generate embeddings using the LM Studio API.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            ProviderError: If API call fails
        """

        # Define the actual API call function
        def _api_call():
            url = f"{self.endpoint}/v1/embeddings"

            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            payload = {"input": text_list, "model": self.model}

            kwargs = self.tls_config.as_requests_kwargs()
            timeout = kwargs.pop("timeout")
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            response_data = response.json()

            if "data" in response_data and len(response_data["data"]) > 0:
                return [item["embedding"] for item in response_data["data"]]
            raise ProviderError(
                f"Invalid LM Studio embedding response format: {response_data}"
            )

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()
            return retry_with_exponential_backoff(
                max_retries=retry_config["max_retries"],
                initial_delay=retry_config["initial_delay"],
                exponential_base=retry_config["exponential_base"],
                max_delay=retry_config["max_delay"],
                jitter=retry_config["jitter"],
                retry_conditions=retry_config.get("conditions"),
                track_metrics=retry_config.get("track_metrics", True),
                should_retry=self._should_retry,
                retryable_exceptions=(requests.exceptions.RequestException,),
                on_retry=self._emit_retry_telemetry,
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            msg = (
                f"LM Studio endpoint {self.endpoint} is unreachable. "
                "Ensure the server is running."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e

    async def aembed(self, text: str | list[str]) -> list[list[float]]:
        """Asynchronously generate embeddings using the LM Studio API."""

        # Define the actual API call function
        async def _api_call():
            url = f"{self.endpoint}/v1/embeddings"

            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            payload = {"input": text_list, "model": self.model}

            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "data" in data and len(data["data"]) > 0:
                return [item["embedding"] for item in data["data"]]
            raise ProviderError(f"Invalid LM Studio embedding response format: {data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()

            # Since we can't easily decorate async functions with retry,
            # we'll just implement a simple retry loop here
            max_retries = retry_config["max_retries"]
            initial_delay = retry_config["initial_delay"]
            exponential_base = retry_config["exponential_base"]
            max_delay = retry_config["max_delay"]
            jitter = retry_config["jitter"]

            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return await _api_call()
                except httpx.HTTPError as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count > max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (retry_count - 1)),
                        max_delay,
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    self._emit_retry_telemetry(e, retry_count, delay)
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            msg = (
                f"LM Studio endpoint {self.endpoint} is unreachable after "
                f"{max_retries} retries: {last_exception}"
            )
            logger.error(msg)
            raise ProviderError(msg)

        except httpx.HTTPError as e:
            msg = (
                f"LM Studio endpoint {self.endpoint} is unreachable. "
                "Ensure the server is running."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider implementation."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str | None = None,
        tls_config: TLSConfig | None = None,
        retry_config: dict[str, Any] | None = None,
    ):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            base_url: Base URL for OpenRouter API
            model: Model name (optional, defaults to free-tier)
        """
        if requests is None:
            # Avoid import-time hard dependency when [llm] extra is not installed
            raise ProviderError(
                "The 'requests' package is required for OpenRouter provider. "
                "Install the 'devsynth[llm]' extra or set "
                "DEVSYNTH_SAFE_DEFAULT_PROVIDER=stub."
            )
        super().__init__(
            tls_config=tls_config,
            retry_config=retry_config,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://devsynth.dev",
            "X-Title": "DevSynth AI Platform",
        }

        if retry_config is not None:
            self.retry_config = retry_config

    def _should_retry(self, exc: Exception) -> bool:
        """Return ``True`` if the exception should trigger a retry."""
        status = getattr(exc.response, "status_code", None)
        if status is None:
            status = getattr(exc, "status_code", None)
        if status is not None and 400 <= int(status) < 500 and int(status) != 429:
            return False
        return True

    def _get_retry_config(self):
        """Get the retry configuration for OpenRouter API calls."""
        return {
            "max_retries": self.retry_config["max_retries"],
            "initial_delay": self.retry_config["initial_delay"],
            "exponential_base": self.retry_config["exponential_base"],
            "max_delay": self.retry_config["max_delay"],
            "jitter": self.retry_config["jitter"],
            "track_metrics": self.retry_config.get("track_metrics", True),
            "conditions": self.retry_config.get("conditions"),
        }

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a completion using OpenRouter API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            str: Generated completion

        Raises:
            ProviderError: If API call fails
        """

        # Define the actual API call function
        if parameters:
            temperature = parameters.get("temperature", temperature)
            max_tokens = parameters.get("max_tokens", max_tokens)
            top_p = parameters.get("top_p")

            if not 0 <= temperature <= 2:
                raise ProviderError("temperature must be between 0 and 2")
            if max_tokens <= 0:
                raise ProviderError("max_tokens must be positive")
            if top_p is not None and not 0 <= top_p <= 1:
                raise ProviderError("top_p must be between 0 and 1")

        def _api_call():
            url = f"{self.base_url}/chat/completions"

            if parameters and "messages" in parameters:
                messages = list(parameters["messages"])
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model
                or "google/gemini-flash-1.5",  # Default to free tier
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if parameters:
                extra = {
                    k: v
                    for k, v in parameters.items()
                    if k not in {"temperature", "max_tokens", "messages"}
                }
                payload.update(extra)

            kwargs = self.tls_config.as_requests_kwargs()
            timeout = kwargs.pop("timeout")
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            response_data = response.json()

            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if isinstance(choice, dict):
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    if "text" in choice:
                        return choice["text"]
            raise ProviderError(f"Invalid OpenRouter response format: {response_data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()
            return retry_with_exponential_backoff(
                max_retries=retry_config["max_retries"],
                initial_delay=retry_config["initial_delay"],
                exponential_base=retry_config["exponential_base"],
                max_delay=retry_config["max_delay"],
                jitter=retry_config["jitter"],
                retry_conditions=retry_config.get("conditions"),
                track_metrics=retry_config.get("track_metrics", True),
                should_retry=self._should_retry,
                retryable_exceptions=(requests.exceptions.RequestException,),
                on_retry=self._emit_retry_telemetry,
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            msg = (
                "OpenRouter API is unreachable. "
                "Check your API key and internet connection."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Asynchronously generate a completion using OpenRouter."""
        if httpx is None:
            raise ProviderError(
                "The 'httpx' package is required for async OpenRouter operations. "
                "Install 'devsynth[llm]' or use synchronous methods."
            )
        # Define the actual API call function
        if parameters:
            temperature = parameters.get("temperature", temperature)
            max_tokens = parameters.get("max_tokens", max_tokens)
            top_p = parameters.get("top_p")

            if not 0 <= temperature <= 2:
                raise ProviderError("temperature must be between 0 and 2")
            if max_tokens <= 0:
                raise ProviderError("max_tokens must be positive")
            if top_p is not None and not 0 <= top_p <= 1:
                raise ProviderError("top_p must be between 0 and 1")

        async def _api_call():
            url = f"{self.base_url}/chat/completions"

            if parameters and "messages" in parameters:
                messages = list(parameters["messages"])
            else:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model
                or "google/gemini-flash-1.5",  # Default to free tier
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if parameters:
                extra = {
                    k: v
                    for k, v in parameters.items()
                    if k not in {"temperature", "max_tokens", "messages"}
                }
                payload.update(extra)

            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if isinstance(choice, dict):
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    if "text" in choice:
                        return choice["text"]
            raise ProviderError(f"Invalid OpenRouter response format: {data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()

            # Since we can't easily decorate async functions with retry,
            # we'll just implement a simple retry loop here
            max_retries = retry_config["max_retries"]
            initial_delay = retry_config["initial_delay"]
            exponential_base = retry_config["exponential_base"]
            max_delay = retry_config["max_delay"]
            jitter = retry_config["jitter"]

            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return await _api_call()
                except httpx.HTTPError as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count > max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (retry_count - 1)),
                        max_delay,
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    self._emit_retry_telemetry(e, retry_count, delay)
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            msg = (
                f"OpenRouter API is unreachable after "
                f"{max_retries} retries: {last_exception}"
            )
            logger.error(msg)
            raise ProviderError(msg)

        except httpx.HTTPError as e:
            msg = (
                "OpenRouter API is unreachable. "
                "Check your API key and internet connection."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e

    def complete_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Generate a completion using chat ``context``."""
        messages = list(context) + [{"role": "user", "content": prompt}]

        system_msg = None
        if messages and messages[0].get("role") == "system":
            system_msg = messages.pop(0)["content"]

        return self.complete(
            prompt,
            system_prompt=system_msg,
            parameters={**(parameters or {}), "messages": messages},
        )

    def embed(self, text: str | list[str]) -> list[list[float]]:
        """
        Generate embeddings using the OpenRouter API.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            ProviderError: If API call fails
        """

        # Define the actual API call function
        def _api_call():
            url = f"{self.base_url}/embeddings"

            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            # Use OpenAI-compatible embedding model
            payload = {
                "model": "text-embedding-ada-002",
                "input": text_list,
            }

            kwargs = self.tls_config.as_requests_kwargs()
            timeout = kwargs.pop("timeout")
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            response_data = response.json()

            if "data" in response_data and len(response_data["data"]) > 0:
                return [item["embedding"] for item in response_data["data"]]
            raise ProviderError(
                f"Invalid OpenRouter embedding response format: {response_data}"
            )

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()
            return retry_with_exponential_backoff(
                max_retries=retry_config["max_retries"],
                initial_delay=retry_config["initial_delay"],
                exponential_base=retry_config["exponential_base"],
                max_delay=retry_config["max_delay"],
                jitter=retry_config["jitter"],
                retry_conditions=retry_config.get("conditions"),
                track_metrics=retry_config.get("track_metrics", True),
                should_retry=self._should_retry,
                retryable_exceptions=(requests.exceptions.RequestException,),
                on_retry=self._emit_retry_telemetry,
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            msg = (
                "OpenRouter API is unreachable. "
                "Check your API key and internet connection."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e

    async def aembed(self, text: str | list[str]) -> list[list[float]]:
        """Asynchronously generate embeddings using the OpenRouter API."""

        # Define the actual API call function
        async def _api_call():
            url = f"{self.base_url}/embeddings"

            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            # Use OpenAI-compatible embedding model
            payload = {
                "model": "text-embedding-ada-002",
                "input": text_list,
            }

            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "data" in data and len(data["data"]) > 0:
                return [item["embedding"] for item in data["data"]]
            raise ProviderError(f"Invalid OpenRouter embedding response format: {data}")

        # Use retry with exponential backoff
        try:
            retry_config = self._get_retry_config()

            # Since we can't easily decorate async functions with retry,
            # we'll just implement a simple retry loop here
            max_retries = retry_config["max_retries"]
            initial_delay = retry_config["initial_delay"]
            exponential_base = retry_config["exponential_base"]
            max_delay = retry_config["max_delay"]
            jitter = retry_config["jitter"]

            retry_count = 0
            last_exception = None

            while retry_count <= max_retries:
                try:
                    return await _api_call()
                except httpx.HTTPError as e:
                    last_exception = e
                    retry_count += 1

                    if retry_count > max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (retry_count - 1)),
                        max_delay,
                    )

                    # Add jitter if enabled
                    if jitter:
                        import random

                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    self._emit_retry_telemetry(e, retry_count, delay)
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            msg = (
                f"OpenRouter API is unreachable after "
                f"{max_retries} retries: {last_exception}"
            )
            logger.error(msg)
            raise ProviderError(msg)

        except httpx.HTTPError as e:
            msg = (
                "OpenRouter API is unreachable. "
                "Check your API key and internet connection."
            )
            logger.error("%s: %s", msg, e)
            raise ProviderError(msg) from e


class FallbackProvider(BaseProvider):
    """Fallback provider that tries multiple providers in sequence."""

    def __init__(
        self,
        providers: list[BaseProvider] | None = None,
        *,
        config: dict[str, Any] | None = None,
        provider_factory: Any = ProviderFactory,
    ) -> None:
        """Initialize with optional provider list and config."""
        super().__init__(retry_config=(config or get_provider_config()).get("retry"))

        self.config = config or get_provider_config()
        self.fallback_config = self.config.get(
            "fallback",
            {"enabled": True, "order": ["openai", "lmstudio"]},
        )
        self.circuit_breaker_config = self.config.get(
            "circuit_breaker",
            {"enabled": True, "failure_threshold": 5, "recovery_timeout": 60.0},
        )

        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.provider_factory = provider_factory
        self.providers = providers or self._initialize_providers()

        if not self.providers:
            raise ProviderError("No valid providers available for fallback")

        logger.info(
            "Initialized fallback provider order: %s",
            ", ".join(p.__class__.__name__ for p in self.providers),
        )

    def _initialize_providers(self) -> list[BaseProvider]:
        """Create provider instances based on config order."""
        providers: list[BaseProvider] = []
        provider_order = self.fallback_config["order"]

        for provider_type in provider_order:
            try:
                provider = self.provider_factory.create_provider(
                    provider_type,
                    config=self.config,
                    retry_config=self.config.get("retry"),
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    f"Failed to create {provider_type} provider: {exc}; continuing"
                )
                continue

            providers.append(provider)
            if self.circuit_breaker_config["enabled"]:
                self.circuit_breakers[provider_type] = CircuitBreaker(
                    failure_threshold=self.circuit_breaker_config["failure_threshold"],
                    recovery_timeout=self.circuit_breaker_config["recovery_timeout"],
                )

        return providers

    @staticmethod
    def _provider_type(provider: BaseProvider) -> str:
        return provider.__class__.__name__.replace("Provider", "").lower()

    def _call_sync(self, provider: BaseProvider, method: str, **kwargs: Any) -> Any:
        ptype = self._provider_type(provider)
        if (
            self.circuit_breaker_config.get("enabled", True)
            and ptype in self.circuit_breakers
        ):
            return self.circuit_breakers[ptype].call(
                getattr(provider, method), **kwargs
            )
        return getattr(provider, method)(**kwargs)

    async def _call_async(
        self, provider: BaseProvider, method: str, **kwargs: Any
    ) -> Any:
        ptype = self._provider_type(provider)
        if (
            self.circuit_breaker_config.get("enabled", True)
            and ptype in self.circuit_breakers
            and self.circuit_breakers[ptype].state != "closed"
        ):
            logger.warning(
                f"Provider {provider.__class__.__name__} circuit breaker is open"
            )
            raise ProviderError(
                f"Provider {provider.__class__.__name__} circuit breaker is open"
            )

        try:
            result = await getattr(provider, method)(**kwargs)
        except Exception as exc:
            if (
                self.circuit_breaker_config.get("enabled", True)
                and ptype in self.circuit_breakers
            ):
                self.circuit_breakers[ptype]._record_failure()
            raise ProviderError(f"Provider {provider.__class__.__name__} failed: {exc}")
        else:
            if (
                self.circuit_breaker_config.get("enabled", True)
                and ptype in self.circuit_breakers
            ):
                self.circuit_breakers[ptype]._record_success()
            return result

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Try providers sequentially until one succeeds."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    "Trying completion with provider: %s",
                    provider.__class__.__name__,
                )
                return self._call_sync(
                    provider,
                    "complete",
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    parameters=parameters,
                )
            except Exception as exc:
                logger.warning(
                    "Provider %s failed: %s",
                    provider.__class__.__name__,
                    exc,
                )
                last_error = exc

        raise ProviderError(
            f"All providers failed for completion. Last error: {last_error}"
        )

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Asynchronously try providers until one succeeds."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    "Trying async completion with provider: %s",
                    provider.__class__.__name__,
                )
                return await self._call_async(
                    provider,
                    "acomplete",
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    parameters=parameters,
                )
            except Exception as exc:
                logger.warning(
                    "Provider %s failed: %s",
                    provider.__class__.__name__,
                    exc,
                )
                last_error = exc

        raise ProviderError(
            f"All providers failed for completion. Last error: {last_error}"
        )

    def embed(self, text: str | list[str]) -> list[list[float]]:
        """Try providers sequentially to generate embeddings."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    "Trying embeddings with provider: %s",
                    provider.__class__.__name__,
                )
                return self._call_sync(provider, "embed", text=text)
            except Exception as exc:
                logger.warning(
                    "Provider %s failed for embeddings: %s",
                    provider.__class__.__name__,
                    exc,
                )
                last_error = exc

        raise ProviderError(
            f"All providers failed for embeddings. Last error: {last_error}"
        )

    async def aembed(self, text: str | list[str]) -> list[list[float]]:
        """Asynchronously try providers for embeddings."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    "Trying async embeddings with provider: %s",
                    provider.__class__.__name__,
                )
                return await self._call_async(provider, "aembed", text=text)
            except Exception as exc:
                logger.warning(
                    "Provider %s failed for embeddings: %s",
                    provider.__class__.__name__,
                    exc,
                )
                last_error = exc

        raise ProviderError(
            f"All providers failed for embeddings. Last error: {last_error}"
        )


# Simplified API for common usage
def get_provider(
    provider_type: str | None = None, fallback: bool = False
) -> BaseProvider:
    """
    Get a provider instance, optionally with fallback capability.

    Args:
        provider_type: Optional provider type, defaults to config value
        fallback: Whether to use fallback mechanism

    Returns:
        BaseProvider: A provider instance
    """
    if fallback:
        return FallbackProvider()
    else:
        return ProviderFactory.create_provider(provider_type)


def complete(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    provider_type: str | None = None,
    fallback: bool = True,
    *,
    parameters: dict[str, Any] | None = None,
) -> str:
    """
    Generate a completion using the configured provider.

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate
        provider_type: Optional provider type, defaults to config value
        fallback: Whether to use fallback mechanism

    Returns:
        str: Generated completion
    """
    provider = get_provider(provider_type=provider_type, fallback=fallback)
    inc_provider("complete")
    # Only pass ``parameters`` if explicitly provided to keep the mocked
    # call signatures simple in unit tests and avoid provider implementations
    # receiving ``parameters=None``.
    call_args = {
        "prompt": prompt,
        "system_prompt": system_prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if parameters is not None:
        call_args["parameters"] = parameters
    return provider.complete(**call_args)


def embed(
    text: str | list[str],
    provider_type: str | None = None,
    fallback: bool = True,
) -> list[list[float]]:
    """
    Generate embeddings using the configured provider.

    Args:
        text: Input text or list of texts
        provider_type: Optional provider type, defaults to config value
        fallback: Whether to use fallback mechanism

    Returns:
        List[List[float]]: Embeddings
    """
    provider = get_provider(provider_type=provider_type, fallback=fallback)
    inc_provider("embed")
    try:
        return provider.embed(text=text)
    except NotImplementedError as exc:  # pragma: no cover - defensive
        raise ProviderError(
            f"Embeddings not supported by provider {provider.__class__.__name__}"
        ) from exc
    except ProviderError:
        # Already the canonical ProviderError; propagate intact
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        # If downstream raised a ProviderError from another context, treat it as such
        if isinstance(exc, ProviderError):
            raise exc
        raise ProviderError(f"Embedding call failed: {exc}") from exc


async def acomplete(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    provider_type: str | None = None,
    fallback: bool = True,
) -> str:
    """Asynchronously generate a completion using the configured provider."""
    provider = get_provider(provider_type=provider_type, fallback=fallback)
    inc_provider("acomplete")
    return await provider.acomplete(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def aembed(
    text: str | list[str],
    provider_type: str | None = None,
    fallback: bool = True,
) -> list[list[float]]:
    """Asynchronously generate embeddings using the configured provider."""
    provider = get_provider(provider_type=provider_type, fallback=fallback)
    inc_provider("aembed")
    try:
        return await provider.aembed(text=text)
    except NotImplementedError as exc:  # pragma: no cover - defensive
        raise ProviderError(
            f"Embeddings not supported by provider {provider.__class__.__name__}"
        ) from exc
    except ProviderError:
        # Already the canonical ProviderError; propagate intact
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        if isinstance(exc, ProviderError):
            raise exc
        raise ProviderError(f"Embedding call failed: {exc}") from exc
