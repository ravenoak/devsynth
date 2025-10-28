import concurrent.futures
import inspect
import os
from typing import Any, Dict, List, Optional

import httpx

# Import get_llm_settings lazily to avoid import issues during testing
from devsynth.core.config_loader import load_config

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...application.utils.token_tracker import TokenTracker
from ...domain.interfaces.llm import LLMProvider, LLMProviderFactory
from ...fallback import CircuitBreaker, retry_with_exponential_backoff
from ...metrics import inc_provider

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class ValidationError(DevSynthError):
    """Exception raised when validation fails."""

    pass


class BaseLLMProvider:
    """Base class for LLM providers."""

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

    def generate(self, prompt: str, parameters: dict[str, Any] = None) -> str:
        """Generate text from a prompt."""
        raise NotImplementedError("Subclasses must implement this method")

    def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] = None,
    ) -> str:
        """Generate text from a prompt with conversation context."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_embedding(self, text: str) -> list[float]:
        """Get an embedding vector for the given text."""
        raise NotImplementedError("Subclasses must implement this method")


class AnthropicConnectionError(DevSynthError):
    """Exception raised when there's an issue connecting to Anthropic."""


class AnthropicModelError(DevSynthError):
    """Exception raised for errors returned by Anthropic's API."""


class AnthropicAuthenticationError(DevSynthError):
    """Exception raised when Anthropic authentication fails."""

    pass


class AnthropicConfigurationError(DevSynthError):
    """Exception raised when Anthropic configuration is invalid."""

    pass


class AnthropicTokenLimitError(DevSynthError):
    """Exception raised when Anthropic token limit is exceeded."""

    pass


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider implementation."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)

        self.api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        self.model = self.config.get("model", "claude-2")
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.temperature = self.config.get("temperature", 0.7)
        self.api_base = self.config.get("api_base", "https://api.anthropic.com")
        self.timeout = self.config.get("timeout", 60)
        self.max_retries = self.config.get("max_retries", 3)
        self.embedding_model = self.config.get("embedding_model", "claude-3-embed")

        if not self.api_key:
            raise AnthropicAuthenticationError("Anthropic API key is required")

        # Validate configuration parameters
        self._validate_configuration()

        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Initialize resilience patterns
        self.max_retries = self.config.get("max_retries", 3)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60),
        )

        # Initialize token tracker
        self.token_tracker = TokenTracker()

    def _validate_configuration(self) -> None:
        """Validate Anthropic provider configuration parameters."""
        # Parameter range validation
        if not 0.0 <= self.temperature <= 2.0:
            raise AnthropicConfigurationError(
                f"Anthropic temperature must be between 0.0 and 2.0, got {self.temperature}"
            )

        if self.max_tokens <= 0:
            raise AnthropicConfigurationError(
                f"Anthropic max_tokens must be positive, got {self.max_tokens}"
            )

        if self.timeout <= 0:
            raise AnthropicConfigurationError(
                f"Anthropic timeout must be positive, got {self.timeout}"
            )

        if self.max_retries < 0:
            raise AnthropicConfigurationError(
                f"Anthropic max_retries must be non-negative, got {self.max_retries}"
            )

    def _validate_runtime_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate runtime parameters for API calls."""
        # Validate temperature if provided
        if "temperature" in parameters:
            temp = parameters["temperature"]
            if not isinstance(temp, (int, float)) or not 0.0 <= temp <= 2.0:
                raise AnthropicConfigurationError(
                    f"Anthropic temperature must be a number between 0.0 and 2.0, got {temp}"
                )

        # Validate max_tokens if provided
        if "max_tokens" in parameters:
            max_tokens = parameters["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                raise AnthropicConfigurationError(
                    f"Anthropic max_tokens must be a positive integer, got {max_tokens}"
                )

        # Validate top_p if provided
        if "top_p" in parameters:
            top_p = parameters["top_p"]
            if top_p is not None and (
                not isinstance(top_p, (int, float)) or not 0.0 <= top_p <= 1.0
            ):
                raise AnthropicConfigurationError(
                    f"Anthropic top_p must be a number between 0.0 and 1.0, got {top_p}"
                )

    def _should_retry(self, exc: Exception) -> bool:
        """Return ``True`` if the exception should trigger a retry."""
        # Don't retry on client errors (4xx) except rate limits (429)
        if hasattr(exc, "response") and exc.response is not None:
            status_code = exc.response.status_code
            if 400 <= status_code < 500 and status_code != 429:
                return False
        return True

    def _on_retry(self, exc: Exception, attempt: int, delay: float) -> None:
        """Emit telemetry when a retry occurs."""
        logger.warning(
            "Retrying AnthropicProvider due to %s (attempt %d, delay %.2fs)",
            exc,
            attempt,
            delay,
        )
        inc_provider("retry")

    def _execute_with_resilience(self, func, *args, **kwargs):
        """Execute a function with retry and circuit breaker protection."""

        @retry_with_exponential_backoff(
            max_retries=self.max_retries,
            should_retry=self._should_retry,
            on_retry=self._on_retry,
        )
        def _wrapped():
            # Execute in a worker with a strict timeout to avoid hangs
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.circuit_breaker.call, func, *args, **kwargs
                )
                return future.result(timeout=self.timeout)

        return _wrapped()

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.api_base}{endpoint}"
        try:
            response = httpx.post(
                url, headers=self.headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"Anthropic API error: {e.response.text}"
            logger.error(error_msg)
            raise AnthropicModelError(error_msg) from e
        except httpx.RequestError as e:
            error_msg = f"Anthropic connection error: {str(e)}"
            logger.error(error_msg)
            raise AnthropicConnectionError(error_msg) from e

    def generate(self, prompt: str, parameters: dict[str, Any] | None = None) -> str:
        """Generate text from a prompt using Anthropic."""

        # Ensure the prompt doesn't exceed token limits
        self.token_tracker.ensure_token_limit(prompt, self.max_tokens)

        # Validate runtime parameters
        self._validate_runtime_parameters(parameters or {})

        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if parameters:
            params.update(parameters)

        payload = {
            "model": params["model"],
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "messages": [{"role": "user", "content": prompt}],
        }

        def _api_call():
            data = self._post("/v1/messages", payload)

            if "content" in data and isinstance(data["content"], list):
                return "".join(part.get("text", "") for part in data["content"])
            if "completion" in data:
                return data["completion"]
            raise AnthropicModelError("Invalid response from Anthropic")

        try:
            return self._execute_with_resilience(_api_call)
        except AnthropicTokenLimitError:
            raise  # Re-raise token limit errors as-is
        except AnthropicConnectionError:
            raise  # Re-raise connection errors as-is
        except Exception as e:
            error_msg = f"Anthropic API error: {str(e)}. Check your API key and model configuration."
            logger.error(error_msg)
            raise AnthropicConnectionError(error_msg)

    def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Generate text from a prompt with conversation context using Anthropic."""

        messages = context.copy()
        messages.append({"role": "user", "content": prompt})

        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if parameters:
            params.update(parameters)

        payload = {
            "model": params["model"],
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"],
            "messages": messages,
        }

        data = self._post("/v1/messages", payload)

        if "content" in data and isinstance(data["content"], list):
            return "".join(part.get("text", "") for part in data["content"])
        if "completion" in data:
            return data["completion"]
        raise AnthropicModelError("Invalid response from Anthropic")

    def get_embedding(self, text: str) -> list[float]:
        """Get an embedding vector for the given text using Anthropic."""

        payload = {
            "model": self.embedding_model,
            "input": text,
        }

        data = self._post("/v1/embeddings", payload)

        if "embedding" in data:
            return data["embedding"]
        if "data" in data and data["data"]:
            return data["data"][0]["embedding"]
        raise AnthropicModelError("Invalid embedding response from Anthropic")


class SimpleLLMProviderFactory(LLMProviderFactory):
    """Simple implementation of LLMProviderFactory with lazy provider resolution.

    The registry accepts either:
    - a provider class type; or
    - a callable taking a config dict and returning either an instance or a class.

    This design ensures that test-time stubs applied to provider modules are respected,
    aligning with tasks in docs/tasks.md (13, 31, 32).
    """

    def __init__(self):
        self.provider_types: dict[str, Any] = {}

    def create_provider(
        self, provider_type: str, config: dict[str, Any] = None
    ) -> LLMProvider:
        """Create an LLM provider of the specified type."""
        if provider_type not in self.provider_types:
            if provider_type == "lmstudio":
                raise ValidationError(
                    "LMStudio provider is unavailable. Install the 'lmstudio' package to enable this provider."
                )
            raise ValidationError(f"Unknown provider type: {provider_type}")

        entry = self.provider_types[provider_type]
        cfg = config or {}
        # If entry is callable, invoke it. It may return an instance or a class.
        if callable(entry):
            obj = entry(cfg)
            # If the callable returned a class, instantiate it; otherwise, assume it's an instance and return it.
            if inspect.isclass(obj):  # type: ignore[arg-type]
                return obj(cfg)  # type: ignore[misc]
            return obj  # type: ignore[return-value]
        # Otherwise, assume it's a class type
        provider_class = entry
        return provider_class(cfg)  # type: ignore[call-arg]

    def register_provider_type(
        self, provider_type: str, provider_class_or_factory: Any
    ) -> None:
        """Register a new provider type or factory."""
        self.provider_types[provider_type] = provider_class_or_factory


# Provider selection logic
def get_llm_provider(config: dict[str, Any] | None = None) -> LLMProvider:
    """Return an LLM provider based on configuration.

    Safe-by-default policy:
    - If offline_mode is true, select 'offline'.
    - If DEVSYNTH_OFFLINE=true (env), force 'offline'.
    - If a provider is explicitly configured, use it but validate required credentials.
    - If 'lmstudio' is requested but not marked available via DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE, fall back to 'offline'.
    - Otherwise, default to 'offline'.
    """

    cfg = config or load_config().as_dict()
    offline = cfg.get("offline_mode", False)

    # Honor global offline kill-switch
    offline_env = os.getenv("DEVSYNTH_OFFLINE", "").lower() in {"1", "true", "yes"}
    if offline_env:
        offline = True

    # Tests default: require explicit opt-in to use real providers
    allow_providers = os.getenv("DEVSYNTH_TEST_ALLOW_PROVIDERS", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    if not allow_providers:
        offline = True

    from devsynth.config import get_llm_settings

    llm_cfg = get_llm_settings()
    if "offline_provider" in cfg:
        llm_cfg["offline_provider"] = cfg["offline_provider"]

    # Determine provider safely
    if offline:
        provider_type = "offline"
    else:
        provider_type = llm_cfg.get("provider") or "offline"

    # Enforce LM Studio availability flag
    pt_lower = str(provider_type).lower()
    if pt_lower == "lmstudio":
        lmstudio_available = os.getenv(
            "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false"
        ).lower() in {"1", "true", "yes"}
        if not lmstudio_available:
            provider_type = "offline"
            pt_lower = "offline"

    # Validate credentials if a remote provider is explicitly requested
    if pt_lower == "openai":
        api_key = llm_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValidationError(
                "OpenAI provider requested but no OPENAI_API_KEY configured"
            )
    elif pt_lower == "anthropic":
        api_key = llm_cfg.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValidationError(
                "Anthropic provider requested but no ANTHROPIC_API_KEY configured"
            )

    return factory.create_provider(provider_type, llm_cfg)


# Import providers at the end to avoid circular imports
lmstudio_requested = os.getenv(
    "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false"
).lower() in {"1", "true", "yes"}
if lmstudio_requested:  # pragma: no cover - optional dependency
    try:
        from .lmstudio_provider import LMStudioProvider
    except ImportError as exc:  # pragma: no cover - fallback path
        LMStudioProvider = None
        logger.warning("LMStudioProvider not available: %s", exc)
else:  # pragma: no cover - optional dependency
    LMStudioProvider = None

# Try to import OpenRouter provider if available
try:
    from .openrouter_provider import OpenRouterProvider
except ImportError as exc:  # pragma: no cover - optional dependency
    OpenRouterProvider = None
    logger.warning("OpenRouterProvider not available: %s", exc)
# Avoid importing provider modules at import time to keep this module inert.
# Only import within factory callables to prevent side effects during test collection.
from . import offline_provider as _offline_provider

# Re-export only the offline provider (safe/local and side-effect free)
OfflineProvider = _offline_provider.OfflineProvider

# Provide a patchable OpenAIProvider symbol for tests; lazily resolved if available.
try:  # pragma: no cover - symbol exposure for patching in tests
    from .openai_provider import OpenAIProvider as _OpenAIProvider  # type: ignore

    OpenAIProvider = _OpenAIProvider  # type: ignore
except Exception:  # pragma: no cover - fallback sentinel

    class OpenAIProvider:  # type: ignore
        """Sentinel to allow patching in tests when openai not installed."""

        pass


# Provide LocalProvider symbol for explicit imports and registration in provider_factory
try:  # pragma: no cover - symbol exposure for imports/registration
    from .local_provider import LocalProvider as _LocalProvider  # type: ignore

    LocalProvider = _LocalProvider  # type: ignore
except Exception:  # pragma: no cover - fallback sentinel

    class LocalProvider:  # type: ignore
        """Sentinel LocalProvider; real implementation resides in local_provider.py."""

        pass


# Create factory instance
factory = SimpleLLMProviderFactory()

# Register providers using callables to resolve classes at call time (lazy import)
factory.register_provider_type("anthropic", lambda cfg: AnthropicProvider(cfg))
if LMStudioProvider is not None:
    # Keep direct reference for optional provider; requires explicit opt-in via env flag
    factory.register_provider_type("lmstudio", lambda cfg: LMStudioProvider(cfg))

# Lazy import inside the lambda to avoid import-time side effects
factory.register_provider_type(
    "openai",
    lambda cfg: (
        __import__(
            "devsynth.application.llm.openai_provider", fromlist=["OpenAIProvider"]
        ).OpenAIProvider
    )(cfg),
)
factory.register_provider_type(
    "local",
    lambda cfg: (
        __import__(
            "devsynth.application.llm.local_provider", fromlist=["LocalProvider"]
        ).LocalProvider
    )(cfg),
)
factory.register_provider_type(
    "offline", lambda cfg: _offline_provider.OfflineProvider(cfg)
)
if OpenRouterProvider is not None:
    # Keep direct reference for optional provider; requires explicit opt-in via API key
    factory.register_provider_type("openrouter", lambda cfg: OpenRouterProvider(cfg))
