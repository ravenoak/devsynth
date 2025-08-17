from __future__ import annotations

import types
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
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
def lmstudio_stub(monkeypatch) -> LMStudioMockServer:
    """Provide a mocked LM Studio HTTP API and patch the SDK."""

    lmstudio = pytest.importorskip("lmstudio")

    app = FastAPI()
    server = LMStudioMockServer(base_url="")

    @app.get("/v1/models")
    def list_models() -> Dict[str, Any]:
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )
        return {"data": [{"id": "test-model", "object": "model"}]}

    @app.post("/v1/chat/completions")
    def chat_completions(payload: Dict[str, Any]) -> Any:
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )
        return {
            "choices": [
                {"message": {"content": "This is a test response"}},
            ]
        }

    @app.post("/v1/embeddings")
    def embeddings(payload: Dict[str, Any]) -> Any:
        if server.fail:
            return JSONResponse(
                status_code=server.status_code, content={"error": "Internal error"}
            )
        return {"data": [{"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}]}

    client = TestClient(app)
    server.base_url = str(client.base_url)

    def _post(path: str, json_payload: Dict[str, Any]) -> Dict[str, Any]:
        response = client.post(path, json=json_payload)
        if response.status_code >= 400:
            raise Exception(response.json().get("error", "error"))
        return response.json()

    class MockLLM:
        def __init__(self, model: str):
            self.model = model

        def complete(self, prompt: str, config: Dict[str, Any] | None = None) -> Any:
            data = _post(
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            return types.SimpleNamespace(
                content=data["choices"][0]["message"]["content"]
            )

        def respond(
            self, payload: Dict[str, Any], config: Dict[str, Any] | None = None
        ) -> Any:
            data = _post(
                "/v1/chat/completions",
                {"model": self.model, "messages": payload["messages"]},
            )
            return types.SimpleNamespace(
                content=data["choices"][0]["message"]["content"]
            )

    class MockEmbeddingModel:
        def __init__(self, model: str):
            self.model = model

        def embed(self, text: str) -> List[float]:
            data = _post("/v1/embeddings", {"model": self.model, "input": text})
            return data["data"][0]["embedding"]

    class MockSyncAPI:
        def configure_default_client(
            self, host: str
        ) -> None:  # pragma: no cover - noop
            return None

        def list_downloaded_models(self, kind: str) -> List[Any]:
            return [
                types.SimpleNamespace(model_key="test-model", display_name="Test Model")
            ]

        def _reset_default_client(self) -> None:  # pragma: no cover - noop
            return None

    monkeypatch.setattr(lmstudio, "llm", lambda model: MockLLM(model))
    monkeypatch.setattr(
        lmstudio, "embedding_model", lambda model: MockEmbeddingModel(model)
    )
    monkeypatch.setattr(lmstudio, "sync_api", MockSyncAPI())

    try:
        yield server
    finally:
        server.reset()


def test_lmstudio_stub_fixture_returns_base_url(lmstudio_stub):
    """Ensure the stub fixture provides a usable base URL."""
    assert lmstudio_stub.base_url
