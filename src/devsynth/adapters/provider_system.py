"""
Provider System for abstracting LLM providers (OpenAI, LM Studio).

This module implements a unified interface for different LLM providers with
automatic fallback and selection based on configuration.
"""

import asyncio
import json
import logging
import os
import time
from enum import Enum
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import httpx
import requests

from devsynth.config.settings import get_settings
from devsynth.exceptions import ConfigurationError, DevSynthError
from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import inc_provider
from devsynth.security.tls import TLSConfig

# Create a logger for this module
logger = DevSynthLogger(__name__)


class ProviderType(Enum):
    """Enum for supported LLM providers."""

    OPENAI = "openai"
    LMSTUDIO = "lmstudio"


class ProviderError(DevSynthError):
    """Exception raised for provider-related errors."""

    pass


def get_env_or_default(env_var: str, default: str = None) -> Optional[str]:
    """Get environment variable or return default value."""
    return os.environ.get(env_var, default)


def _load_env_file(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load values from a local ``.env`` file into the provided config."""
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return config

    try:
        with open(env_path, "r") as f:
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


@lru_cache(maxsize=1)
def get_provider_config() -> Dict[str, Any]:
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
        provider_type: Optional[str] = None,
        *,
        config: Optional[Dict[str, Any]] = None,
        tls_config: Optional[TLSConfig] = None,
        retry_config: Optional[Dict[str, Any]] = None,
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
        tls_conf = tls_config or _create_tls_config(tls_settings)

        if provider_type is None:
            provider_type = config["default_provider"]

        # Allow ProviderType enum values as well as strings
        if isinstance(provider_type, ProviderType):
            provider_type_value = provider_type.value
        else:
            provider_type_value = str(provider_type)

        try:
            if provider_type_value.lower() == ProviderType.OPENAI.value:
                if not config["openai"]["api_key"]:
                    logger.warning(
                        "OpenAI API key not found; falling back to LM Studio if available"
                    )
                    return ProviderFactory.create_provider(ProviderType.LMSTUDIO.value)
                logger.info("Using OpenAI provider")
                return OpenAIProvider(
                    api_key=config["openai"]["api_key"],
                    model=config["openai"]["model"],
                    base_url=config["openai"]["base_url"],
                    tls_config=tls_conf,
                    retry_config=retry_config or config.get("retry"),
                )
            elif provider_type_value.lower() == ProviderType.LMSTUDIO.value:
                logger.info("Using LM Studio provider")
                return LMStudioProvider(
                    endpoint=config["lmstudio"]["endpoint"],
                    model=config["lmstudio"]["model"],
                    tls_config=tls_conf,
                    retry_config=retry_config or config.get("retry"),
                )
            else:
                logger.warning(
                    f"Unknown provider type '{provider_type}', falling back to OpenAI"
                )
                return ProviderFactory.create_provider(ProviderType.OPENAI.value)
        except Exception as e:
            logger.error(f"Failed to create provider {provider_type}: {e}")
            raise ProviderError(f"Failed to create provider {provider_type}: {e}")


class BaseProvider:
    """Base class for all LLM providers."""

    def __init__(
        self,
        *,
        tls_config: Union[TLSConfig, None] = None,
        retry_config: Optional[Dict[str, Any]] = None,
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
        retryable_exceptions: Tuple[Exception, ...] = (Exception,),
        *,
        should_retry: Optional[Callable[[Exception], bool]] = None,
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
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: Optional[Dict[str, Any]] = None,
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
        context: List[Dict[str, str]],
        *,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a completion given a chat ``context``."""
        raise NotImplementedError("Subclasses must implement complete_with_context()")

    def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
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
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Asynchronous version of :meth:`complete`."""
        raise NotImplementedError("Subclasses must implement acomplete()")

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronous version of :meth:`embed`."""
        raise NotImplementedError("Subclasses must implement aembed()")


class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        base_url: str = "https://api.openai.com/v1",
        tls_config: Union[TLSConfig, None] = None,
        retry_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
            base_url: Base URL for API (default: OpenAI's API)
        """
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
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: Optional[Dict[str, Any]] = None,
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
            frequency_penalty = parameters.get("frequency_penalty")
            presence_penalty = parameters.get("presence_penalty")

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

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                **self.tls_config.as_requests_kwargs(),
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
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Asynchronously generate a completion using the OpenAI API."""

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

            # For async functions, we need to create a wrapper that handles the async nature
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
        context: List[Dict[str, str]],
        *,
        parameters: Optional[Dict[str, Any]] = None,
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

    def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
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

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                **self.tls_config.as_requests_kwargs(),
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

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronously generate embeddings using the OpenAI API."""

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
            logger.error(
                f"OpenAI embedding API error after {max_retries} retries: {last_exception}"
            )
            raise ProviderError(
                f"OpenAI embedding API error after {max_retries} retries: {last_exception}"
            )

        except httpx.HTTPError as e:
            logger.error(f"OpenAI embedding API error: {e}")
            raise ProviderError(f"OpenAI embedding API error: {e}")


class LMStudioProvider(BaseProvider):
    """LM Studio local provider implementation."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:1234",
        model: str = "default",
        tls_config: Union[TLSConfig, None] = None,
        retry_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize LM Studio provider.

        Args:
            endpoint: LM Studio API endpoint
            model: Model name (ignored in LM Studio, uses loaded model)
        """
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
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: Optional[Dict[str, Any]] = None,
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

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                **self.tls_config.as_requests_kwargs(),
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
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Asynchronously generate a completion using LM Studio."""

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
                f"LM Studio endpoint {self.endpoint} is unreachable after {max_retries} "
                f"retries: {last_exception}"
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
        context: List[Dict[str, str]],
        *,
        parameters: Optional[Dict[str, Any]] = None,
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

    def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
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

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                **self.tls_config.as_requests_kwargs(),
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

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
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
                f"LM Studio endpoint {self.endpoint} is unreachable after {max_retries} "
                f"retries: {last_exception}"
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


class FallbackProvider(BaseProvider):
    """Fallback provider that tries multiple providers in sequence."""

    def __init__(
        self,
        providers: Optional[List[BaseProvider]] = None,
        *,
        config: Optional[Dict[str, Any]] = None,
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

        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.provider_factory = provider_factory
        self.providers = providers or self._initialize_providers()

        if not self.providers:
            raise ProviderError("No valid providers available for fallback")

        logger.info(
            "Initialized fallback provider order: %s",
            ", ".join(p.__class__.__name__ for p in self.providers),
        )

    def _initialize_providers(self) -> List[BaseProvider]:
        """Create provider instances based on config order."""
        providers: List[BaseProvider] = []
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
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Try providers sequentially until one succeeds."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    f"Trying completion with provider: {provider.__class__.__name__}"
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
                logger.warning(f"Provider {provider.__class__.__name__} failed: {exc}")
                last_error = exc

        raise ProviderError(
            f"All providers failed for completion. Last error: {last_error}"
        )

    async def acomplete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Asynchronously try providers until one succeeds."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    f"Trying async completion with provider: {provider.__class__.__name__}"
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
                logger.warning(f"Provider {provider.__class__.__name__} failed: {exc}")
                last_error = exc

        raise ProviderError(
            f"All providers failed for completion. Last error: {last_error}"
        )

    def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Try providers sequentially to generate embeddings."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    f"Trying embeddings with provider: {provider.__class__.__name__}"
                )
                return self._call_sync(provider, "embed", text=text)
            except Exception as exc:
                logger.warning(
                    f"Provider {provider.__class__.__name__} failed for embeddings: {exc}"
                )
                last_error = exc

        raise ProviderError(
            f"All providers failed for embeddings. Last error: {last_error}"
        )

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronously try providers for embeddings."""
        last_error = None
        providers = self.providers
        if not self.fallback_config.get("enabled", True) and self.providers:
            providers = [self.providers[0]]

        for provider in providers:
            try:
                logger.info(
                    f"Trying async embeddings with provider: {provider.__class__.__name__}"
                )
                return await self._call_async(provider, "aembed", text=text)
            except Exception as exc:
                logger.warning(
                    f"Provider {provider.__class__.__name__} failed for embeddings: {exc}"
                )
                last_error = exc

        raise ProviderError(
            f"All providers failed for embeddings. Last error: {last_error}"
        )


# Simplified API for common usage
def get_provider(
    provider_type: Optional[str] = None, fallback: bool = False
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
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    provider_type: Optional[str] = None,
    fallback: bool = True,
    *,
    parameters: Optional[Dict[str, Any]] = None,
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
    text: Union[str, List[str]],
    provider_type: Optional[str] = None,
    fallback: bool = True,
) -> List[List[float]]:
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
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        raise ProviderError(f"Embedding call failed: {exc}") from exc


async def acomplete(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    provider_type: Optional[str] = None,
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
    text: Union[str, List[str]],
    provider_type: Optional[str] = None,
    fallback: bool = True,
) -> List[List[float]]:
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
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        raise ProviderError(f"Embedding call failed: {exc}") from exc
