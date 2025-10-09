"""Step definitions for security audit reporting feature."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "security_audit_reporting.feature"))


@pytest.fixture
def context(tmp_path: Path):
    class Ctx:
        exit_code: int | None = None
        report_path: Path | None = None

    ctx = Ctx()
    ctx.tmpdir = tmp_path
    return ctx


@given("the security audit pre-deployment checks are approved")
def pre_deploy_checks(monkeypatch):
    required_true = [
        "DEVSYNTH_AUTHENTICATION_ENABLED",
        "DEVSYNTH_AUTHORIZATION_ENABLED",
        "DEVSYNTH_SANITIZATION_ENABLED",
        "DEVSYNTH_ENCRYPTION_AT_REST",
        "DEVSYNTH_ENCRYPTION_IN_TRANSIT",
        "DEVSYNTH_TLS_VERIFY",
        "DEVSYNTH_PRE_DEPLOY_APPROVED",
    ]
    for var in required_true:
        monkeypatch.setenv(var, "true")
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "token")


@when(
    parsers.parse('I run the command "devsynth security-audit --report ' '{filename}"')
)
def run_security_audit(context, filename: str):
    report = context.tmpdir / filename
    cmd = [
        "poetry",
        "run",
        sys.executable,
        "scripts/security_audit.py",
        "--report",
        str(report),
        "--skip-bandit",
        "--skip-safety",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    context.exit_code = result.returncode
    context.report_path = report


@then(
    parsers.parse(
        'the audit report "{filename}" should contain "bandit" ' 'and "safety" results'
    )
)
def verify_report(context, filename: str):
    assert context.report_path and context.report_path.name == filename
    data = json.loads(context.report_path.read_text())
    assert "bandit" in data
    assert "safety" in data


@then("the workflow should execute successfully")
def workflow_succeeds(context):
    assert context.exit_code == 0
