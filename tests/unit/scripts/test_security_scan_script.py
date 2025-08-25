"""Smoke tests for scripts/security/security_scan.py. ReqID: SEC-01

Ensures the security scan script behaves gracefully without network/tools
by mocking subprocess calls.
"""

from types import SimpleNamespace

import scripts.security.security_scan as security_scan


def test_main_non_strict_no_tools_returns_ok(monkeypatch):
    """In non-strict mode, missing tools should not cause a failure. ReqID: SEC-01"""

    # Mock the module-level run() helper to simulate missing tools / no network
    def fake_run(cmd):
        # Simulate failure or missing tool without raising
        return 127

    monkeypatch.setattr(security_scan, "run", fake_run)

    # Also patch subprocess.run used for capturing Safety output to prevent real calls
    def fake_subprocess_run(cmd, cwd=None, capture_output=False, text=False):
        return SimpleNamespace(returncode=127, stdout="", stderr="")

    monkeypatch.setattr(
        security_scan, "subprocess", SimpleNamespace(run=fake_subprocess_run)
    )

    # Non-strict should tolerate missing tools and still exit 0
    assert security_scan.main() == 0
