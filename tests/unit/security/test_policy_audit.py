"""Tests for the policy audit script."""

import sys
from pathlib import Path

import pytest

sys.path.append("scripts")

import policy_audit  # type: ignore


@pytest.mark.fast
def test_audit_detects_violation(tmp_path: Path) -> None:
    """A file with forbidden patterns should be reported."""
    config = tmp_path / "unsafe.cfg"
    config.write_text("password=secret")
    results = policy_audit.audit([config])
    assert results and results[0][0] == config


@pytest.mark.fast
def test_audit_passes_clean_file(tmp_path: Path) -> None:
    """A clean file should yield no findings."""
    config = tmp_path / "safe.cfg"
    config.write_text("value=1")
    assert policy_audit.audit([config]) == []
