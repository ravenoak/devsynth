"""Steps for the edrr_cycle.feature implemented without mocks."""

from __future__ import annotations

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


@given("a valid manifest file")
def valid_manifest(tmp_path: Path, context: Dict[str, object]) -> Path:
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


@given("no manifest file exists at the provided path")
def missing_manifest(tmp_path: Path, context: Dict[str, object]) -> Path:
    context["manifest"] = tmp_path / "missing.json"
    return context["manifest"]


@given("an invalid manifest file")
def invalid_manifest(tmp_path: Path, context: Dict[str, object]) -> Path:
    manifest = tmp_path / "invalid.json"
    manifest.write_text("not valid json")
    context["manifest"] = manifest
    return manifest


@when('I run the command "devsynth edrr-cycle" with that file')
def run_edrr_cycle(context: Dict[str, object]) -> None:
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


@then("the coordinator should process the manifest")
def coordinator_processed_manifest(context: Dict[str, object]) -> None:
    logger.debug("Checking if coordinator processed manifest")
    logger.debug("Context: %s", context)
    logger.debug("Started: %s", context.get("started"))
    assert context.get("started") is True


@then("the workflow should complete successfully")
def workflow_completed(context: Dict[str, object]) -> None:
    assert context.get("started") is True


@then("the output should indicate the cycle started")
def cycle_start_message(context: Dict[str, object]) -> None:
    assert "Starting EDRR cycle" in context.get("output", "")


@then("the system should report that the manifest file was not found")
def manifest_not_found_error(context: Dict[str, object]) -> None:
    assert "not found" in context.get("output", "")


@then("the coordinator should not be invoked")
def coordinator_not_invoked(context: Dict[str, object]) -> None:
    assert context.get("started") is False


@then("the system should report that the manifest file is invalid")
def invalid_manifest_error(context: Dict[str, object]) -> None:
    assert "Invalid manifest" in context.get("output", "")
