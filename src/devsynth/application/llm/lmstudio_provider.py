
"""
LM Studio Provider implementation for DevSynth.
This provider connects to a local LM Studio server running on localhost.
"""

import os
from urllib.parse import urlparse
import lmstudio
from typing import Any, Dict, List, Optional, Tuple
from ..utils.token_tracker import TokenTracker, TokenLimitExceededError
from ...domain.interfaces.llm import LLMProvider
from ...config import get_llm_settings

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger
from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class LMStudioConnectionError(DevSynthError):
    """Exception raised when there's an issue connecting to LM Studio."""
    pass

class LMStudioModelError(DevSynthError):
    """Exception raised when there's an issue with LM Studio models."""
    pass

class BaseLLMProvider:
    """Base class for LLM providers."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt."""
        raise NotImplementedError("Subclasses must implement this method")

    def generate_with_context(self, prompt: str, context: List[Dict[str, str]], parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt with conversation context."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text."""
        raise NotImplementedError("Subclasses must implement this method")

class LMStudioProvider(BaseLLMProvider):
    """LM Studio LLM provider implementation."""

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
        default_settings = get_llm_settings()

        # Initialize with default settings, overridden by provided config
        merged_config = {**default_settings, **(config or {})}
        super().__init__(merged_config)

        # Set instance variables from config
        self.api_base = self.config.get("api_base")
        self.max_tokens = self.config.get("max_tokens")
        self.temperature = self.config.get("temperature")
        parsed = urlparse(self.api_base)
        self.api_host = parsed.netloc or parsed.path.split("/")[0]
        lmstudio.sync_api.configure_default_client(self.api_host)
        self.max_retries = self.config.get("max_retries", 3)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.get("failure_threshold", 3),
            recovery_timeout=self.config.get("recovery_timeout", 60),
        )
        self.token_tracker = TokenTracker()

        # Auto-select model if not specified
        auto_select = self.config.get("auto_select_model")
        specified_model = self.config.get("model")

        if specified_model:
            self.model = specified_model
            logger.info(f"Using specified model: {self.model}")
        elif auto_select:
            try:
                available_models = self.list_available_models()
                if available_models:
                    self.model = available_models[0]["id"]
                    logger.info(f"Auto-selected model: {self.model}")
                else:
                    self.model = "local_model"
                    logger.warning("No models available from LM Studio. Using default: local_model")
            except LMStudioConnectionError as e:
                self.model = "local_model"
                logger.warning(f"Could not connect to LM Studio: {str(e)}. Using default: local_model")
        else:
            self.model = "local_model"
            logger.info("Using default model: local_model")

    def _execute_with_resilience(self, func, *args, **kwargs):
        """Execute a function with retry and circuit breaker protection."""

        @retry_with_exponential_backoff(max_retries=self.max_retries)
        def _wrapped():
            return self.circuit_breaker.call(func, *args, **kwargs)

        return _wrapped()

    def list_available_models(self) -> List[Dict[str, Any]]:
        """List available models from LM Studio.

        Returns:
            A list of available models with their details

        Raises:
            LMStudioConnectionError: If there's an issue connecting to LM Studio
        """
        try:
            models = lmstudio.sync_api.list_downloaded_models("llm")
            logger.info(f"Found {len(models)} models from LM Studio")
            return [
                {"id": m.model_key, "name": m.display_name}
                for m in models
            ]
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
                lmstudio.llm(self.model).complete,
                prompt,
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

    def generate_with_context(self, prompt: str, context: List[Dict[str, str]], parameters: Dict[str, Any] = None) -> str:
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
                lmstudio.llm(self.model).respond,
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
                lmstudio.embedding_model(self.model).embed,
                text,
            )
            if isinstance(result, list) and result:
                return result if isinstance(result[0], float) else result[0]
            raise LMStudioModelError("Invalid embedding response")
        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to connect to LM Studio: {str(e)}"
            logger.error(error_msg)
            raise LMStudioConnectionError(error_msg)
