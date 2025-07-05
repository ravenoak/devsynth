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
from typing import Any, Callable, Dict, List, Optional, Union

import httpx
import requests

from devsynth.config.settings import get_settings
from devsynth.exceptions import DevSynthError
from devsynth.fallback import retry_with_exponential_backoff
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import inc_provider
from devsynth.security.tls import TLSConfig

# Create a logger for this module
logger = DevSynthLogger(__name__)


class ProviderType(Enum):
    """Enum for supported LLM providers."""

    OPENAI = "openai"
    LM_STUDIO = "lm_studio"


class ProviderError(DevSynthError):
    """Exception raised for provider-related errors."""

    pass


def get_env_or_default(env_var: str, default: str = None) -> Optional[str]:
    """Get environment variable or return default value."""
    return os.environ.get(env_var, default)


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
        "lm_studio": {
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
        },
        "fallback": {
            "enabled": getattr(settings, "provider_fallback_enabled", True),
            "order": getattr(settings, "provider_fallback_order", "openai,lm_studio").split(","),
        },
        "circuit_breaker": {
            "enabled": getattr(settings, "provider_circuit_breaker_enabled", True),
            "failure_threshold": getattr(settings, "provider_failure_threshold", 5),
            "recovery_timeout": getattr(settings, "provider_recovery_timeout", 60.0),
        },
    }

    # Check for .env file and load if exists
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        os.environ[key] = value

                        # Update config based on loaded .env values
                        if key == "OPENAI_API_KEY":
                            config["openai"]["api_key"] = value
                        elif key == "OPENAI_MODEL":
                            config["openai"]["model"] = value
                        elif key == "LM_STUDIO_ENDPOINT":
                            config["lm_studio"]["endpoint"] = value
                        elif key == "LM_STUDIO_MODEL":
                            config["lm_studio"]["model"] = value
                        elif key == "DEVSYNTH_PROVIDER":
                            config["default_provider"] = value
        except Exception as e:
            logger.warning(f"Error loading .env file: {e}")

    return config


class ProviderFactory:
    """Factory class for creating provider instances."""

    @staticmethod
    def create_provider(provider_type: Optional[str] = None) -> "BaseProvider":
        """
        Create a provider instance based on the specified type or config.

        Args:
            provider_type: Optional provider type, defaults to config value

        Returns:
            BaseProvider: A provider instance

        Raises:
            ProviderError: If provider creation fails
        """
        config = get_provider_config()
        tls_settings = get_settings()
        tls_conf = TLSConfig(
            verify=getattr(tls_settings, "tls_verify", True),
            cert_file=getattr(tls_settings, "tls_cert_file", None),
            key_file=getattr(tls_settings, "tls_key_file", None),
            ca_file=getattr(tls_settings, "tls_ca_file", None),
        )

        if provider_type is None:
            provider_type = config["default_provider"]

        try:
            if provider_type.lower() == ProviderType.OPENAI.value:
                if not config["openai"]["api_key"]:
                    logger.warning(
                        "OpenAI API key not found; falling back to LM Studio if available"
                    )
                    return ProviderFactory.create_provider(ProviderType.LM_STUDIO.value)
                logger.info("Using OpenAI provider")
                return OpenAIProvider(
                    api_key=config["openai"]["api_key"],
                    model=config["openai"]["model"],
                    base_url=config["openai"]["base_url"],
                    tls_config=tls_conf,
                )
            elif provider_type.lower() == ProviderType.LM_STUDIO.value:
                logger.info("Using LM Studio provider")
                return LMStudioProvider(
                    endpoint=config["lm_studio"]["endpoint"],
                    model=config["lm_studio"]["model"],
                    tls_config=tls_conf,
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

    def __init__(self, tls_config: TLSConfig | None = None, **kwargs):
        """Initialize the provider with implementation-specific kwargs."""
        self.kwargs = kwargs
        self.tls_config = tls_config or TLSConfig()

        # Get retry configuration
        config = get_provider_config()
        self.retry_config = config.get("retry", {
            "max_retries": 3,
            "initial_delay": 1.0,
            "exponential_base": 2.0,
            "max_delay": 60.0,
            "jitter": True,
        })

    def get_retry_decorator(self, retryable_exceptions=(Exception,)):
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
            retryable_exceptions=retryable_exceptions,
        )

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
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
        tls_config: TLSConfig | None = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
            base_url: Base URL for API (default: OpenAI's API)
        """
        super().__init__(
            tls_config=tls_config, api_key=api_key, model=model, base_url=base_url
        )
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Get retry configuration
        config = get_provider_config()
        self.retry_config = config.get("retry", {
            "max_retries": 3,
            "initial_delay": 1.0,
            "exponential_base": 2.0,
            "max_delay": 60.0,
            "jitter": True,
        })

    def _get_retry_config(self):
        """Get the retry configuration for OpenAI API calls."""
        return {
            "max_retries": self.retry_config["max_retries"],
            "initial_delay": self.retry_config["initial_delay"],
            "exponential_base": self.retry_config["exponential_base"],
            "max_delay": self.retry_config["max_delay"],
            "jitter": self.retry_config["jitter"],
        }

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
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
        def _api_call():
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
                retryable_exceptions=(requests.exceptions.RequestException,)
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
                    retryable_exceptions=(httpx.HTTPError,)
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
                    delay = min(initial_delay * (exponential_base ** (retry_count - 1)), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            logger.error(f"OpenAI API error after {max_retries} retries: {last_exception}")
            raise ProviderError(f"OpenAI API error after {max_retries} retries: {last_exception}")

        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ProviderError(f"OpenAI API error: {e}")

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
                retryable_exceptions=(requests.exceptions.RequestException,)
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
                    delay = min(initial_delay * (exponential_base ** (retry_count - 1)), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            logger.error(f"OpenAI embedding API error after {max_retries} retries: {last_exception}")
            raise ProviderError(f"OpenAI embedding API error after {max_retries} retries: {last_exception}")

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
    ):
        """
        Initialize LM Studio provider.

        Args:
            endpoint: LM Studio API endpoint
            model: Model name (ignored in LM Studio, uses loaded model)
        """
        super().__init__(tls_config=tls_config, endpoint=endpoint, model=model)
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.headers = {"Content-Type": "application/json"}

    def _get_retry_config(self):
        """Get the retry configuration for LM Studio API calls."""
        return {
            "max_retries": self.retry_config["max_retries"],
            "initial_delay": self.retry_config["initial_delay"],
            "exponential_base": self.retry_config["exponential_base"],
            "max_delay": self.retry_config["max_delay"],
            "jitter": self.retry_config["jitter"],
        }

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
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
        def _api_call():
            url = f"{self.endpoint}/v1/chat/completions"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

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
                raise ProviderError(
                    f"Invalid LM Studio response format: {response_data}"
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
                retryable_exceptions=(requests.exceptions.RequestException,)
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            logger.error(f"LM Studio API error: {e}")
            raise ProviderError(f"LM Studio API error: {e}")

    async def acomplete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Asynchronously generate a completion using LM Studio."""
        # Define the actual API call function
        async def _api_call():
            url = f"{self.endpoint}/v1/chat/completions"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
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
                    delay = min(initial_delay * (exponential_base ** (retry_count - 1)), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            logger.error(f"LM Studio API error after {max_retries} retries: {last_exception}")
            raise ProviderError(f"LM Studio API error after {max_retries} retries: {last_exception}")

        except httpx.HTTPError as e:
            logger.error(f"LM Studio API error: {e}")
            raise ProviderError(f"LM Studio API error: {e}")

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
                retryable_exceptions=(requests.exceptions.RequestException,)
            )(_api_call)()
        except requests.exceptions.RequestException as e:
            logger.error(f"LM Studio embedding API error: {e}")
            raise ProviderError(f"LM Studio embedding API error: {e}")

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
                    delay = min(initial_delay * (exponential_base ** (retry_count - 1)), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        import random
                        delay = delay * (0.5 + random.random())

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # If we've exhausted all retries, raise the last exception
            logger.error(f"LM Studio embedding API error after {max_retries} retries: {last_exception}")
            raise ProviderError(f"LM Studio embedding API error after {max_retries} retries: {last_exception}")

        except httpx.HTTPError as e:
            logger.error(f"LM Studio embedding API error: {e}")
            raise ProviderError(f"LM Studio embedding API error: {e}")


class FallbackProvider(BaseProvider):
    """Fallback provider that tries multiple providers in sequence."""

    def __init__(self, providers: List[BaseProvider] = None):
        """
        Initialize with list of providers to try in sequence.

        Args:
            providers: List of provider instances (if None, auto-creates based on config)
        """
        super().__init__()

        # Get fallback and circuit breaker configuration
        config = get_provider_config()
        self.fallback_config = config.get("fallback", {
            "enabled": True,
            "order": ["openai", "lm_studio"],
        })
        self.circuit_breaker_config = config.get("circuit_breaker", {
            "enabled": True,
            "failure_threshold": 5,
            "recovery_timeout": 60.0,
        })

        # Initialize circuit breakers for providers
        self.circuit_breakers = {}

        if providers is None:
            # Try to create providers based on fallback order
            providers = []
            provider_order = self.fallback_config["order"]

            for provider_type in provider_order:
                if provider_type.lower() == ProviderType.OPENAI.value:
                    if config["openai"]["api_key"]:
                        try:
                            providers.append(
                                ProviderFactory.create_provider(ProviderType.OPENAI.value)
                            )
                            # Create circuit breaker for this provider
                            if self.circuit_breaker_config["enabled"]:
                                self.circuit_breakers[ProviderType.OPENAI.value] = CircuitBreaker(
                                    failure_threshold=self.circuit_breaker_config["failure_threshold"],
                                    recovery_timeout=self.circuit_breaker_config["recovery_timeout"]
                                )
                        except Exception as e:
                            logger.warning(
                                f"Failed to create OpenAI provider: {e}; continuing with next provider"
                            )
                    else:
                        logger.info("OpenAI API key missing; skipping OpenAI provider")
                elif provider_type.lower() == ProviderType.LM_STUDIO.value:
                    try:
                        providers.append(
                            ProviderFactory.create_provider(ProviderType.LM_STUDIO.value)
                        )
                        # Create circuit breaker for this provider
                        if self.circuit_breaker_config["enabled"]:
                            self.circuit_breakers[ProviderType.LM_STUDIO.value] = CircuitBreaker(
                                failure_threshold=self.circuit_breaker_config["failure_threshold"],
                                recovery_timeout=self.circuit_breaker_config["recovery_timeout"]
                            )
                    except Exception as e:
                        logger.warning(f"Failed to create LM Studio provider: {e}")

        if not providers:
            raise ProviderError("No valid providers available for fallback")

        self.providers = providers
        logger.info(
            "Initialized fallback provider order: %s",
            ", ".join(p.__class__.__name__ for p in self.providers),
        )

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Try to complete with each provider until one succeeds.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate

        Returns:
            str: Generated completion

        Raises:
            ProviderError: If all providers fail
        """
        last_error = None

        # If fallback is disabled and we have providers, just use the first one
        if not self.fallback_config.get("enabled", True) and self.providers:
            provider = self.providers[0]
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # Use circuit breaker if enabled
            if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                try:
                    return self.circuit_breakers[provider_type].call(
                        provider.complete,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                except Exception as e:
                    logger.error(f"Provider {provider.__class__.__name__} failed with circuit breaker: {e}")
                    raise ProviderError(f"Provider {provider.__class__.__name__} failed: {e}")
            else:
                return provider.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

        # Try each provider in sequence
        for provider in self.providers:
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # Skip if circuit breaker is open
            if (self.circuit_breaker_config.get("enabled", True) and 
                provider_type in self.circuit_breakers and 
                self.circuit_breakers[provider_type].state != "closed"):
                logger.warning(f"Skipping provider {provider.__class__.__name__} due to open circuit breaker")
                continue

            try:
                logger.info(f"Trying completion with provider: {provider.__class__.__name__}")

                # Use circuit breaker if enabled
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    return self.circuit_breakers[provider_type].call(
                        provider.complete,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                else:
                    return provider.complete(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                last_error = e

        raise ProviderError(
            f"All providers failed for completion. Last error: {last_error}"
        )

    async def acomplete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Asynchronously try each provider until one succeeds."""
        last_error = None

        # If fallback is disabled and we have providers, just use the first one
        if not self.fallback_config.get("enabled", True) and self.providers:
            provider = self.providers[0]
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # For async methods, we can't use the circuit breaker directly
            # since it doesn't support async calls, so we'll just check the state
            if (self.circuit_breaker_config.get("enabled", True) and 
                provider_type in self.circuit_breakers and 
                self.circuit_breakers[provider_type].state != "closed"):
                logger.warning(f"Provider {provider.__class__.__name__} circuit breaker is open")
                raise ProviderError(f"Provider {provider.__class__.__name__} circuit breaker is open")

            try:
                return await provider.acomplete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                # Update circuit breaker state manually
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    self.circuit_breakers[provider_type]._record_failure()
                logger.error(f"Provider {provider.__class__.__name__} failed: {e}")
                raise ProviderError(f"Provider {provider.__class__.__name__} failed: {e}")

        # Try each provider in sequence
        for provider in self.providers:
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # Skip if circuit breaker is open
            if (self.circuit_breaker_config.get("enabled", True) and 
                provider_type in self.circuit_breakers and 
                self.circuit_breakers[provider_type].state != "closed"):
                logger.warning(f"Skipping provider {provider.__class__.__name__} due to open circuit breaker")
                continue

            try:
                logger.info(f"Trying async completion with provider: {provider.__class__.__name__}")
                result = await provider.acomplete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # Update circuit breaker state manually on success
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    self.circuit_breakers[provider_type]._record_success()

                return result
            except Exception as e:
                # Update circuit breaker state manually on failure
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    self.circuit_breakers[provider_type]._record_failure()

                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                last_error = e

        raise ProviderError(
            f"All providers failed for completion. Last error: {last_error}"
        )

    def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Try to generate embeddings with each provider until one succeeds.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            ProviderError: If all providers fail
        """
        last_error = None

        # If fallback is disabled and we have providers, just use the first one
        if not self.fallback_config.get("enabled", True) and self.providers:
            provider = self.providers[0]
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # Use circuit breaker if enabled
            if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                try:
                    return self.circuit_breakers[provider_type].call(
                        provider.embed,
                        text=text,
                    )
                except Exception as e:
                    logger.error(f"Provider {provider.__class__.__name__} failed with circuit breaker: {e}")
                    raise ProviderError(f"Provider {provider.__class__.__name__} failed: {e}")
            else:
                return provider.embed(text=text)

        # Try each provider in sequence
        for provider in self.providers:
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # Skip if circuit breaker is open
            if (self.circuit_breaker_config.get("enabled", True) and 
                provider_type in self.circuit_breakers and 
                self.circuit_breakers[provider_type].state != "closed"):
                logger.warning(f"Skipping provider {provider.__class__.__name__} due to open circuit breaker")
                continue

            try:
                logger.info(f"Trying embeddings with provider: {provider.__class__.__name__}")

                # Use circuit breaker if enabled
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    return self.circuit_breakers[provider_type].call(
                        provider.embed,
                        text=text,
                    )
                else:
                    return provider.embed(text=text)
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed for embeddings: {e}")
                last_error = e

        raise ProviderError(
            f"All providers failed for embeddings. Last error: {last_error}"
        )

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronously try to generate embeddings with providers."""
        last_error = None

        # If fallback is disabled and we have providers, just use the first one
        if not self.fallback_config.get("enabled", True) and self.providers:
            provider = self.providers[0]
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # For async methods, we can't use the circuit breaker directly
            # since it doesn't support async calls, so we'll just check the state
            if (self.circuit_breaker_config.get("enabled", True) and 
                provider_type in self.circuit_breakers and 
                self.circuit_breakers[provider_type].state != "closed"):
                logger.warning(f"Provider {provider.__class__.__name__} circuit breaker is open")
                raise ProviderError(f"Provider {provider.__class__.__name__} circuit breaker is open")

            try:
                return await provider.aembed(text=text)
            except Exception as e:
                # Update circuit breaker state manually
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    self.circuit_breakers[provider_type]._record_failure()
                logger.error(f"Provider {provider.__class__.__name__} failed: {e}")
                raise ProviderError(f"Provider {provider.__class__.__name__} failed: {e}")

        # Try each provider in sequence
        for provider in self.providers:
            provider_type = provider.__class__.__name__.replace("Provider", "").lower()

            # Skip if circuit breaker is open
            if (self.circuit_breaker_config.get("enabled", True) and 
                provider_type in self.circuit_breakers and 
                self.circuit_breakers[provider_type].state != "closed"):
                logger.warning(f"Skipping provider {provider.__class__.__name__} due to open circuit breaker")
                continue

            try:
                logger.info(f"Trying async embeddings with provider: {provider.__class__.__name__}")
                result = await provider.aembed(text=text)

                # Update circuit breaker state manually on success
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    self.circuit_breakers[provider_type]._record_success()

                return result
            except Exception as e:
                # Update circuit breaker state manually on failure
                if self.circuit_breaker_config.get("enabled", True) and provider_type in self.circuit_breakers:
                    self.circuit_breakers[provider_type]._record_failure()

                logger.warning(f"Provider {provider.__class__.__name__} failed for embeddings: {e}")
                last_error = e

        raise ProviderError(
            f"All providers failed for embeddings. Last error: {last_error}"
        )


# Simplified API for common usage
def get_provider(
    provider_type: Optional[str] = None, fallback: bool = True
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
    return provider.complete(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


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
