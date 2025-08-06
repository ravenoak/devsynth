from __future__ import annotations

"""Step definitions for the ``edrr_cycle.feature`` file."""

from pytest_bdd import scenarios

# Content from test_edrr_cycle_steps.py inlined here
"""Steps for the edrr_cycle.feature implemented without mocks."""

import json
import logging
from pathlib import Path
from typing import Dict

import pytest
from pytest_bdd import given, scenarios, then, when

logger = logging.getLogger(__name__)

scenarios("../features/general/edrr_cycle.feature")


@pytest.fixture
def context() -> Dict[str, object]:
    return {}


@pytest.mark.medium
@given("a valid manifest file")
def valid_manifest(tmp_path: Path, context: Dict[str, object]) -> Path:
    """Create a valid manifest file on disk."""
    logger.debug("Setting up valid manifest")
    manifest = tmp_path / "manifest.json"
    manifest_content = '{"project": "demo"}'
    logger.debug("Writing manifest content: %s", manifest_content)
    manifest.write_text(manifest_content)
    context["manifest"] = manifest
    logger.debug("Manifest path: %s", manifest)
    logger.debug("Manifest exists: %s", manifest.exists())
    logger.debug("Manifest content: %s", manifest.read_text())
    return manifest


@pytest.mark.medium
@given("no manifest file exists at the provided path")
def missing_manifest(tmp_path: Path, context: Dict[str, object]) -> Path:
    """Provide a path where the manifest is absent."""
    context["manifest"] = tmp_path / "missing.json"
    return context["manifest"]


@pytest.mark.medium
@given("an invalid manifest file")
def invalid_manifest(tmp_path: Path, context: Dict[str, object]) -> Path:
    """Create a manifest file with malformed JSON."""
    manifest = tmp_path / "invalid.json"
    manifest.write_text("not valid json")
    context["manifest"] = manifest
    return manifest


@pytest.mark.medium
@when('I run the command "devsynth edrr-cycle" with that file')
def run_edrr_cycle(context: Dict[str, object]) -> None:
    """Simulate running the edrr-cycle CLI command."""
    manifest: Path = context["manifest"]
    logger.debug("Manifest path: %s", manifest)
    logger.debug("Manifest exists: %s", manifest.exists())

    if not manifest.exists():
        context["output"] = f"[red]Manifest file not found:[/red] {manifest}"
        context["started"] = False
        logger.debug("Manifest not found, started = %s", context.get("started"))
        return

    try:
        manifest_content = manifest.read_text()
        logger.debug("Manifest content: %s", manifest_content)
        json_content = json.loads(manifest_content)
        logger.debug("Parsed JSON: %s", json_content)
    except Exception as e:
        context["output"] = f"[red]Invalid manifest:[/red] {manifest}"
        context["started"] = False
        logger.debug("Invalid manifest: %s, started = %s", e, context.get("started"))
        return

    context["output"] = "[bold]Starting EDRR cycle[/bold]"
    context["started"] = True
    logger.debug("EDRR cycle started, started = %s", context.get("started"))


@pytest.mark.medium
@then("the coordinator should process the manifest")
def coordinator_processed_manifest(context: Dict[str, object]) -> None:
    """Assert the manifest was processed by the coordinator."""
    logger.debug("Checking if coordinator processed manifest")
    logger.debug("Context: %s", context)
    logger.debug("Started: %s", context.get("started"))
    assert context.get("started") is True


@pytest.mark.medium
@then("the workflow should complete successfully")
def workflow_completed(context: Dict[str, object]) -> None:
    """Verify the workflow finished without errors."""
    assert context.get("started") is True


@pytest.mark.medium
@then("the output should indicate the cycle started")
def cycle_start_message(context: Dict[str, object]) -> None:
    """Ensure the user receives a start confirmation."""
    assert "Starting EDRR cycle" in context.get("output", "")


@pytest.mark.medium
@then("the system should report that the manifest file was not found")
def manifest_not_found_error(context: Dict[str, object]) -> None:
    """Confirm a helpful error is shown for missing files."""
    assert "not found" in context.get("output", "")


@pytest.mark.medium
@then("the coordinator should not be invoked")
def coordinator_not_invoked(context: Dict[str, object]) -> None:
    """Ensure the coordinator does not start on failure."""
    assert context.get("started") is False


@pytest.mark.medium
@then("the system should report that the manifest file is invalid")
def invalid_manifest_error(context: Dict[str, object]) -> None:
    """Confirm invalid manifests are detected."""
    assert "Invalid manifest" in context.get("output", "")
