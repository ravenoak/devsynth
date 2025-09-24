import types

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")
pytest.skip("requires FastAPI test client", allow_module_level=True)
from fastapi import HTTPException
from fastapi.testclient import TestClient

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
    client = TestClient(api.app)
    response = client.get("/health", headers={"Authorization": "Bearer s3cr3t"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
