"""
Optional live LM Studio smoke tests.

These tests are strictly opt-in and will only run when the resource is explicitly
enabled via environment flags and an endpoint is provided.
They must not perform any import-time network calls.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import pytest

requires_lmstudio = pytest.mark.requires_resource("lmstudio")


@pytest.mark.medium
@requires_lmstudio
def test_lmstudio_models_ping_live_smoke():
    """Ping LM Studio /v1/models with a very short timeout and minimal schema checks."""
    import httpx

    endpoint = os.environ.get("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")
    # Allow override of path prefix
    url = endpoint.rstrip("/") + "/v1/models"

    with httpx.Client(timeout=3.0) as client:
        resp = client.get(url)
        assert (
            resp.status_code == 200
        ), f"unexpected status: {resp.status_code}, body={resp.text[:200]}"
        data: Dict[str, Any] = resp.json()
        # Expect either {"data": [...]} (OpenAI-like) or a list-based structure; accept subset
        if isinstance(data, dict) and "data" in data:
            assert isinstance(data["data"], list)
        else:
            # Fallback: ensure it's a list or dict with models-like content
            assert isinstance(data, (list, dict))
