"""Regression tests verifying FastAPI TestClient guards."""

from typing import Any, Callable, cast

import pytest

from tests._typing_utils import ensure_typed_decorator

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")

from fastapi import FastAPI
from fastapi.testclient import TestClient

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

    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
