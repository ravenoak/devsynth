from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from collections.abc import AsyncIterator, Mapping, Sequence

from devsynth.logging_setup import DevSynthLogger

if TYPE_CHECKING:  # pragma: no cover - used only for static typing support

    class BaseLLMProvider:
        """Typed subset of the runtime BaseLLMProvider for mypy."""

        config: dict[str, object]

        def __init__(self, config: Mapping[str, object] | None = None) -> None: ...

        def generate(
            self, prompt: str, parameters: Mapping[str, object] | None = None
        ) -> str: ...

        def generate_with_context(
            self,
            prompt: str,
            context: list[dict[str, str]],
            parameters: Mapping[str, object] | None = None,
        ) -> str: ...

        def get_embedding(self, text: str) -> list[float]: ...

    class StreamingLLMProvider:
        """Streaming interface subset for typing."""

        async def generate_stream(
            self, prompt: str, parameters: Mapping[str, object] | None = None
        ) -> AsyncIterator[str]: ...

        async def generate_with_context_stream(
            self,
            prompt: str,
            context: list[dict[str, str]],
            parameters: Mapping[str, object] | None = None,
        ) -> AsyncIterator[str]: ...

else:
    from devsynth.application.llm.providers import BaseLLMProvider
    from devsynth.domain.interfaces.llm import StreamingLLMProvider

# Create a logger for this module
logger = DevSynthLogger(__name__)
AsyncStrStream = AsyncIterator[str]

DEFAULT_RESPONSE_TEXT = "This is a mock response from the MockLLMAdapter."
DEFAULT_EMBEDDING_VALUES: Sequence[float] = (0.1, 0.2, 0.3, 0.4, 0.5)


def _default_response_templates() -> (
    Sequence[MockResponseTemplate]
):  # pragma: no cover - deterministic default data
    return (
        MockResponseTemplate(key="default", text=DEFAULT_RESPONSE_TEXT),
        MockResponseTemplate(
            key="code_review",
            text=(
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
        ),
    )


def _default_embedding_templates() -> (
    Sequence[MockEmbeddingTemplate]
):  # pragma: no cover - deterministic default data
    return (MockEmbeddingTemplate(key="default", vector=DEFAULT_EMBEDDING_VALUES),)


@dataclass(frozen=True)
class MockResponseTemplate:
    """Typed payload describing how a prompt substring maps to a response."""

    key: str
    text: str


@dataclass(frozen=True)
class MockEmbeddingTemplate:
    """Typed payload describing how a substring maps to an embedding."""

    key: str
    vector: Sequence[float]


def _coerce_float_sequence(values: Sequence[float | int]) -> list[float]:
    """Return a defensive copy of float-compatible values."""

    return [float(value) for value in values]


def chunk_response(response: str, chunk_size: int = 3) -> list[str]:
    """Split a response into whitespace-delimited chunks with trailing spaces."""

    words = response.split()
    return [
        " ".join(words[index : index + chunk_size]) + " "
        for index in range(0, len(words), chunk_size)
    ]


async def stream_chunks(chunks: Sequence[str]) -> AsyncStrStream:
    """Yield each chunk sequentially as an async iterator."""

    for chunk in chunks:
        yield chunk


@dataclass
class MockLLMConfig:
    """Configuration options for :class:`MockLLMAdapter`."""

    default_response: str = DEFAULT_RESPONSE_TEXT
    response_templates: Sequence[MockResponseTemplate] = field(
        default_factory=_default_response_templates
    )
    default_embedding: Sequence[float] = DEFAULT_EMBEDDING_VALUES
    embedding_templates: Sequence[MockEmbeddingTemplate] = field(
        default_factory=_default_embedding_templates
    )

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, object]
    ) -> (
        MockLLMConfig
    ):  # pragma: no cover - configuration parsing exercised indirectly
        """Build a configuration from a mapping while preserving defaults."""

        default_response = str(mapping.get("default_response", DEFAULT_RESPONSE_TEXT))

        response_items = mapping.get("responses")
        response_templates: list[MockResponseTemplate] = []
        if isinstance(response_items, Mapping):
            for key, value in response_items.items():
                if isinstance(key, str) and isinstance(value, str):
                    response_templates.append(MockResponseTemplate(key=key, text=value))

        embedding_items = mapping.get("embeddings")
        embedding_templates: list[MockEmbeddingTemplate] = []
        if isinstance(embedding_items, Mapping):
            for key, value in embedding_items.items():
                if (
                    isinstance(key, str)
                    and isinstance(value, Sequence)
                    and not isinstance(value, (str, bytes))
                ):
                    embedding_templates.append(
                        MockEmbeddingTemplate(
                            key=key, vector=_coerce_float_sequence(value)
                        )
                    )

        default_embedding_values = mapping.get("default_embedding")
        default_embedding: Sequence[float]
        if isinstance(default_embedding_values, Sequence) and not isinstance(
            default_embedding_values, (str, bytes)
        ):
            default_embedding = _coerce_float_sequence(default_embedding_values)
        else:
            default_embedding = DEFAULT_EMBEDDING_VALUES

        resolved_responses: Sequence[MockResponseTemplate]
        if response_templates:
            resolved_responses = tuple(response_templates)
        else:
            resolved_responses = _default_response_templates()

        resolved_embeddings: Sequence[MockEmbeddingTemplate]
        if embedding_templates:
            resolved_embeddings = tuple(embedding_templates)
        else:
            resolved_embeddings = _default_embedding_templates()

        resolved_default_embedding: Sequence[float]
        if default_embedding:
            resolved_default_embedding = tuple(default_embedding)
        else:
            resolved_default_embedding = DEFAULT_EMBEDDING_VALUES

        return cls(
            default_response=default_response,
            response_templates=resolved_responses,
            default_embedding=resolved_default_embedding,
            embedding_templates=resolved_embeddings,
        )

    def to_raw_config(
        self,
    ) -> dict[
        str, object
    ]:  # pragma: no cover - convenience helper for BaseLLMProvider compatibility
        """Expose a dict representation for compatibility with :class:`BaseLLMProvider`."""

        raw: dict[str, object] = {
            "default_response": self.default_response,
            "responses": {
                template.key: template.text for template in self.response_templates
            },
            "default_embedding": list(self.default_embedding),
            "embeddings": {
                template.key: list(template.vector)
                for template in self.embedding_templates
            },
        }
        return raw


class MockLLMAdapter(BaseLLMProvider, StreamingLLMProvider):
    """Mock LLM adapter for testing purposes."""

    def __init__(
        self,
        config: Mapping[str, object] | MockLLMConfig | None = None,
    ) -> None:
        if isinstance(config, MockLLMConfig):
            resolved_config = config
            raw_config = resolved_config.to_raw_config()
        else:
            mapping: Mapping[str, object] = config or {}
            resolved_config = MockLLMConfig.from_mapping(mapping)
            raw_config = dict(mapping)

        super().__init__(
            raw_config if isinstance(raw_config, dict) else dict(raw_config)
        )

        self.config_model: MockLLMConfig = resolved_config
        self.responses: dict[str, str] = {
            template.key: template.text
            for template in resolved_config.response_templates
        }
        self.default_response: str = resolved_config.default_response
        self.embeddings: dict[str, list[float]] = {
            template.key: _coerce_float_sequence(template.vector)
            for template in resolved_config.embedding_templates
        }
        self.default_embedding: list[float] = _coerce_float_sequence(
            resolved_config.default_embedding
        )

    def generate(
        self, prompt: str, parameters: Mapping[str, object] | None = None
    ) -> str:
        """Generate text from a prompt."""
        logger.debug(
            "MockLLMAdapter.generate called with prompt: %s...",
            prompt[:50],
        )

        # Check if the prompt contains a key from the responses dictionary
        for key, response in self.responses.items():
            if key in prompt:
                return response

        return self.default_response

    def generate_with_context(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: Mapping[str, object] | None = None,
    ) -> str:
        """Generate text from a prompt with conversation context."""
        logger.debug(
            "MockLLMAdapter.generate_with_context called with prompt: %s...",
            prompt[:50],
        )

        # For simplicity, we'll just use the same logic as generate
        return self.generate(prompt, parameters)

    def get_embedding(self, text: str) -> list[float]:
        """Get an embedding vector for the given text."""
        logger.debug(
            "MockLLMAdapter.get_embedding called with text: %s...",
            text[:50],
        )

        # Check if the text contains a key from the embeddings dictionary
        for key, embedding in self.embeddings.items():
            if key in text:
                return embedding

        return self.default_embedding

    async def generate_stream(
        self, prompt: str, parameters: Mapping[str, object] | None = None
    ) -> AsyncStrStream:
        """Generate text from a prompt with streaming."""
        logger.debug(
            "MockLLMAdapter.generate_stream called with prompt: %s...",
            prompt[:50],
        )

        response = self.generate(prompt, parameters)
        return stream_chunks(chunk_response(response))

    async def generate_with_context_stream(
        self,
        prompt: str,
        context: list[dict[str, str]],
        parameters: Mapping[str, object] | None = None,
    ) -> AsyncStrStream:
        """Generate text from a prompt with conversation context with streaming."""
        logger.debug(
            "MockLLMAdapter.generate_with_context_stream called with prompt: %s...",
            prompt[:50],
        )

        response = self.generate_with_context(prompt, context, parameters)
        return stream_chunks(chunk_response(response))
