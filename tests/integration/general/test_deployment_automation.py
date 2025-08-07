"""Tests for deployment automation scripts.

This suite verifies that deployment scripts exist and basic rollback
instructions are documented.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts/deployment"
RUNBOOKS_DIR = ROOT / "docs/deployment/runbooks"


def test_bootstrap_env_script_exists_and_contains_docker():
    script = SCRIPTS_DIR / "bootstrap_env.sh"
    assert script.exists()
    content = script.read_text()
    assert "docker compose" in content


def test_health_check_script_exists_and_contains_curl():
    script = SCRIPTS_DIR / "health_check.sh"
    assert script.exists()
    content = script.read_text()
    assert "curl" in content


def test_rollback_runbook_mentions_stop_stack():
    runbook = RUNBOOKS_DIR / "rollback.md"
    assert runbook.exists()
    text = runbook.read_text()
    assert "stop_stack.sh" in text
