"""
OpenRouter Provider implementation for DevSynth.

This provider connects to the OpenRouter API for model inference, providing
access to 400+ AI models through a unified interface.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import httpx
except ImportError:  # pragma: no cover - fallback when httpx not available
    httpx = None

import concurrent.futures

from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import inc_provider

# Import get_llm_settings lazily to avoid import issues during testing
from ...domain.interfaces.llm import LLMProvider, StreamingLLMProvider
from ..utils.token_tracker import TokenLimitExceededError, TokenTracker

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class OpenRouterConnectionError(DevSynthError):
    """Exception raised when there's an issue connecting to OpenRouter."""

    pass


class OpenRouterModelError(DevSynthError):
    """Exception raised when there's an issue with OpenRouter models."""

    pass


class OpenRouterProvider(StreamingLLMProvider):
    """OpenRouter LLM provider implementation."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the OpenRouter provider.

        Args:
            config: Configuration dictionary with the following keys:
                - api_key: OpenRouter API key (default: from config)
                - model: Model name to use (default: from config, falls back to free tier)
                - max_tokens: Maximum tokens for responses (default: from config)
                - temperature: Temperature for generation (default: from config)
                - base_url: Base URL for the OpenRouter API (default: https://openrouter.ai/api/v1)
                - timeout: Request timeout in seconds (default: from config)

        Raises:
            OpenRouterConnectionError: If no API key is provided or available in environment
        """
        # Get default settings from configuration
        from ...config.settings import get_llm_settings

        default_settings = get_llm_settings()

        # Initialize with default settings, overridden by provided config
        self.config = {**default_settings, **(config or {})}

        # Set instance variables from config
        self.api_key = self.config.get("openrouter_api_key")
        self.model = (
            self.config.get("openrouter_model") or "google/gemini-flash-1.5"
        )  # Default to free tier
        self.max_tokens = self.config.get("max_tokens") or 4096
        self.temperature = self.config.get("temperature") or 0.7
        self.base_url = self.config.get("base_url") or "https://openrouter.ai/api/v1"
        self.timeout = self.config.get("timeout") or 60
        self.max_retries = self.config.get("max_retries", 3)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60),
        )

        # Check for API key in config or environment
        if not self.api_key and "OPENROUTER_API_KEY" in __import__("os").environ:
            self.api_key = __import__("os").environ["OPENROUTER_API_KEY"]

        # Initialize token tracker
        self.token_tracker = TokenTracker()

        # Require API key explicitly for this provider; tests enforce clear error
        if not self.api_key:
            raise OpenRouterConnectionError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY or provide 'openrouter_api_key' in config."
            )

        # Initialize HTTP clients
        self._init_clients()

        logger.info(f"Initialized OpenRouter provider with model: {self.model}")

    def _init_clients(self):
        """Initialize HTTP clients for OpenRouter API."""
        # Set up headers with required attribution for OpenRouter
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://devsynth.dev",
            "X-Title": "DevSynth AI Platform",
        }

        # Initialize clients if dependencies are available
        try:
            import httpx

            # Create sync and async clients for different use cases
            self.sync_client = httpx.Client(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self.timeout,
            )
            self.async_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self.timeout,
            )
        except ImportError:
            # Fallback when httpx not available
            self.sync_client = None
            self.async_client = None

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
            "Retrying OpenRouterProvider due to %s (attempt %d, delay %.2fs)",
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

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt using OpenRouter.

        Args:
            prompt: The prompt to generate text from
            parameters: Additional parameters for the generation

        Returns:
            The generated text

        Raises:
            OpenRouterConnectionError: If there's an issue connecting to OpenRouter
            OpenRouterModelError: If there's an issue with the model or response
            TokenLimitExceededError: If the prompt exceeds the token limit
        """
        # Ensure the prompt doesn't exceed token limits
        self.token_tracker.ensure_token_limit(prompt, self.max_tokens)

        # Merge default parameters with provided parameters
        params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if parameters:
            params.update(parameters)

        # Prepare the request payload
        messages = [{"role": "user", "content": prompt}]

        def _api_call():
            if self.sync_client is None:
                raise OpenRouterConnectionError("HTTP client not available")

            payload = {
                "model": self.model,
                "messages": messages,
                **params,
            }

            response = self.sync_client.post("/chat/completions", json=payload)
            response.raise_for_status()
            response_data = response.json()

            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            else:
                raise OpenRouterModelError("Invalid response from OpenRouter")

        try:
            return self._execute_with_resilience(_api_call)
        except Exception as e:
            error_msg = f"OpenRouter API error: {str(e)}"
            logger.error(error_msg)
            raise OpenRouterConnectionError(error_msg)

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> str:
        """Generate text from a prompt with conversation context using OpenRouter.

        Args:
            prompt: The prompt to generate text from
            context: List of conversation messages in the format [{"role": "...", "content": "..."}]
            parameters: Additional parameters for the generation

        Returns:
            The generated text

        Raises:
            OpenRouterConnectionError: If there's an issue connecting to OpenRouter
            OpenRouterModelError: If there's an issue with the model or response
            TokenLimitExceededError: If the conversation exceeds the token limit
        """
        # Create a copy of the context and add the new prompt
        messages = context.copy()
        messages.append({"role": "user", "content": prompt})

        # Check token count and prune if necessary
        token_count = self.token_tracker.count_conversation_tokens(messages)
        if token_count > self.max_tokens:
            messages = self.token_tracker.prune_conversation(messages, self.max_tokens)

        # Merge default parameters with provided parameters
        params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if parameters:
            params.update(parameters)

        def _api_call():
            if self.sync_client is None:
                raise OpenRouterConnectionError("HTTP client not available")

            payload = {
                "model": self.model,
                "messages": messages,
                **params,
            }

            response = self.sync_client.post("/chat/completions", json=payload)
            response.raise_for_status()
            response_data = response.json()

            if "choices" in response_data and len(response_data["choices"]) > 0:
                return response_data["choices"][0]["message"]["content"]
            else:
                raise OpenRouterModelError("Invalid response from OpenRouter")

        try:
            return self._execute_with_resilience(_api_call)
        except Exception as e:
            error_msg = f"OpenRouter API error: {str(e)}"
            logger.error(error_msg)
            raise OpenRouterConnectionError(error_msg)

    async def generate_stream(
        self, prompt: str, parameters: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt using OpenRouter with streaming.

        Args:
            prompt: The prompt to generate text from
            parameters: Additional parameters for the generation

        Yields:
            Chunks of generated text

        Raises:
            OpenRouterConnectionError: If there's an issue connecting to OpenRouter
            OpenRouterModelError: If there's an issue with the model or response
            TokenLimitExceededError: If the prompt exceeds the token limit
        """
        if httpx is None:
            raise OpenRouterConnectionError("httpx package required for streaming")

        # Ensure the prompt doesn't exceed token limits
        self.token_tracker.ensure_token_limit(prompt, self.max_tokens)

        # Merge default parameters with provided parameters
        params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if parameters:
            params.update(parameters)

        # Prepare the request payload
        messages = [{"role": "user", "content": prompt}]

        @retry_with_exponential_backoff(
            max_retries=self.max_retries, should_retry=self._should_retry
        )
        def _wrapped():
            return self.circuit_breaker.call(
                self.async_client.post,
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    **params,
                },
            )

        async def stream_generator() -> AsyncGenerator[str, None]:
            try:
                async with self.async_client.stream(
                    "POST",
                    "/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                        **params,
                    },
                ) as response:
                    response.raise_for_status()

                    # Process the streaming response
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break

                            try:
                                chunk = response.json()
                                if chunk.get("choices") and chunk["choices"][0].get(
                                    "delta", {}
                                ).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except Exception:
                                # Skip malformed chunks
                                continue

            except Exception as e:
                error_msg = f"OpenRouter streaming API error: {str(e)}"
                logger.error(error_msg)
                raise OpenRouterConnectionError(error_msg)

        return stream_generator()

    async def generate_with_context_stream(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with conversation context using OpenRouter with streaming.

        Args:
            prompt: The prompt to generate text from
            context: List of conversation messages in the format [{"role": "...", "content": "..."}]
            parameters: Additional parameters for the generation

        Yields:
            Chunks of generated text

        Raises:
            OpenRouterConnectionError: If there's an issue connecting to OpenRouter
            OpenRouterModelError: If there's an issue with the model or response
            TokenLimitExceededError: If the conversation exceeds the token limit
        """
        if httpx is None:
            raise OpenRouterConnectionError("httpx package required for streaming")

        # Create a copy of the context and add the new prompt
        messages = context.copy()
        messages.append({"role": "user", "content": prompt})

        # Check token count and prune if necessary
        token_count = self.token_tracker.count_conversation_tokens(messages)
        if token_count > self.max_tokens:
            messages = self.token_tracker.prune_conversation(messages, self.max_tokens)

        # Merge default parameters with provided parameters
        params = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if parameters:
            params.update(parameters)

        async def stream_generator() -> AsyncGenerator[str, None]:
            try:
                async with self.async_client.stream(
                    "POST",
                    "/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                        **params,
                    },
                ) as response:
                    response.raise_for_status()

                    # Process the streaming response
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break

                            try:
                                chunk = response.json()
                                if chunk.get("choices") and chunk["choices"][0].get(
                                    "delta", {}
                                ).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except Exception:
                                # Skip malformed chunks
                                continue

            except Exception as e:
                error_msg = f"OpenRouter streaming API error: {str(e)}"
                logger.error(error_msg)
                raise OpenRouterConnectionError(error_msg)

        return stream_generator()

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text using OpenRouter.

        Args:
            text: The text to get an embedding for

        Returns:
            The embedding vector as a list of floats

        Raises:
            OpenRouterConnectionError: If there's an issue connecting to OpenRouter
            OpenRouterModelError: If there's an issue with the model or response
        """

        def _api_call():
            if self.sync_client is None:
                raise OpenRouterConnectionError("HTTP client not available")

            payload = {
                "model": "text-embedding-ada-002",  # Use OpenAI-compatible embedding model
                "input": text,
            }

            response = self.sync_client.post("/embeddings", json=payload)
            response.raise_for_status()
            response_data = response.json()

            if "data" in response_data and len(response_data["data"]) > 0:
                return response_data["data"][0]["embedding"]
            else:
                raise OpenRouterModelError("Invalid embedding response from OpenRouter")

        try:
            return self._execute_with_resilience(_api_call)
        except Exception as e:
            error_msg = f"OpenRouter embedding API error: {str(e)}"
            logger.error(error_msg)
            raise OpenRouterConnectionError(error_msg)
