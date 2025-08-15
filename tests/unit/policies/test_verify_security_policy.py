"""Tests for ``scripts/verify_security_policy.py``."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3] / "scripts"))

import verify_security_policy as vsp  # type: ignore


@pytest.mark.fast
def test_passes_when_all_variables_set(monkeypatch, capsys) -> None:
    """Script returns 0 when all required variables are set correctly."""
    for name in vsp.REQUIRED_TRUE:
        monkeypatch.setenv(name, "true")
    for name in vsp.REQUIRED_NONEMPTY:
        monkeypatch.setenv(name, "token")
    assert vsp.main() == 0
    captured = capsys.readouterr()
    assert "Security policy checks passed." in captured.out


@pytest.mark.fast
def test_fails_when_variable_missing(monkeypatch, capsys) -> None:
    """Script returns 1 and lists violations when variables are missing."""
    for name in vsp.REQUIRED_TRUE + vsp.REQUIRED_NONEMPTY:
        monkeypatch.delenv(name, raising=False)
    assert vsp.main() == 1
    captured = capsys.readouterr()
    assert "Security policy violations:" in captured.out
    assert "DEVSYNTH_AUTHENTICATION_ENABLED" in captured.out
