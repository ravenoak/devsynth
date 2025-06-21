"""
Provider System for abstracting LLM providers (OpenAI, LM Studio).

This module implements a unified interface for different LLM providers with
automatic fallback and selection based on configuration.
"""

import os
import json
import logging
import requests
import httpx
import time
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
from functools import lru_cache, wraps

from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import inc_provider
from devsynth.exceptions import DevSynthError
from devsynth.fallback import retry_with_exponential_backoff
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

    @retry_with_exponential_backoff(max_retries=3, initial_delay=1, max_delay=10)
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

        try:
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

        try:
            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            raise ProviderError(f"Invalid response format: {data}")
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ProviderError(f"OpenAI API error: {e}")

    @retry_with_exponential_backoff(max_retries=3, initial_delay=1, max_delay=10)
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
        url = f"{self.base_url}/embeddings"

        if isinstance(text, str):
            text = [text]

        payload = {
            "model": "text-embedding-3-small",  # Use appropriate embedding model
            "input": text,
        }

        try:
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

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI embedding API error: {e}")
            raise ProviderError(f"OpenAI embedding API error: {e}")

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronously generate embeddings using the OpenAI API."""
        url = f"{self.base_url}/embeddings"

        if isinstance(text, str):
            text = [text]

        payload = {
            "model": "text-embedding-3-small",
            "input": text,
        }

        try:
            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "data" in data and len(data["data"]) > 0:
                return [item["embedding"] for item in data["data"]]
            raise ProviderError(f"Invalid embedding response format: {data}")
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

    @retry_with_exponential_backoff(max_retries=3, initial_delay=1, max_delay=10)
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

        try:
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

        try:
            async with httpx.AsyncClient(
                **self.tls_config.as_requests_kwargs()
            ) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            raise ProviderError(f"Invalid LM Studio response format: {data}")
        except httpx.HTTPError as e:
            logger.error(f"LM Studio API error: {e}")
            raise ProviderError(f"LM Studio API error: {e}")

    def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings using LM Studio API.
        Note: LM Studio might not support embeddings directly.
        This implementation is a placeholder.

        Args:
            text: Input text or list of texts

        Returns:
            List[List[float]]: Embeddings

        Raises:
            ProviderError: If API call fails or not supported
        """
        # If LM Studio supports embeddings, implement here
        # For now, raise an error
        raise ProviderError("Embeddings not supported by LM Studio provider")

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronous embeddings placeholder for LM Studio."""
        raise ProviderError("Embeddings not supported by LM Studio provider")


class FallbackProvider(BaseProvider):
    """Fallback provider that tries multiple providers in sequence."""

    def __init__(self, providers: List[BaseProvider] = None):
        """
        Initialize with list of providers to try in sequence.

        Args:
            providers: List of provider instances (if None, auto-creates based on config)
        """
        super().__init__()

        if providers is None:
            # Try to create providers in order: OpenAI, LM Studio
            providers = []
            config = get_provider_config()

            # Try OpenAI
            if config["openai"]["api_key"]:
                try:
                    providers.append(
                        ProviderFactory.create_provider(ProviderType.OPENAI.value)
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to create OpenAI provider: {e}; attempting LM Studio"
                    )
            else:
                logger.info("OpenAI API key missing; skipping OpenAI provider")

            # Try LM Studio
            try:
                providers.append(
                    ProviderFactory.create_provider(ProviderType.LM_STUDIO.value)
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

        for provider in self.providers:
            try:
                logger.info(
                    f"Trying completion with provider: {provider.__class__.__name__}"
                )
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

        for provider in self.providers:
            try:
                logger.info(
                    f"Trying completion with provider: {provider.__class__.__name__}"
                )
                return await provider.acomplete(
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

        for provider in self.providers:
            try:
                logger.info(
                    f"Trying embeddings with provider: {provider.__class__.__name__}"
                )
                return provider.embed(text=text)
            except Exception as e:
                logger.warning(
                    f"Provider {provider.__class__.__name__} failed for embeddings: {e}"
                )
                last_error = e

        raise ProviderError(
            f"All providers failed for embeddings. Last error: {last_error}"
        )

    async def aembed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Asynchronously try to generate embeddings with providers."""
        last_error = None

        for provider in self.providers:
            try:
                logger.info(
                    f"Trying embeddings with provider: {provider.__class__.__name__}"
                )
                return await provider.aembed(text=text)
            except Exception as e:
                logger.warning(
                    f"Provider {provider.__class__.__name__} failed for embeddings: {e}"
                )
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
