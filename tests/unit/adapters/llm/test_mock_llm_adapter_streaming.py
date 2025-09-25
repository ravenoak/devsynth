"""Streaming behaviour tests for MockLLMAdapter."""

from __future__ import annotations

import pytest

from devsynth.adapters.llm.mock_llm_adapter import MockLLMAdapter


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
