from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List

from devsynth.application.llm.providers import BaseLLMProvider
from devsynth.domain.interfaces.llm import StreamingLLMProvider
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class MockLLMAdapter(BaseLLMProvider, StreamingLLMProvider):
    """Mock LLM adapter for testing purposes."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.responses = {
            "default": "This is a mock response from the MockLLMAdapter.",
            "code_review": (
                "I've reviewed the code and found the following issues:\n\n"
                "1. The function doesn't handle edge cases.\n"
                "2. There's no type checking or validation of inputs.\n\n"
                "Suggested improvements:\n\n"
                "```python\n"
                "def improved_function(a, b):\n"
                "    # Add validation here\n"
                "    return a + b\n"
                "```"
            ),
        }
        self.embeddings = {"default": [0.1, 0.2, 0.3, 0.4, 0.5]}

    def generate(self, prompt: str, parameters: Dict[str, Any] = None) -> str:
        """Generate text from a prompt."""
        logger.debug(
            "MockLLMAdapter.generate called with prompt: %s...",
            prompt[:50],
        )

        # Check if the prompt contains a key from the responses dictionary
        for key, response in self.responses.items():
            if key in prompt:
                return response

        return self.responses["default"]

    def generate_with_context(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> str:
        """Generate text from a prompt with conversation context."""
        logger.debug(
            "MockLLMAdapter.generate_with_context called with prompt: %s...",
            prompt[:50],
        )

        # For simplicity, we'll just use the same logic as generate
        return self.generate(prompt, parameters)

    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text."""
        logger.debug(
            "MockLLMAdapter.get_embedding called with text: %s...",
            text[:50],
        )

        # Check if the text contains a key from the embeddings dictionary
        for key, embedding in self.embeddings.items():
            if key in text:
                return embedding

        return self.embeddings["default"]

    async def generate_stream(
        self, prompt: str, parameters: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with streaming."""
        logger.debug(
            "MockLLMAdapter.generate_stream called with prompt: %s...",
            prompt[:50],
        )

        response = self.generate(prompt, parameters)

        async def _stream() -> AsyncGenerator[str, None]:
            words = response.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i : i + 3])
                yield chunk + " "

        return _stream()

    async def generate_with_context_stream(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        parameters: Dict[str, Any] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate text from a prompt with conversation context with streaming."""
        logger.debug(
            "MockLLMAdapter.generate_with_context_stream called with prompt: %s...",
            prompt[:50],
        )

        response = self.generate_with_context(prompt, context, parameters)

        async def _stream() -> AsyncGenerator[str, None]:
            words = response.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i : i + 3])
                yield chunk + " "

        return _stream()
