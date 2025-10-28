"""
Optional live OpenAI smoke tests.

These tests are strictly opt-in and will only run when the resource is explicitly
enabled via environment flags and a valid API key is present.
They must not perform any import-time network calls.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import pytest

requires_openai = pytest.mark.requires_resource("openai")


@pytest.mark.medium
@requires_openai
def test_openai_chat_completion_live_smoke():
    """Minimal live prompt against OpenAI with a very short timeout.

    - Deterministic, short prompt
    - Explicit model via OPENAI_MODEL env var (caller responsibility)
    - Short timeout to fail fast if misconfigured
    - Assert on basic shape only
    """
    import httpx

    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    assert api_key, "OPENAI_API_KEY must be set for live OpenAI smoke test"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Say the word 'ok'."},
        ],
        "max_tokens": 5,
        "temperature": 0,
    }

    with httpx.Client(timeout=5.0) as client:
        resp = client.post(
            "https://api.openai.com/v1/chat/completions", json=payload, headers=headers
        )
        assert (
            resp.status_code == 200
        ), f"unexpected status: {resp.status_code}, body={resp.text[:200]}"
        data = resp.json()
        assert "choices" in data and isinstance(data["choices"], list)
        assert len(data["choices"]) >= 1
        # Basic schema checks
        first = data["choices"][0]
        assert "message" in first and "content" in first["message"]


@pytest.mark.medium
@requires_openai
def test_openai_embeddings_live_smoke():
    """Minimal live embeddings request with explicit model and short timeout.
    Asserts on the basic shape only.
    """
    import httpx

    api_key = os.environ.get("OPENAI_API_KEY")
    emb_model = os.environ.get(
        "OPENAI_EMBEDDINGS_MODEL",
        os.environ.get("OPENAI_MODEL", "text-embedding-3-small"),
    )
    assert api_key, "OPENAI_API_KEY must be set for live OpenAI embeddings smoke test"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": emb_model, "input": ["tiny"]}

    with httpx.Client(timeout=5.0) as client:
        resp = client.post(
            "https://api.openai.com/v1/embeddings", json=payload, headers=headers
        )
        assert (
            resp.status_code == 200
        ), f"unexpected status: {resp.status_code}, body={resp.text[:200]}"
        data = resp.json()
        assert "data" in data and isinstance(data["data"], list)
        assert len(data["data"]) >= 1
        vec = data["data"][0]
        assert "embedding" in vec and isinstance(vec["embedding"], list)
