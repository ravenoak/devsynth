"""Local LLM provider for offline mode."""

from typing import Any, AsyncGenerator, Dict, List

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

# Import get_llm_settings lazily to avoid import issues during testing
from ...domain.interfaces.llm import StreamingLLMProvider
from ..utils.token_tracker import TokenTracker

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class LocalProviderError(DevSynthError):
    """Exception raised for local provider errors."""


class LocalProvider(StreamingLLMProvider):
    """Simplified local provider used when offline_mode is enabled."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        from ...config.settings import get_llm_settings
        default_settings = get_llm_settings()
        self.config = {**default_settings, **(config or {})}

        self.model_path = self.config.get("model_path") or self.config.get(
            "local_model_path"
        )
        self.model = self.config.get("model", "local_model")
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.temperature = self.config.get("temperature", 0.7)
        self.context_length = self.config.get("context_length", 2048)
        self.token_tracker = TokenTracker()

    def generate(self, prompt: str, parameters: Dict[str, Any] | None = None) -> str:
        """Generate a response for the given prompt."""
        self.token_tracker.ensure_token_limit(prompt, self.max_tokens)
        return f"[local] {prompt}"

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] | None = None,
    ) -> str:
        """Generate a response using conversation context."""
        messages = context.copy()
        messages.append({"role": "user", "content": prompt})
        token_count = self.token_tracker.count_conversation_tokens(messages)
        if token_count > self.context_length:
            messages = self.token_tracker.prune_conversation(
                messages, self.context_length
            )
        return f"[local] {prompt}"

    def get_embedding(self, text: str) -> List[float]:
        """Return a deterministic embedding vector for the text."""
        return [float(ord(c)) for c in text[:8]]

    async def generate_stream(
        self, prompt: str, parameters: Dict[str, Any] | None = None
    ) -> AsyncGenerator[str, None]:
        """Stream a generated response."""

        async def _stream() -> AsyncGenerator[str, None]:
            yield self.generate(prompt, parameters)

        return _stream()

    async def generate_with_context_stream(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a generated response using conversation context."""

        async def _stream() -> AsyncGenerator[str, None]:
            yield self.generate_with_context(prompt, context, parameters)

        return _stream()
