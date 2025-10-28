#!/usr/bin/env python3
"""
Mock LM Studio-compatible server for local testing (Tasks 21–26 support).
- Implements a minimal subset of OpenAI-compatible endpoints used by tests:
  - POST /v1/chat/completions
- Returns deterministic dummy responses to avoid network reliance.

Usage:
  poetry run python scripts/mock_lmstudio_server.py --host 127.0.0.1 --port 1234

Environment:
  LM_STUDIO_ENDPOINT can point to http://127.0.0.1:1234 when using this mock.

Notes:
- Keep responses small and fast; this is for test plumbing only.
- Avoid importing heavy optional dependencies outside FastAPI/Uvicorn.
"""
from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

try:
    import uvicorn
    from fastapi import FastAPI
    from pydantic import BaseModel
except Exception as e:  # pragma: no cover - optional for local use only
    raise SystemExit(
        "FastAPI and uvicorn are required to run the mock LM Studio server.\n"
        "Install them with: poetry add fastapi uvicorn --group dev"
    ) from e

app = FastAPI(title="Mock LM Studio", version="0.1.0")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest) -> dict[str, Any]:
    # Return deterministic content expected by tests
    reply = "This is a test response"
    return {
        "id": "chatcmpl-mock-123",
        "object": "chat.completion",
        "created": 0,
        "model": req.model or "mock-lmstudio",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": len(reply.split()),
            "total_tokens": 0,
        },
    }


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Run mock LM Studio server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1234)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":  # pragma: no cover
    main()
