"""Tests for deployment automation scripts.

This suite verifies that deployment scripts exist, images can be published,
and rollback instructions are documented.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts/deployment"
RUNBOOKS_DIR = ROOT / "docs/deployment/runbooks"


@pytest.mark.slow
def test_bootstrap_script_exists_and_builds_images():
    script = SCRIPTS_DIR / "bootstrap.sh"
    assert script.exists()
    content = script.read_text()
    assert "docker compose build" in content


@pytest.mark.slow
def test_health_check_script_exists_and_contains_curl():
    script = SCRIPTS_DIR / "health_check.sh"
    assert script.exists()
    content = script.read_text()
    assert "curl" in content


@pytest.mark.slow
def test_publish_image_script_exists_and_pushes():
    script = SCRIPTS_DIR / "publish_image.sh"
    assert script.exists()
    content = script.read_text()
    assert "docker compose push" in content


@pytest.mark.slow
def test_docker_compose_defines_image_for_devsynth():
    compose_file = ROOT / "docker-compose.yml"
    assert compose_file.exists()
    text = compose_file.read_text()
    assert "image: ghcr.io/devsynth/devsynth" in text


@pytest.mark.slow
def test_rollback_runbook_mentions_scripts():
    runbook = RUNBOOKS_DIR / "rollback.md"
    assert runbook.exists()
    text = runbook.read_text()
    assert "rollback.sh" in text
    assert "publish_image.sh" in text
    assert "health_check.sh" in text


@pytest.mark.slow
def test_rollback_script_exists_and_redeploys():
    script = SCRIPTS_DIR / "rollback.sh"
    assert script.exists()
    content = script.read_text()
    assert "docker compose --env-file" in content
    assert "pull devsynth" in content
    assert "up -d devsynth" in content
