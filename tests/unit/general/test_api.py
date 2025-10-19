import types

import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException

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


from devsynth import api


@pytest.mark.fast
def test_verify_token_rejects_invalid_token(monkeypatch):
    """Verify incorrect token triggers unauthorized error.

    ReqID: FR-74"""
    monkeypatch.setattr(api, "settings", types.SimpleNamespace(access_token="s3cr3t"))
    with pytest.raises(HTTPException):
        api.verify_token("Bearer wrong")


@pytest.mark.fast
def test_health_endpoint_accepts_valid_token(monkeypatch):
    """Health endpoint returns ok when authorized.

    ReqID: FR-74"""
    monkeypatch.setattr(api, "settings", types.SimpleNamespace(access_token="s3cr3t"))
    client = _get_testclient()(api.app)
    response = client.get("/health", headers={"Authorization": "Bearer s3cr3t"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
