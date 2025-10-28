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

from devsynth.testing.llm_test_timeouts import TEST_TIMEOUTS

requires_lmstudio = pytest.mark.requires_resource("lmstudio")


@pytest.mark.slow  # Changed from medium due to measured 5.6s response time
@requires_lmstudio
def test_lmstudio_models_ping_live_smoke():
    """Ping LM Studio /v1/models.

    Note: Runs on shared host with LM Studio. Conservative timeout
    accounts for system load. Measured baseline: 3-6s.
    """
    import httpx

    endpoint = os.environ.get("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234")
    # Allow override of path prefix
    url = endpoint.rstrip("/") + "/v1/models"

    with httpx.Client(timeout=TEST_TIMEOUTS.lmstudio_health) as client:
        resp = client.get(url)
        assert (
            resp.status_code == 200
        ), f"unexpected status: {resp.status_code}, body={resp.text[:200]}"
        data: dict[str, Any] = resp.json()
        # Expect either {"data": [...]} (OpenAI-like) or a list-based structure; accept subset
        if isinstance(data, dict) and "data" in data:
            assert isinstance(data["data"], list)
        else:
            # Fallback: ensure it's a list or dict with models-like content
            assert isinstance(data, (list, dict))
