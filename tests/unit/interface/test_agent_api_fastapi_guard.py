"""Regression tests verifying FastAPI TestClient guards."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.fast


def test_fastapi_testclient_guard_allows_minimal_request():
    """Ensure a minimal FastAPI app responds through the TestClient."""

    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
