"""Regression tests verifying FastAPI TestClient guards."""

from typing import Any, Callable, cast

import pytest

from tests._typing_utils import ensure_typed_decorator

pytest.importorskip("fastapi")

from fastapi import FastAPI

# Defer fastapi.testclient import to avoid MRO issues during collection
# Import will be done lazily when actually needed by tests
TestClient = None

def _get_testclient():
    """Lazily import TestClient to avoid MRO issues during collection."""
    global TestClient
    if TestClient is None:
        try:
            from fastapi.testclient import TestClient
        except TypeError:
            # Fallback for MRO compatibility issues
            from starlette.testclient import TestClient
    return TestClient

pytestmark = pytest.mark.fast


def test_fastapi_testclient_guard_allows_minimal_request():
    """Ensure a minimal FastAPI app responds through the TestClient."""

    app = FastAPI()

    route = ensure_typed_decorator(
        cast(Callable[[Callable[..., Any]], Any], app.get("/ping"))
    )

    @route
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    client = _get_testclient()(app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
