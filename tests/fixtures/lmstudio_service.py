from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator, Callable, Generator
from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from ._lmstudio_types import (
    LMStudioChatCompletion,
    LMStudioChatMessage,
    LMStudioChatPayload,
    LMStudioDownloadedModel,
    LMStudioModule,
    LMStudioSyncAPI,
)

_IMPORTORSKIP: Callable[[str], ModuleType] = cast(
    Callable[[str], ModuleType], getattr(pytest, "importorskip")
)

if TYPE_CHECKING:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.testclient import TestClient
else:
    # Defer FastAPI imports to avoid MRO issues during test collection
    # These will only be imported when actually needed by tests
    FastAPI = None
    JSONResponse = None
    StreamingResponse = None
    TestClient = None


class _ChatDelta(TypedDict, total=False):
    content: str


class _ChatChoice(TypedDict):
    delta: _ChatDelta


class _ChatCompletionStreamChunk(TypedDict):
    choices: list[_ChatChoice]


class _EmbeddingDatum(TypedDict):
    embedding: list[float]


class _EmbeddingResponse(TypedDict):
    data: list[_EmbeddingDatum]


@dataclass
class LMStudioMockServer:
    """In-memory FastAPI server emulating the LM Studio HTTP API."""

    base_url: str
    fail: bool = False
    status_code: int = 500

    def trigger_error(self, status_code: int = 500) -> None:
        """Make subsequent requests return an HTTP error."""
        self.fail = True
        self.status_code = status_code

    def reset(self) -> None:
        """Reset error state."""
        self.fail = False
        self.status_code = 500


@pytest.fixture
def lmstudio_service(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[LMStudioMockServer]:
    """Provide a mocked LM Studio HTTP API with streaming responses.

    Skips unless ``DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE`` is truthy and the
    :mod:`lmstudio` package is installed.
    """

    if os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false").lower() not in (
        "1",
        "true",
        "yes",
    ):
        pytest.skip("LMStudio service not available")

    lmstudio = cast(LMStudioModule, _IMPORTORSKIP("lmstudio"))

    # Lazy import FastAPI classes to avoid MRO issues during collection
    if FastAPI is None:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse, StreamingResponse
        from fastapi.testclient import TestClient

    app = FastAPI()
    server = LMStudioMockServer(base_url="")

    async def list_models() -> JSONResponse | dict[str, object]:
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )
        return {"data": [{"id": "test-model", "object": "model"}]}

    async def chat_completions(
        payload: dict[str, object],
    ) -> StreamingResponse | JSONResponse:
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )

        tokens = ["This", " is", " a", " test", " response"]

        async def event_stream() -> AsyncIterator[str]:
            for token in tokens:
                data = {"choices": [{"delta": {"content": token}}]}
                yield f"data: {json.dumps(data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    async def embeddings(
        payload: dict[str, object],
    ) -> JSONResponse | dict[str, object]:
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )
        return {"data": [{"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}]}

    app.get("/v1/models")(list_models)
    app.post("/v1/chat/completions")(chat_completions)
    app.post("/v1/embeddings")(embeddings)

    # Lazy import TestClient to avoid MRO issues during collection
    if TestClient is None:
        from fastapi.testclient import TestClient

    client = TestClient(app)
    server.base_url = str(client.base_url)

    DEFAULT_TIMEOUT = float(os.environ.get("DEVSYNTH_TEST_HTTP_TIMEOUT", "0.5"))

    def _post_stream(path: str, json_payload: dict[str, object]) -> str:
        with client.stream(
            "POST", path, json=json_payload, timeout=DEFAULT_TIMEOUT
        ) as response:
            if response.status_code >= 400:
                error_payload = response.json()
                error_message = "error"
                if isinstance(error_payload, dict):
                    maybe_error = error_payload.get("error")
                    if isinstance(maybe_error, str):
                        error_message = maybe_error
                raise Exception(error_message)
            content = ""
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                if raw_line.startswith("data: "):
                    data = raw_line[6:]
                    if data == "[DONE]":
                        break
                    parsed = cast(_ChatCompletionStreamChunk, json.loads(data))
                    token = ""
                    if parsed["choices"]:
                        delta = parsed["choices"][0]["delta"]
                        token = delta.get("content", "")
                    content += token
            return content

    class MockLLM:
        def __init__(self, model: str):
            self.model = model

        def complete(
            self, prompt: str, config: dict[str, object] | None = None
        ) -> LMStudioChatCompletion:
            message: LMStudioChatMessage = {"role": "user", "content": prompt}
            text = _post_stream(
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [message],
                },
            )
            return LMStudioChatCompletion(content=text)

        def respond(
            self,
            payload: LMStudioChatPayload,
            config: dict[str, object] | None = None,
        ) -> LMStudioChatCompletion:
            text = _post_stream(
                "/v1/chat/completions",
                {"model": self.model, "messages": payload["messages"]},
            )
            return LMStudioChatCompletion(content=text)

    class MockEmbeddingModel:
        def __init__(self, model: str):
            self.model = model

        def embed(self, text: str) -> list[float]:
            response = client.post(
                "/v1/embeddings",
                json={"model": self.model, "input": text},
                timeout=DEFAULT_TIMEOUT,
            )
            if response.status_code >= 400:
                error_payload = response.json()
                error_message = "error"
                if isinstance(error_payload, dict):
                    maybe_error = error_payload.get("error")
                    if isinstance(maybe_error, str):
                        error_message = maybe_error
                raise Exception(error_message)
            embedding_response = cast(_EmbeddingResponse, response.json())
            return embedding_response["data"][0]["embedding"]

    class MockSyncAPI:
        def configure_default_client(self, host: str) -> None:  # pragma: no cover
            return None

        def list_downloaded_models(self, kind: str) -> list[LMStudioDownloadedModel]:
            return [
                LMStudioDownloadedModel(
                    model_key="test-model", display_name="Test Model"
                )
            ]

        def _reset_default_client(self) -> None:  # pragma: no cover
            return None

    def _mock_llm(model: str) -> MockLLM:
        return MockLLM(model)

    def _mock_embedding_model(model: str) -> MockEmbeddingModel:
        return MockEmbeddingModel(model)

    sync_api_mock: LMStudioSyncAPI = MockSyncAPI()

    monkeypatch.setattr(lmstudio, "llm", _mock_llm, raising=False)
    monkeypatch.setattr(
        lmstudio, "embedding_model", _mock_embedding_model, raising=False
    )
    monkeypatch.setattr(lmstudio, "sync_api", sync_api_mock, raising=False)

    try:
        yield server
    finally:
        server.reset()
