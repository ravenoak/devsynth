"""Tests for the security audit script."""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.append("scripts")

import security_audit  # type: ignore


@patch("security_audit.audit.main")
@patch("security_audit.verify_security_policy.main", return_value=0)
@patch("security_audit.require_pre_deploy_checks")
@pytest.mark.fast
def test_run_executes_policy_and_audit(
    mock_pre: MagicMock, mock_policy: MagicMock, mock_audit: MagicMock
) -> None:
    """The script should validate flags and run dependency checks."""
    security_audit.run([])
    mock_pre.assert_called_once_with()
    mock_policy.assert_called_once_with()
    mock_audit.assert_called_once_with([])


@patch("security_audit.audit.main")
@patch("security_audit.verify_security_policy.main", return_value=1)
@patch("security_audit.require_pre_deploy_checks")
@pytest.mark.fast
def test_run_raises_on_policy_failure(
    mock_pre: MagicMock, mock_policy: MagicMock, mock_audit: MagicMock
) -> None:
    """A non-zero policy result should raise an error."""
    with pytest.raises(subprocess.CalledProcessError):
        security_audit.run([])
