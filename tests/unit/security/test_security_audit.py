"""Tests for the security audit script."""

import sys
from unittest.mock import patch

sys.path.append("scripts")

import security_audit  # type: ignore


@patch("security_audit.run_safety")
@patch("security_audit.run_bandit")
def test_main_runs_all_checks(mock_bandit, mock_safety) -> None:
    """The script should execute Bandit and Safety by default."""
    security_audit.main([])
    mock_bandit.assert_called_once()
    mock_safety.assert_called_once()


@patch("security_audit.run_safety")
@patch("security_audit.run_bandit")
def test_main_respects_skip_flags(mock_bandit, mock_safety) -> None:
    """Skip flags should prevent running the associated tools."""
    security_audit.main(["--skip-bandit", "--skip-safety"])
    mock_bandit.assert_not_called()
    mock_safety.assert_not_called()
