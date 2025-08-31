import pytest

pytest.importorskip("fastapi")
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from devsynth.api import verify_token


@pytest.fixture
def mock_settings():
    """Mock settings with a test token."""
    with patch("devsynth.api.settings") as mock_settings:
        mock_settings.access_token = "test_token"
        yield mock_settings


@pytest.mark.fast
def test_verify_token_valid_is_valid(mock_settings):
    """Test that verify_token accepts a valid token.

    ReqID: N/A"""
    authorization = "Bearer test_token"
    verify_token(authorization)


@pytest.mark.fast
def test_verify_token_invalid_is_valid(mock_settings):
    """Test that verify_token rejects an invalid token.

    ReqID: N/A"""
    authorization = "Bearer invalid_token"
    with pytest.raises(HTTPException) as excinfo:
        verify_token(authorization)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Unauthorized"


@pytest.mark.fast
def test_verify_token_missing_succeeds(mock_settings):
    """Test that verify_token rejects a missing token.

    ReqID: N/A"""
    authorization = None
    with pytest.raises(HTTPException) as excinfo:
        verify_token(authorization)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Unauthorized"


@pytest.mark.fast
def test_verify_token_wrong_format_succeeds(mock_settings):
    """Test that verify_token rejects a token in the wrong format.

    ReqID: N/A"""
    authorization = "test_token"
    with pytest.raises(HTTPException) as excinfo:
        verify_token(authorization)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Unauthorized"


@pytest.mark.fast
def test_verify_token_access_control_disabled_succeeds(mock_settings):
    """Test that verify_token accepts any token when access control is disabled.

    ReqID: N/A"""
    mock_settings.access_token = ""
    verify_token("Bearer any_token")
    verify_token("any_token")
    verify_token(None)
