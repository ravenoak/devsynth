"""Step definitions for policy audit behavior tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "policy_audit.feature"))


@pytest.fixture
def context():
    class Ctx:
        target: Path | None = None
        exit_code: int | None = None
        output: str | None = None

    return Ctx()


@given(parsers.parse('a config file "{filename}" containing "{content}"'))
def config_file(tmp_path: Path, filename: str, content: str, context):
    """Create a configuration file with insecure content."""
    path = tmp_path / filename
    path.write_text(content)
    context.target = path
    return path


@when("I run the policy audit on that file")
def run_policy_audit(context):
    """Execute the policy audit script against the target file."""
    assert context.target is not None
    result = subprocess.run(
        [
            "poetry",
            "run",
            sys.executable,
            "scripts/policy_audit.py",
            str(context.target),
        ],
        capture_output=True,
        text=True,
    )
    context.exit_code = result.returncode
    context.output = result.stdout


@then("the audit should report a violation")
def audit_reports_violation(context):
    """Verify the audit detected a policy violation."""
    assert context.exit_code and context.exit_code != 0
    assert context.output and "Policy violations found" in context.output
