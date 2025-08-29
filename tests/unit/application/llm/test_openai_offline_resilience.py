import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from devsynth.application.llm.openai_provider import (
    OpenAIConnectionError,
    OpenAIModelError,
    OpenAIProvider,
)


@pytest.mark.fast
def test_generate_success_offline(monkeypatch):
    # Arrange: stub OpenAI client chat.completions.create
    fake_response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))])

    with patch("devsynth.application.llm.openai_provider.OpenAI") as MockOpenAI, \
         patch("devsynth.application.llm.openai_provider.AsyncOpenAI") as MockAsyncOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = fake_response
        MockOpenAI.return_value = mock_client
        MockAsyncOpenAI.return_value = MagicMock()

        provider = OpenAIProvider({"model": "gpt-4o-mini"})
        out = provider.generate("hi")
        assert out == "hello"
        mock_client.chat.completions.create.assert_called()


@pytest.mark.fast
def test_generate_timeout_retries_and_raises_connection_error(monkeypatch):
    with patch("devsynth.application.llm.openai_provider.OpenAI") as MockOpenAI, \
         patch("devsynth.application.llm.openai_provider.AsyncOpenAI") as MockAsyncOpenAI:
        mock_client = MagicMock()
        # Simulate network/timeout error repeatedly
        mock_client.chat.completions.create.side_effect = TimeoutError("boom")
        MockOpenAI.return_value = mock_client
        MockAsyncOpenAI.return_value = MagicMock()

        provider = OpenAIProvider({"model": "gpt-4o-mini", "max_retries": 2, "initial_backoff": 0.0, "max_backoff": 0.0})
        with pytest.raises(OpenAIConnectionError):
            provider.generate("hi")


@pytest.mark.fast
@pytest.mark.asyncio
async def test_generate_stream_yields_tokens_offline(monkeypatch):
    class DummyStream:
        def __iter__(self):
            return iter([
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="A"))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="B"))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]),
            ])

    with patch("devsynth.application.llm.openai_provider.OpenAI") as MockOpenAI, \
         patch("devsynth.application.llm.openai_provider.AsyncOpenAI") as MockAsyncOpenAI:
        mock_client = MagicMock()
        # Provider calls client.chat.completions.create with stream=True and expects iterable chunks
        mock_client.chat.completions.create.return_value = DummyStream()
        MockOpenAI.return_value = mock_client
        MockAsyncOpenAI.return_value = MagicMock()

        provider = OpenAIProvider({"model": "gpt-4o-mini"})
        out = []
        async for chunk in provider.generate_stream("hi"):
            out.append(chunk)
        assert out == ["A", "B"]


@pytest.mark.fast
def test_generate_invalid_response_raises_model_error(monkeypatch):
    # Return an object without expected choices/message/content
    fake_bad = SimpleNamespace(choices=[SimpleNamespace(message=None)])

    with patch("devsynth.application.llm.openai_provider.OpenAI") as MockOpenAI, \
         patch("devsynth.application.llm.openai_provider.AsyncOpenAI") as MockAsyncOpenAI:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = fake_bad
        MockOpenAI.return_value = mock_client
        MockAsyncOpenAI.return_value = MagicMock()

        provider = OpenAIProvider({"model": "gpt-4o-mini"})
        with pytest.raises(OpenAIModelError):
            provider.generate("hi")
