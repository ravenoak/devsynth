"""Regression tests for FastAPI/Starlette compatibility."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")

pytestmark = pytest.mark.fast


def test_testclient_imports_without_mro_conflict() -> None:
    """ReqID: FASTAPI-STARLETTE-0001
    Ensure TestClient import avoids the Starlette MRO regression."""

    from fastapi.testclient import TestClient

    app = fastapi.FastAPI()

    client = TestClient(app)

    response = client.get("/")
    # The default root route returns a 404; status 404 confirms the client works.
    assert response.status_code == 404
