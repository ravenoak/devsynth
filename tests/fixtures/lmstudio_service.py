from __future__ import annotations

import json
import types
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.testclient import TestClient


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
def lmstudio_service(monkeypatch) -> LMStudioMockServer:
    """Provide a mocked LM Studio HTTP API with streaming responses."""

    lmstudio = pytest.importorskip("lmstudio")

    app = FastAPI()
    server = LMStudioMockServer(base_url="")

    @app.get("/v1/models")
    async def list_models() -> Dict[str, Any]:
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )
        return {"data": [{"id": "test-model", "object": "model"}]}

    @app.post("/v1/chat/completions")
    async def chat_completions(payload: Dict[str, Any]):
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )

        tokens = ["This", " is", " a", " test"]

        async def event_stream():
            for token in tokens:
                data = {"choices": [{"delta": {"content": token}}]}
                yield f"data: {json.dumps(data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.post("/v1/embeddings")
    async def embeddings(payload: Dict[str, Any]):
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )
        return {"data": [{"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}]}

    client = TestClient(app)
    server.base_url = str(client.base_url)

    def _post_stream(path: str, json_payload: Dict[str, Any]) -> str:
        with client.stream("POST", path, json=json_payload) as response:
            if response.status_code >= 400:
                raise Exception(response.json().get("error", "error"))
            content = ""
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    token = json.loads(data)["choices"][0]["delta"].get("content", "")
                    content += token
            return content

    class MockLLM:
        def __init__(self, model: str):
            self.model = model

        def complete(self, prompt: str, config: Dict[str, Any] | None = None):
            text = _post_stream(
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            return types.SimpleNamespace(content=text)

        def respond(
            self, payload: Dict[str, Any], config: Dict[str, Any] | None = None
        ):
            text = _post_stream(
                "/v1/chat/completions",
                {"model": self.model, "messages": payload["messages"]},
            )
            return types.SimpleNamespace(content=text)

    class MockEmbeddingModel:
        def __init__(self, model: str):
            self.model = model

        def embed(self, text: str) -> List[float]:
            response = client.post(
                "/v1/embeddings", json={"model": self.model, "input": text}
            )
            if response.status_code >= 400:
                raise Exception(response.json().get("error", "error"))
            return response.json()["data"][0]["embedding"]

    class MockSyncAPI:
        def configure_default_client(self, host: str) -> None:  # pragma: no cover
            return None

        def list_downloaded_models(self, kind: str) -> List[Any]:
            return [
                types.SimpleNamespace(model_key="test-model", display_name="Test Model")
            ]

        def _reset_default_client(self) -> None:  # pragma: no cover
            return None

    monkeypatch.setattr(lmstudio, "llm", lambda model: MockLLM(model), raising=False)
    monkeypatch.setattr(
        lmstudio,
        "embedding_model",
        lambda model: MockEmbeddingModel(model),
        raising=False,
    )
    monkeypatch.setattr(lmstudio, "sync_api", MockSyncAPI(), raising=False)

    try:
        yield server
    finally:
        server.reset()
