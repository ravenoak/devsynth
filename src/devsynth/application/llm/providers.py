from typing import Any, Dict, List, Optional
import httpx
from ...domain.interfaces.llm import LLMProvider, LLMProviderFactory
import os
from devsynth.core.config_loader import load_config
from devsynth.config import get_llm_settings

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class ValidationError(DevSynthError):
    """Exception raised when validation fails."""

    pass


class BaseLLMProvider:
    """Base class for LLM providers."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt."""
        raise NotImplementedError("Subclasses must implement this method")

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> str:
        """Generate text from a prompt with conversation context."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text."""
        raise NotImplementedError("Subclasses must implement this method")


class AnthropicConnectionError(DevSynthError):
    """Exception raised when there's an issue connecting to Anthropic."""


class AnthropicModelError(DevSynthError):
    """Exception raised for errors returned by Anthropic's API."""


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider implementation."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)

        self.api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        self.model = self.config.get("model", "claude-2")
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.temperature = self.config.get("temperature", 0.7)
        self.api_base = self.config.get("api_base", "https://api.anthropic.com")
        self.timeout = self.config.get("timeout", 60)
        self.embedding_model = self.config.get("embedding_model", "claude-3-embed")

        if not self.api_key:
            raise AnthropicConnectionError("Anthropic API key is required")

        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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

    def generate(self, prompt: str, parameters: Dict[str, Any] | None = None) -> str:
        """Generate text from a prompt using Anthropic."""

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

        data = self._post("/v1/messages", payload)

        if "content" in data and isinstance(data["content"], list):
            return "".join(part.get("text", "") for part in data["content"])
        if "completion" in data:
            return data["completion"]
        raise AnthropicModelError("Invalid response from Anthropic")

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] | None = None,
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

    def get_embedding(self, text: str) -> List[float]:
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
    """Simple implementation of LLMProviderFactory."""

    def __init__(self):
        self.provider_types: Dict[str, type] = {}

    def create_provider(
        self, provider_type: str, config: Dict[str, Any] = None
    ) -> LLMProvider:
        """Create an LLM provider of the specified type."""
        if provider_type not in self.provider_types:
            raise ValidationError(f"Unknown provider type: {provider_type}")

        provider_class = self.provider_types[provider_type]
        return provider_class(config)

    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        self.provider_types[provider_type] = provider_class


# Provider selection logic
def get_llm_provider(config: Dict[str, Any] | None = None) -> LLMProvider:
    """Return an LLM provider based on configuration."""

    cfg = config or load_config().as_dict()
    offline = cfg.get("offline_mode", False)

    llm_cfg = get_llm_settings()
    provider_type = "offline" if offline else llm_cfg.get("provider", "openai")
    return factory.create_provider(provider_type, llm_cfg)


# Import providers at the end to avoid circular imports
from .lmstudio_provider import LMStudioProvider
from .openai_provider import OpenAIProvider
from .local_provider import LocalProvider
from .offline_provider import OfflineProvider

# Create factory instance
factory = SimpleLLMProviderFactory()

# Register providers
factory.register_provider_type("anthropic", AnthropicProvider)
factory.register_provider_type("lmstudio", LMStudioProvider)
factory.register_provider_type("openai", OpenAIProvider)
factory.register_provider_type("local", LocalProvider)
factory.register_provider_type("offline", OfflineProvider)
