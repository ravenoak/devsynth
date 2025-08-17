"""Tests for the security audit script."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append("scripts")

import security_audit  # type: ignore


@patch("security_audit.audit.run_bandit")
@patch("security_audit.audit.run_safety")
@patch("security_audit.verify_security_policy.main", return_value=0)
@patch("security_audit.require_pre_deploy_checks")
@pytest.mark.fast
def test_run_executes_checks(
    mock_pre: MagicMock,
    mock_policy: MagicMock,
    mock_safety: MagicMock,
    mock_bandit: MagicMock,
) -> None:
    """The script should validate flags and run Bandit and Safety."""
    security_audit.run([])
    mock_pre.assert_called_once_with()
    mock_policy.assert_called_once_with()
    mock_bandit.assert_called_once_with()
    mock_safety.assert_called_once_with()


@patch("security_audit.audit.run_bandit")
@patch("security_audit.audit.run_safety")
@patch("security_audit.verify_security_policy.main", return_value=1)
@patch("security_audit.require_pre_deploy_checks")
@pytest.mark.fast
def test_run_raises_on_policy_failure(
    mock_pre: MagicMock,
    mock_policy: MagicMock,
    mock_safety: MagicMock,
    mock_bandit: MagicMock,
) -> None:
    """A non-zero policy result should raise an error."""
    with pytest.raises(subprocess.CalledProcessError):
        security_audit.run([])


@patch("security_audit.audit.run_bandit")
@patch("security_audit.audit.run_safety")
@patch("security_audit.verify_security_policy.main", return_value=0)
@patch("security_audit.require_pre_deploy_checks")
@pytest.mark.fast
def test_report_writes_results(
    mock_pre: MagicMock,
    mock_policy: MagicMock,
    mock_safety: MagicMock,
    mock_bandit: MagicMock,
    tmp_path: Path,
) -> None:
    """Running with --report should write a JSON summary."""
    report = tmp_path / "audit.json"
    security_audit.run(["--report", str(report)])
    data = json.loads(report.read_text())
    assert data == {"bandit": "passed", "safety": "passed"}


@patch(
    "security_audit.audit.run_bandit",
    side_effect=subprocess.CalledProcessError(1, "bandit"),
)
@patch("security_audit.verify_security_policy.main", return_value=0)
@patch("security_audit.require_pre_deploy_checks")
@pytest.mark.fast
def test_report_records_failure(
    mock_pre: MagicMock,
    mock_policy: MagicMock,
    mock_bandit: MagicMock,
    tmp_path: Path,
) -> None:
    """Failed checks should be noted in the report."""
    report = tmp_path / "audit.json"
    with pytest.raises(subprocess.CalledProcessError):
        security_audit.run(["--report", str(report)])
    data = json.loads(report.read_text())
    assert data == {"bandit": "failed", "safety": "skipped"}
