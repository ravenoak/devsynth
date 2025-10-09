"""Streaming behaviour tests for MockLLMAdapter."""

from __future__ import annotations

import sys
import types
from collections.abc import AsyncIterator

import pytest

# Provide lightweight stubs so importing MockLLMAdapter avoids heavy runtime imports.
if "devsynth.application.llm.providers" not in sys.modules:
    providers_module = types.ModuleType("devsynth.application.llm.providers")

    class _StubBaseLLMProvider:
        def __init__(self, config: dict[str, object] | None = None) -> None:
            self.config = dict(config or {})

    providers_module.BaseLLMProvider = _StubBaseLLMProvider  # type: ignore[attr-defined]
    parent_pkg = sys.modules.setdefault(
        "devsynth.application.llm", types.ModuleType("devsynth.application.llm")
    )
    setattr(parent_pkg, "providers", providers_module)
    sys.modules["devsynth.application.llm.providers"] = providers_module

if "devsynth.domain.interfaces.llm" not in sys.modules:
    interfaces_module = types.ModuleType("devsynth.domain.interfaces.llm")

    class _StubStreamingLLMProvider:
        pass

    class _StubLLMProvider:
        pass

    class _StubLLMProviderFactory:
        pass

    interfaces_module.StreamingLLMProvider = _StubStreamingLLMProvider  # type: ignore[attr-defined]
    interfaces_module.LLMProvider = _StubLLMProvider  # type: ignore[attr-defined]
    interfaces_module.LLMProviderFactory = _StubLLMProviderFactory  # type: ignore[attr-defined]
    sys.modules["devsynth.domain.interfaces.llm"] = interfaces_module

from devsynth.adapters.llm.mock_llm_adapter import (
    MockLLMAdapter,
    chunk_response,
    stream_chunks,
)


@pytest.mark.fast
@pytest.mark.asyncio
async def test_generate_stream_returns_chunks():
    """Mock adapter should stream chunked responses when awaited."""
    adapter = MockLLMAdapter()

    stream = await adapter.generate_stream("default prompt")

    chunks: list[str] = []
    async for chunk in stream:
        chunks.append(chunk.strip())

    assembled = " ".join(chunks).strip()
    assert len(chunks) > 1
    assert assembled.startswith("This is a mock response")


@pytest.mark.fast
@pytest.mark.asyncio
async def test_generate_with_context_stream_returns_chunks():
    """Mock adapter should stream chunked responses with context."""
    adapter = MockLLMAdapter()

    context = [{"role": "system", "content": "context"}]
    expected = adapter.generate_with_context("prompt", context)

    stream = await adapter.generate_with_context_stream("prompt", context)

    chunks = []
    async for chunk in stream:
        chunks.append(chunk.strip())

    assembled = " ".join(chunks).strip()
    assert len(chunks) > 1
    assert assembled == expected


@pytest.mark.fast
def test_chunk_response_helper_respects_chunk_size() -> None:
    """Typed chunk helper should preserve ordering and trailing spacing."""

    chunks = chunk_response("one two three four five", chunk_size=2)

    assert chunks == ["one two ", "three four ", "five "]


@pytest.mark.fast
@pytest.mark.asyncio
async def test_stream_chunks_yields_all_segments() -> None:
    """The async helper should expose an AsyncIterator[str] stream."""

    segments = ["alpha ", "beta "]
    stream = stream_chunks(segments)

    assert isinstance(stream, AsyncIterator)

    collected: list[str] = []
    async for chunk in stream:
        collected.append(chunk)

    assert collected == segments
