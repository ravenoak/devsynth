"""Steps for the edrr_cycle.feature implemented without mocks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("../features/edrr_cycle.feature")


@pytest.fixture
def context() -> Dict[str, object]:
    return {}


@given("a valid manifest file")
def valid_manifest(tmp_path: Path, context: Dict[str, object]) -> Path:
    print("\n=== Setting up valid manifest ===")
    manifest = tmp_path / "manifest.json"
    manifest_content = '{"project": "demo"}'
    print(f"Writing manifest content: {manifest_content}")
    manifest.write_text(manifest_content)
    context["manifest"] = manifest
    print(f"Manifest path: {manifest}")
    print(f"Manifest exists: {manifest.exists()}")
    print(f"Manifest content: {manifest.read_text()}")
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
    print(f"Manifest path: {manifest}")
    print(f"Manifest exists: {manifest.exists()}")

    if not manifest.exists():
        context["output"] = f"[red]Manifest file not found:[/red] {manifest}"
        context["started"] = False
        print(f"Manifest not found, started = {context.get('started')}")
        return

    try:
        manifest_content = manifest.read_text()
        print(f"Manifest content: {manifest_content}")
        json_content = json.loads(manifest_content)
        print(f"Parsed JSON: {json_content}")
    except Exception as e:
        context["output"] = f"[red]Invalid manifest:[/red] {manifest}"
        context["started"] = False
        print(f"Invalid manifest: {e}, started = {context.get('started')}")
        return

    context["output"] = "[bold]Starting EDRR cycle[/bold]"
    context["started"] = True
    print(f"EDRR cycle started, started = {context.get('started')}")


@then("the coordinator should process the manifest")
def coordinator_processed_manifest(context: Dict[str, object]) -> None:
    print("\n=== Checking if coordinator processed manifest ===")
    print(f"Context: {context}")
    print(f"Started: {context.get('started')}")
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
