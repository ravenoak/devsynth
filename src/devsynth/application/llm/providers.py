import os
from typing import Any, Dict, List, Optional

import httpx

from devsynth.config import get_llm_settings
from devsynth.core.config_loader import load_config

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

from ...domain.interfaces.llm import LLMProvider, LLMProviderFactory

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
    """Simple implementation of LLMProviderFactory with lazy provider resolution.

    The registry accepts either:
    - a provider class type; or
    - a callable taking a config dict and returning either an instance or a class.

    This design ensures that test-time stubs applied to provider modules are respected,
    aligning with tasks in docs/tasks.md (13, 31, 32).
    """

    def __init__(self):
        self.provider_types: Dict[str, Any] = {}

    def create_provider(
        self, provider_type: str, config: Dict[str, Any] = None
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
            # If it returned an instance, use it directly; if it returned a class, instantiate.
            try:
                # Duck-typing: check for typical provider methods
                if hasattr(obj, "generate") or hasattr(obj, "complete"):
                    return obj  # type: ignore[return-value]
            except Exception:
                pass
            return obj(cfg)  # type: ignore[misc]
        # Otherwise, assume it's a class type
        provider_class = entry
        return provider_class(cfg)  # type: ignore[call-arg]

    def register_provider_type(
        self, provider_type: str, provider_class_or_factory: Any
    ) -> None:
        """Register a new provider type or factory."""
        self.provider_types[provider_type] = provider_class_or_factory


# Provider selection logic
def get_llm_provider(config: Dict[str, Any] | None = None) -> LLMProvider:
    """Return an LLM provider based on configuration.

    Safe-by-default policy:
    - If offline_mode is true, select 'offline'.
    - If a provider is explicitly configured, use it but validate required credentials.
    - Otherwise, default to 'offline'.
    """

    cfg = config or load_config().as_dict()
    offline = cfg.get("offline_mode", False)

    # Tests default: require explicit opt-in to use real providers
    allow_providers = os.getenv("DEVSYNTH_TEST_ALLOW_PROVIDERS", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    if not allow_providers:
        offline = True

    llm_cfg = get_llm_settings()
    if "offline_provider" in cfg:
        llm_cfg["offline_provider"] = cfg["offline_provider"]

    # Determine provider safely
    if offline:
        provider_type = "offline"
    else:
        provider_type = llm_cfg.get("provider") or "offline"

    # Validate credentials if a remote provider is explicitly requested
    pt_lower = str(provider_type).lower()
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
from . import local_provider as _local_provider
from . import offline_provider as _offline_provider
from . import openai_provider as _openai_provider

# Create factory instance
factory = SimpleLLMProviderFactory()

# Register providers using callables to resolve classes at call time
factory.register_provider_type("anthropic", lambda cfg: AnthropicProvider(cfg))
if LMStudioProvider is not None:
    # Keep direct reference for optional provider; if stubbing is applied at the module level,
    # tests that need LMStudio should opt-in via DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
    factory.register_provider_type("lmstudio", lambda cfg: LMStudioProvider(cfg))
factory.register_provider_type(
    "openai", lambda cfg: _openai_provider.OpenAIProvider(cfg)
)
factory.register_provider_type("local", lambda cfg: _local_provider.LocalProvider(cfg))
factory.register_provider_type(
    "offline", lambda cfg: _offline_provider.OfflineProvider(cfg)
)
