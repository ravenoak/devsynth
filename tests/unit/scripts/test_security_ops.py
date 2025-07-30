import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append('scripts')

from security_incident_response import collect_logs, run_audit  # type: ignore
from vulnerability_management import list_outdated, apply_updates  # type: ignore


def test_collect_logs_missing_directory(tmp_path, capsys, monkeypatch):
    """collect_logs should warn when LOG_DIR is absent."""
    monkeypatch.setattr('security_incident_response.LOG_DIR', tmp_path / 'logs')
    collect_logs(tmp_path / 'out')
    captured = capsys.readouterr()
    assert 'No logs directory' in captured.out


@patch('security_incident_response.subprocess.check_call')
def test_run_audit_calls_security_audit(mock_call):
    """run_audit should invoke the security audit script."""
    run_audit()
    mock_call.assert_called_once_with(['python', 'scripts/security_audit.py'])


@patch('vulnerability_management.subprocess.check_call')
def test_list_outdated_runs_poetry(mock_call):
    """list_outdated should invoke poetry show --outdated."""
    list_outdated()
    mock_call.assert_called_once_with(['poetry', 'show', '--outdated'])


@patch('vulnerability_management.subprocess.check_call')
def test_apply_updates_runs_poetry(mock_call):
    """apply_updates should invoke poetry update."""
    apply_updates()
    mock_call.assert_called_once_with(['poetry', 'update'])
