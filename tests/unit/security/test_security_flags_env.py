import os

import pytest

from devsynth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InputSanitizationError,
)
from devsynth.security.authentication import authenticate, hash_password
from devsynth.security.authorization import require_authorization
from devsynth.security.sanitization import validate_safe_input

ACL = {"admin": ["read"], "user": ["read"]}


@pytest.mark.fast
def test_authentication_disabled_allows_any_credentials(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_AUTHENTICATION_ENABLED", "0")
    creds = {"alice": hash_password("secret")}
    assert authenticate("alice", "wrong", creds)


@pytest.mark.fast
def test_authentication_enabled_enforces(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_AUTHENTICATION_ENABLED", "1")
    creds = {"alice": hash_password("secret")}
    with pytest.raises(AuthenticationError):
        authenticate("alice", "bad", creds)


@pytest.mark.fast
def test_authorization_disabled_allows(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_AUTHORIZATION_ENABLED", "false")
    require_authorization(["guest"], "read", ACL)


@pytest.mark.fast
def test_authorization_enabled_enforces(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_AUTHORIZATION_ENABLED", "true")
    with pytest.raises(AuthorizationError):
        require_authorization(["guest"], "read", ACL)


@pytest.mark.fast
def test_sanitization_disabled_no_error(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_SANITIZATION_ENABLED", "0")
    text = "<script>bad</script>"
    assert validate_safe_input(text) == text


@pytest.mark.fast
def test_sanitization_enabled_raises(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_SANITIZATION_ENABLED", "1")
    with pytest.raises(InputSanitizationError):
        validate_safe_input("<script>bad</script>")
