import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock

from devsynth.api import verify_token


@pytest.fixture
def mock_settings():
    """Mock settings with a test token."""
    with patch("devsynth.api.settings") as mock_settings:
        mock_settings.access_token = "test_token"
        yield mock_settings


def test_verify_token_valid(mock_settings):
    """Test that verify_token accepts a valid token."""
    # Valid token in the correct format
    authorization = "Bearer test_token"
    # Should not raise an exception
    verify_token(authorization)


def test_verify_token_invalid(mock_settings):
    """Test that verify_token rejects an invalid token."""
    # Invalid token
    authorization = "Bearer invalid_token"
    # Should raise an HTTPException with 401 status code
    with pytest.raises(HTTPException) as excinfo:
        verify_token(authorization)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Unauthorized"


def test_verify_token_missing(mock_settings):
    """Test that verify_token rejects a missing token."""
    # No token provided
    authorization = None
    # Should raise an HTTPException with 401 status code
    with pytest.raises(HTTPException) as excinfo:
        verify_token(authorization)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Unauthorized"


def test_verify_token_wrong_format(mock_settings):
    """Test that verify_token rejects a token in the wrong format."""
    # Token in wrong format (missing 'Bearer' prefix)
    authorization = "test_token"
    # Should raise an HTTPException with 401 status code
    with pytest.raises(HTTPException) as excinfo:
        verify_token(authorization)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Unauthorized"


def test_verify_token_access_control_disabled(mock_settings):
    """Test that verify_token accepts any token when access control is disabled."""
    # Disable access control by setting access_token to empty string
    mock_settings.access_token = ""
    
    # Any token or no token should be accepted
    verify_token("Bearer any_token")
    verify_token("any_token")
    verify_token(None)