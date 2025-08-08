"""Tests for the dependency safety check script."""

import sys
from unittest.mock import patch

sys.path.append("scripts")

import dependency_safety_check  # type: ignore


@patch("dependency_safety_check.run_safety")
@patch("dependency_safety_check.run_bandit")
def test_main_runs_all_checks(mock_bandit, mock_safety) -> None:
    """The script should execute Bandit and Safety by default."""
    dependency_safety_check.main([])
    mock_bandit.assert_called_once()
    mock_safety.assert_called_once()


@patch("dependency_safety_check.run_safety")
@patch("dependency_safety_check.run_bandit")
def test_main_respects_skip_flags(mock_bandit, mock_safety) -> None:
    """Skip flags should prevent running the associated tools."""
    dependency_safety_check.main(["--skip-bandit", "--skip-safety"])
    mock_bandit.assert_not_called()
    mock_safety.assert_not_called()
