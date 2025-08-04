"""Tests for the deprecated security audit wrapper."""

import sys
from unittest.mock import patch

sys.path.append("scripts")

import security_audit  # type: ignore


@patch("security_audit.subprocess.run")
def test_main_invokes_cli(mock_run) -> None:
    """The wrapper should invoke the devsynth CLI without flags."""
    security_audit.main([])
    mock_run.assert_called_once_with(["devsynth", "security-audit"], check=True)


@patch("security_audit.subprocess.run")
def test_main_passes_flags(mock_run) -> None:
    """Flags should be forwarded to the CLI command."""
    security_audit.main(
        ["--skip-bandit", "--skip-safety", "--skip-secrets", "--skip-owasp"]
    )
    mock_run.assert_called_once_with(
        [
            "devsynth",
            "security-audit",
            "--skip-static",
            "--skip-safety",
            "--skip-secrets",
            "--skip-owasp",
        ],
        check=True,
    )

