"""
LM Studio Provider implementation for DevSynth.
This provider connects to a local LM Studio server running on localhost.
"""

import concurrent.futures
import os
from typing import Any, Dict, List
from urllib.parse import urlparse

from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import inc_provider

# Import get_llm_settings lazily to avoid import issues during testing
from ..utils.token_tracker import TokenLimitExceededError, TokenTracker
from .providers import BaseLLMProvider

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


def _require_lmstudio():
    """Lazy import for the optional lmstudio package.

    Returns the imported module or raises a clear DevSynthError with guidance.
    """
    try:  # pragma: no cover - optional dependency
        import lmstudio as _lmstudio  # type: ignore

        return _lmstudio
    except ImportError as e:  # pragma: no cover - if lmstudio is missing tests skip
        raise DevSynthError(
            "LMStudio support requires the 'lmstudio' package. Install it with 'pip install lmstudio' or use 'poetry install --extras \"llm\"'."
        ) from e


class _AttrForwarder:
    """An attribute object that forwards callable access to the real lmstudio attribute.

    This lives on the proxy instance's __dict__ so unittest.mock.patch can replace it.
    """

    def __init__(self, proxy: "_LMStudioProxy", attr: str) -> None:
        self._proxy = proxy
        self._attr = attr

    def __call__(self, *args, **kwargs):  # pragma: no cover - thin forwarder
        real = self._proxy._ensure()
        return getattr(real, self._attr)(*args, **kwargs)


class _NamespaceForwarder:
    """A namespace forwarder that exposes attributes of lmstudio.<name> lazily.

    This object is placed directly on the proxy instance (e.g., proxy.sync_api),
    so unittest.mock.patch can target attributes like
    devsynth.application.llm.lmstudio_provider.lmstudio.sync_api.list_downloaded_models
    without importing the optional dependency at module import time.
    """

    def __init__(self, proxy: "_LMStudioProxy", ns_name: str) -> None:
        self._proxy = proxy
        self._ns_name = ns_name

    def __getattr__(self, item: str):  # pragma: no cover - thin delegator
        real = self._proxy._ensure()
        namespace = getattr(real, self._ns_name)
        return getattr(namespace, item)

    # Provide common attributes so unittest.mock.patch can replace them without
    # needing the underlying optional dependency to be present.
    def list_downloaded_models(self, *args, **kwargs):  # pragma: no cover - bridge
        real = self._proxy._ensure()
        namespace = getattr(real, self._ns_name)
        return namespace.list_downloaded_models(*args, **kwargs)

    def configure_default_client(self, *args, **kwargs):  # pragma: no cover - bridge
        real = self._proxy._ensure()
        namespace = getattr(real, self._ns_name)
        return namespace.configure_default_client(*args, **kwargs)


class _LMStudioProxy:
    """Proxy object that defers importing lmstudio until attribute access.

    This enables tests to patch devsynth.application.llm.lmstudio_provider.lmstudio.llm
    without importing the optional dependency at module import time.
    """

    def __init__(self) -> None:
        self._real: Any | None = None
        # Place forwarders in instance __dict__ so unittest.mock.patch can replace them.
        self.llm = _AttrForwarder(self, "llm")
        self.embedding_model = _AttrForwarder(self, "embedding_model")
        # Expose a namespace forwarder for sync_api so tests can patch its attributes
        # even if the optional dependency is not installed in this environment.
        self.sync_api = _NamespaceForwarder(self, "sync_api")

    def _ensure(self) -> Any:
        if self._real is None:
            self._real = _require_lmstudio()
        return self._real

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - simple delegator
        real = self._ensure()
        return getattr(real, name)


# Module-level proxy to satisfy patch paths in tests:
#   patch("devsynth.application.llm.lmstudio_provider.lmstudio.llm")
# This keeps optional import semantics while allowing attribute patching.
lmstudio = _LMStudioProxy()


class LMStudioConnectionError(DevSynthError):
    """Exception raised when there's an issue connecting to LM Studio."""

    pass


class LMStudioModelError(DevSynthError):
    """Exception raised when there's an issue with LM Studio models."""

    pass


class LMStudioAuthenticationError(DevSynthError):
    """Exception raised when LM Studio authentication fails."""

    pass


class LMStudioConfigurationError(DevSynthError):
    """Exception raised when LM Studio configuration is invalid."""

    pass


class LMStudioTokenLimitError(DevSynthError):
    """Exception raised when LM Studio token limit is exceeded."""

    pass


class LMStudioProvider(BaseLLMProvider):
    """LM Studio LLM provider implementation.

    Adds a lightweight health check and bounded handshake retry/backoff per docs/tasks.md Task 9/18.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the LM Studio provider.

        Args:
            config: Configuration dictionary with the following keys:
                - api_base: Base URL for the LM Studio API (default: from config)
                - model: Model name to use (default: from config or auto-selected)
                - max_tokens: Maximum tokens for responses (default: from config)
                - temperature: Temperature for generation (default: from config)
                - auto_select_model: Whether to automatically select a model (default: from config)
        """
        # Get default settings from configuration
        from ...config.settings import get_llm_settings

        default_settings = get_llm_settings()

        # Initialize with default settings, overridden by provided config
        merged_config = {**default_settings, **(config or {})}
        super().__init__(merged_config)

        # Set instance variables from config
        endpoint_default = os.environ.get("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")
        self.api_base = self.config.get("api_base") or endpoint_default
        self.max_tokens = self.config.get("max_tokens")
        self.temperature = self.config.get("temperature")
        self.timeout = self.config.get("timeout") or 60
        parsed = urlparse(self.api_base)
        self.api_host = parsed.netloc or parsed.path.split("/")[0]
        # Use module-level proxy to allow tests to patch lmstudio.llm
        self._lmstudio = lmstudio
        # Only configure the client when LM Studio resource is explicitly enabled
        resource_enabled = (
            os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false").lower()
            == "true"
        )
        if resource_enabled:
            try:
                self._lmstudio.sync_api.configure_default_client(self.api_host)
            except Exception as e:  # noqa: BLE001
                logger.warning("LM Studio default client configuration failed: %s", e)
        else:
            logger.info(
                "LM Studio resource disabled; skipping default client configuration"
            )
        # Retries: env override with default 1 (idempotent minimal retries)
        retries_env = os.environ.get("DEVSYNTH_LMSTUDIO_RETRIES")
        try:
            self.max_retries = (
                int(retries_env)
                if retries_env is not None
                else int(self.config.get("max_retries", 1))
            )
        except (TypeError, ValueError):
            self.max_retries = 1
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60),
        )
        # Deterministic per-call timeout (seconds) with env default via LM_STUDIO_HTTP_TIMEOUT (Task 70)
        timeout_env = os.environ.get("LM_STUDIO_HTTP_TIMEOUT")
        try:
            self.call_timeout = (
                float(timeout_env)
                if timeout_env is not None
                else float(
                    self.config.get("call_timeout", 30)
                )  # Increased default timeout
            )
        except (TypeError, ValueError):
            self.call_timeout = 30.0  # Increased default timeout
        self.token_tracker = TokenTracker()

        # Validate configuration parameters
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate LM Studio provider configuration parameters."""
        # Parameter range validation
        if self.temperature is not None and not 0.0 <= self.temperature <= 2.0:
            raise LMStudioConfigurationError(
                f"LM Studio temperature must be between 0.0 and 2.0, got {self.temperature}"
            )

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise LMStudioConfigurationError(
                f"LM Studio max_tokens must be positive, got {self.max_tokens}"
            )

        if self.timeout is not None and self.timeout <= 0:
            raise LMStudioConfigurationError(
                f"LM Studio timeout must be positive, got {self.timeout}"
            )

        if self.max_retries < 0:
            raise LMStudioConfigurationError(
                f"LM Studio max_retries must be non-negative, got {self.max_retries}"
            )

        # Auto-select model if not specified
        auto_select = self.config.get("auto_select_model")
        specified_model = self.config.get("model")

        # Try specified model first, fallback to auto-selection if it fails
        model_selected = False

        if specified_model:
            try:
                # Test if the specified model is available
                available_models = self.list_available_models()
                if any(model["id"] == specified_model for model in available_models):
                    self.model = specified_model
                    logger.info(f"Using specified model: {self.model}")
                    model_selected = True
                else:
                    logger.warning(
                        f"Specified model '{specified_model}' not available, falling back to auto-selection"
                    )
            except (LMStudioConnectionError, Exception) as e:
                logger.warning(
                    f"Could not verify specified model '{specified_model}': {e}, falling back to auto-selection"
                )

        if not model_selected and auto_select:
            # Try to use a known working model if auto-selection fails
            try:
                available_models = self.list_available_models()
                if available_models:
                    # Look for a Qwen model first, then any available model
                    for model in available_models:
                        model_id = model["id"]
                        if "qwen" in model_id.lower():
                            self.model = model_id
                            logger.info(f"Auto-selected Qwen model: {self.model}")
                            break
                    else:
                        # Use first available model if no Qwen model found
                        self.model = available_models[0]["id"]
                        logger.info(f"Auto-selected model: {self.model}")
                else:
                    self.model = "qwen/qwen3-4b-2507"  # Fallback to known working model
                    logger.warning(
                        f"No models available from LM Studio. Using fallback: {self.model}"
                    )
            except LMStudioConnectionError as e:
                self.model = "qwen/qwen3-4b-2507"  # Fallback to known working model
                logger.warning(
                    f"Could not connect to LM Studio: {str(e)}. Using fallback: {self.model}"
                )
        else:
            self.model = "qwen/qwen3-4b-2507"  # Use known working model as default
            logger.info(f"Using default model: {self.model}")

    def health_check(self) -> bool:
        """Lightweight health check to the LM Studio endpoint.

        Performs a GET to /api/v0/models via HTTP request. If DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE
        is true but the endpoint is unreachable, tests may skip quickly with a clear reason.
        The total time spent in retries is bounded (<= 5 seconds).
        """
        # If resource flag is not enabled, we consider health as not applicable/false
        resource_enabled = (
            os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false").lower()
            == "true"
        )
        if not resource_enabled:
            return False

        # Compute bounded retries/delay to stay under 10s total (conservative for shared host)
        max_total_seconds = 10.0
        # Default to at most 3 retries with small backoff, but cap by max_total_seconds using call_timeout as base
        attempt = 0
        delay = min(0.5, self.call_timeout / 4)
        total = 0.0
        last_exc: Exception | None = None
        while total <= max_total_seconds and attempt < max(1, self.max_retries):
            attempt += 1
            try:
                # Use HTTP request to /api/v0/models endpoint
                try:
                    self._lmstudio.sync_api.configure_default_client(self.api_host)
                except Exception as cfg_err:  # noqa: BLE001
                    # Don't fail health check early on configure failure; proceed to list models
                    logger.debug(
                        "LM Studio health_check configure_default_client failed (ignored): %s",
                        cfg_err,
                    )
                # Use native API for health check (5s timeout for quick health checks)
                import requests

                response = requests.get(f"{self.api_base}/api/v0/models", timeout=5)
                models_data = response.json()
                models = [
                    m for m in models_data.get("data", []) if m.get("type") == "llm"
                ]
                _ = len(models)
                return True
            except Exception as e:  # noqa: BLE001
                last_exc = e
                logger.debug("LM Studio health_check attempt %d failed: %s", attempt, e)
                # Sleep bounded by remaining budget
                if total + delay > max_total_seconds:
                    break
                import time

                time.sleep(delay)
                total += delay
                delay = min(max_total_seconds - total, delay * 2)
        if last_exc:
            logger.info("LM Studio health_check failed within budget: %s", last_exc)
        return False

    def _should_retry(self, exc: Exception) -> bool:
        """Return ``True`` if the exception should trigger a retry."""
        status = getattr(exc, "status_code", None)
        if status is not None and 400 <= int(status) < 500 and int(status) != 429:
            return False
        if isinstance(exc, LMStudioModelError):
            return False
        return True

    def _on_retry(self, exc: Exception, attempt: int, delay: float) -> None:
        """Emit telemetry when a retry occurs."""
        logger.warning(
            "Retrying LMStudioProvider due to %s (attempt %d, delay %.2fs)",
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
                return future.result(timeout=self.call_timeout)

        return _wrapped()

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List available models from LM Studio.

        Returns:
            A list of available models with their details

        Raises:
            LMStudioConnectionError: If there's an issue connecting to LM Studio
        """
        try:
            # Use the native LM Studio API instead of the OpenAI-compatible one
            import requests

            response = requests.get(f"{self.api_base}/api/v0/models", timeout=30)
            response.raise_for_status()

            models_data = response.json()
            models = models_data.get("data", [])

            # Filter for LLM models only and format correctly
            llm_models = [
                {"id": m["id"], "name": f"{m.get('publisher', 'Unknown')}/{m['id']}"}
                for m in models
                if m.get("type") == "llm"
            ]

            logger.info(f"Found {len(llm_models)} LLM models from LM Studio")
            return llm_models

        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to connect to LM Studio: {str(e)}"
            logger.error(error_msg)
            raise LMStudioConnectionError(error_msg)

    def get_model_details(self, model_id: str) -> Dict[str, Any]:
        """Get details for a specific model from LM Studio.

        Args:
            model_id: The ID of the model to get details for

        Returns:
            The model details

        Raises:
            LMStudioConnectionError: If there's an issue connecting to LM Studio
            LMStudioModelError: If the model is not found
        """
        try:
            models = self.list_available_models()
            for model in models:
                if model["id"] == model_id:
                    return model

            error_msg = f"Model not found: {model_id}"
            logger.error(error_msg)
            raise LMStudioModelError(error_msg)
        except LMStudioConnectionError as e:
            # Re-raise the connection error
            raise e

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt using LM Studio.

        Args:
            prompt: The prompt to generate text from
            parameters: Additional parameters for the generation

        Returns:
            The generated text

        Raises:
            LMStudioConnectionError: If there's an issue connecting to LM Studio
            LMStudioModelError: If there's an issue with the model or response
            TokenLimitExceededError: If the prompt exceeds the token limit
        """
        # Ensure the prompt doesn't exceed token limits
        self.token_tracker.ensure_token_limit(prompt, self.max_tokens)

        params = {
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
        }
        if parameters:
            params.update(parameters)

        try:
            result = self._execute_with_resilience(
                self._lmstudio.llm(self.model).complete,
                prompt,
                config=params,
            )
            content = getattr(result, "content", None)
            if isinstance(content, str) and content:
                return content
            raise LMStudioModelError("Invalid response from LM Studio")
        except LMStudioModelError:
            raise
        except LMStudioTokenLimitError:
            raise  # Re-raise token limit errors as-is
        except LMStudioConnectionError:
            raise  # Re-raise connection errors as-is
        except Exception as e:  # noqa: BLE001
            error_msg = f"LM Studio API error: {str(e)}. Check that LM Studio is running and accessible."
            logger.error(error_msg)
            raise LMStudioConnectionError(error_msg)

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> str:
        """Generate text from a prompt with conversation context using LM Studio.

        Args:
            prompt: The prompt to generate text from
            context: List of conversation messages in the format [{"role": "...", "content": "..."}]
            parameters: Additional parameters for the generation

        Returns:
            The generated text

        Raises:
            LMStudioConnectionError: If there's an issue connecting to LM Studio
            LMStudioModelError: If there's an issue with the model or response
            TokenLimitExceededError: If the conversation exceeds the token limit
        """
        # Create a copy of the context and add the new prompt
        messages = context.copy()
        messages.append({"role": "user", "content": prompt})

        # Check token count and prune if necessary
        token_count = self.token_tracker.count_conversation_tokens(messages)
        if token_count > self.max_tokens:
            messages = self.token_tracker.prune_conversation(messages, self.max_tokens)

        params = {
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
        }
        if parameters:
            params.update(parameters)

        try:
            result = self._execute_with_resilience(
                self._lmstudio.llm(self.model).respond,
                {"messages": messages},
                config=params,
            )
            if hasattr(result, "content"):
                return result.content
            raise LMStudioModelError("Invalid response from LM Studio")
        except LMStudioModelError:
            raise
        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to connect to LM Studio: {str(e)}"
            logger.error(error_msg)
            raise LMStudioConnectionError(error_msg)

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text using LM Studio.

        Args:
            text: The text to get an embedding for

        Returns:
            The embedding vector as a list of floats

        Raises:
            LMStudioConnectionError: If there's an issue connecting to LM Studio
            LMStudioModelError: If there's an issue with the model or response
        """
        try:
            result = self._execute_with_resilience(
                self._lmstudio.embedding_model(self.model).embed,
                text,
            )
            if isinstance(result, list) and result:
                return result if isinstance(result[0], float) else result[0]
            raise LMStudioModelError("Invalid embedding response")
        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to connect to LM Studio: {str(e)}"
            logger.error(error_msg)
            raise LMStudioConnectionError(error_msg)
