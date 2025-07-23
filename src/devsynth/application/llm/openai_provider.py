"""
OpenAI Provider implementation for DevSynth.
This provider connects to the OpenAI API for model inference.
"""

import os
import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from ..utils.token_tracker import TokenTracker, TokenLimitExceededError
from ...domain.interfaces.llm import LLMProvider, StreamingLLMProvider
from ...config.settings import get_llm_settings

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger
from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class OpenAIConnectionError(DevSynthError):
    """Exception raised when there's an issue connecting to OpenAI."""

    pass


class OpenAIModelError(DevSynthError):
    """Exception raised when there's an issue with OpenAI models."""

    pass


class OpenAIProvider(StreamingLLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the OpenAI provider.

        Args:
            config: Configuration dictionary with the following keys:
                - api_key: OpenAI API key (default: from config)
                - model: Model name to use (default: from config)
                - max_tokens: Maximum tokens for responses (default: from config)
                - temperature: Temperature for generation (default: from config)
                - api_base: Base URL for the OpenAI API (default: from config)

        Raises:
            OpenAIConnectionError: If no API key is provided or available in environment
        """
        # Get default settings from configuration
        default_settings = get_llm_settings()

        # Initialize with default settings, overridden by provided config
        self.config = {**default_settings, **(config or {})}

        # Set instance variables from config
        self.api_key = self.config.get("openai_api_key")
        self.model = self.config.get("openai_model") or "gpt-3.5-turbo"
        self.max_tokens = self.config.get("max_tokens") or 1024
        self.temperature = self.config.get("temperature") or 0.7
        self.api_base = self.config.get("api_base")
        self.max_retries = self.config.get("max_retries", 3)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60),
        )

        # Check for API key in config or environment
        if not self.api_key and "OPENAI_API_KEY" in os.environ:
            self.api_key = os.environ["OPENAI_API_KEY"]

        # Raise error if no API key is available
        if not self.api_key:
            raise OpenAIConnectionError("OpenAI API key is required")

        # Initialize token tracker
        self.token_tracker = TokenTracker()

        # Initialize OpenAI client
        self._init_client()

        logger.info(f"Initialized OpenAI provider with model: {self.model}")

    def _init_client(self):
        """Initialize the OpenAI client."""
        client_kwargs = {}

        client_kwargs["api_key"] = self.api_key

        if self.api_base:
            client_kwargs["base_url"] = self.api_base

        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

    def _should_retry(self, exc: Exception) -> bool:
        """Return ``True`` if the exception should trigger a retry."""
        status = getattr(exc, "status_code", None)
        if status is not None and 400 <= int(status) < 500 and int(status) != 429:
            return False
        return True

    def _execute_with_resilience(self, func, *args, **kwargs):
        """Execute a function with retry and circuit breaker protection."""

        @retry_with_exponential_backoff(
            max_retries=self.max_retries, should_retry=self._should_retry
        )
        def _wrapped():
            return self.circuit_breaker.call(func, *args, **kwargs)

        return _wrapped()

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt using OpenAI.

        Args:
            prompt: The prompt to generate text from
            parameters: Additional parameters for the generation

        Returns:
            The generated text

        Raises:
            OpenAIConnectionError: If there's an issue connecting to OpenAI
            OpenAIModelError: If there's an issue with the model or response
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

        try:
            response = self._execute_with_resilience(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                **params,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIConnectionError(error_msg)

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> str:
        """Generate text from a prompt with conversation context using OpenAI.

        Args:
            prompt: The prompt to generate text from
            context: List of conversation messages in the format [{"role": "...", "content": "..."}]
            parameters: Additional parameters for the generation

        Returns:
            The generated text

        Raises:
            OpenAIConnectionError: If there's an issue connecting to OpenAI
            OpenAIModelError: If there's an issue with the model or response
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

        try:
            response = self._execute_with_resilience(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                **params,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIConnectionError(error_msg)

    async def generate_stream(
        self, prompt: str, parameters: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt using OpenAI with streaming.

        Args:
            prompt: The prompt to generate text from
            parameters: Additional parameters for the generation

        Yields:
            Chunks of generated text

        Raises:
            OpenAIConnectionError: If there's an issue connecting to OpenAI
            OpenAIModelError: If there's an issue with the model or response
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

        # Define a function to create the stream with retry and circuit breaker protection
        async def create_stream_with_resilience():
            @retry_with_exponential_backoff(
                max_retries=self.max_retries, should_retry=self._should_retry
            )
            def _wrapped():
                return self.circuit_breaker.call(
                    self.async_client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    stream=True,
                    **params,
                )

            return await _wrapped()

        # Make the API call with resilience
        try:
            stream = await create_stream_with_resilience()

            # Yield chunks of generated text
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIConnectionError(error_msg)

    async def generate_with_context_stream(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with conversation context using OpenAI with streaming.

        Args:
            prompt: The prompt to generate text from
            context: List of conversation messages in the format [{"role": "...", "content": "..."}]
            parameters: Additional parameters for the generation

        Yields:
            Chunks of generated text

        Raises:
            OpenAIConnectionError: If there's an issue connecting to OpenAI
            OpenAIModelError: If there's an issue with the model or response
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

        # Define a function to create the stream with retry and circuit breaker protection
        async def create_stream_with_resilience():
            @retry_with_exponential_backoff(
                max_retries=self.max_retries, should_retry=self._should_retry
            )
            def _wrapped():
                return self.circuit_breaker.call(
                    self.async_client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    stream=True,
                    **params,
                )

            return await _wrapped()

        # Make the API call with resilience
        try:
            stream = await create_stream_with_resilience()

            # Yield chunks of generated text
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIConnectionError(error_msg)

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text using OpenAI.

        Args:
            text: The text to get an embedding for

        Returns:
            The embedding vector as a list of floats

        Raises:
            OpenAIConnectionError: If there's an issue connecting to OpenAI
            OpenAIModelError: If there's an issue with the model or response
        """
        try:
            embedding_model = (
                self.config.get("openai_embedding_model") or "text-embedding-ada-002"
            )
            response = self._execute_with_resilience(
                self.client.embeddings.create,
                model=embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIConnectionError(error_msg)
