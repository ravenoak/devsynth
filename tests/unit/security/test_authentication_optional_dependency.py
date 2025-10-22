"""Tests for the optional Argon2 dependency in authentication utilities."""

from __future__ import annotations

import importlib
import sys

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.fast]


def test_authentication_handles_missing_argon2(monkeypatch: pytest.MonkeyPatch) -> None:
    """Module loads without Argon2 and surfaces actionable guidance when required."""

    monkeypatch.setitem(sys.modules, "argon2", None)
    monkeypatch.setitem(sys.modules, "argon2.exceptions", None)
    monkeypatch.setenv("DEVSYNTH_AUTHENTICATION_ENABLED", "true")
    sys.modules.pop("devsynth.security.authentication", None)

    auth_module = importlib.import_module("devsynth.security.authentication")
    assert hasattr(auth_module, "authenticate")

    with pytest.raises(ImportError) as excinfo:
        auth_module.authenticate("alice", "password", {"alice": "hash"})

    message = str(excinfo.value)
    assert "Argon2 support is required" in message
    assert "security" in message

    monkeypatch.setenv("DEVSYNTH_AUTHENTICATION_ENABLED", "false")
    assert auth_module.authenticate("alice", "password", {"alice": "hash"}) is True
