"""Focused coverage tests for security/deployment.py missing lines."""

import os
from unittest.mock import patch

import pytest

from devsynth.security.deployment import (
    apply_secure_umask,
    check_required_env_vars,
    harden_runtime,
    require_non_root_user,
)


@pytest.mark.fast
def test_require_non_root_user_when_not_required(monkeypatch):
    """Test require_non_root_user when DEVSYNTH_REQUIRE_NON_ROOT is false."""
    monkeypatch.setenv("DEVSYNTH_REQUIRE_NON_ROOT", "false")

    # Should not raise even if running as root
    with patch("os.geteuid", return_value=0):
        require_non_root_user()  # Should not raise


@pytest.mark.fast
def test_check_required_env_vars_with_missing_vars(monkeypatch):
    """Test check_required_env_vars with missing environment variables."""
    # Clear any existing env vars
    monkeypatch.delenv("TEST_VAR_1", raising=False)
    monkeypatch.delenv("TEST_VAR_2", raising=False)

    with pytest.raises(RuntimeError, match="Missing required environment variables"):
        check_required_env_vars(["TEST_VAR_1", "TEST_VAR_2"])


@pytest.mark.fast
def test_check_required_env_vars_with_all_present(monkeypatch):
    """Test check_required_env_vars when all variables are present."""
    monkeypatch.setenv("TEST_VAR_1", "value1")
    monkeypatch.setenv("TEST_VAR_2", "value2")

    # Should not raise
    check_required_env_vars(["TEST_VAR_1", "TEST_VAR_2"])


@pytest.mark.fast
def test_apply_secure_umask():
    """Test apply_secure_umask returns previous umask."""
    # Save current umask
    current_umask = os.umask(0o022)
    os.umask(current_umask)  # Restore it

    # Test with default
    previous = apply_secure_umask()
    assert isinstance(previous, int)

    # Test with custom value
    previous2 = apply_secure_umask(0o022)
    assert isinstance(previous2, int)


@pytest.mark.fast
def test_harden_runtime_with_required_env(monkeypatch):
    """Test harden_runtime with required environment variables."""
    monkeypatch.setenv("DEVSYNTH_REQUIRE_NON_ROOT", "false")
    monkeypatch.setenv("TEST_REQ_VAR", "present")

    # Should not raise when env var is present
    harden_runtime(required_env=["TEST_REQ_VAR"])


@pytest.mark.fast
def test_harden_runtime_without_required_env(monkeypatch):
    """Test harden_runtime without required environment variables."""
    monkeypatch.setenv("DEVSYNTH_REQUIRE_NON_ROOT", "false")

    # Should not raise when no required env specified
    harden_runtime(required_env=None)
