"""Tests for security audit environment variable checks."""

import sys

import pytest

sys.path.append("scripts")

from security_audit import check_required_env  # type: ignore


def test_check_required_env_missing(monkeypatch):
    """check_required_env should raise when required variables are absent."""
    monkeypatch.delenv("DEVSYNTH_ACCESS_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        check_required_env()


def test_check_required_env_present(monkeypatch):
    """check_required_env should pass when variables are set."""
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "token")
    check_required_env()
