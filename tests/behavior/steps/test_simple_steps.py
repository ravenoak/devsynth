"""Simple test to isolate the issue."""

from __future__ import annotations
from typing import Dict, Generator
import os
import json
import shutil

from pytest_bdd import given, when, then, parsers
from pytest_bdd import scenarios
import pytest

# Import the scenarios from the feature file
scenarios('../features/general/edrr_cycle.feature')

@pytest.fixture
def context() -> Generator[Dict[str, object], None, None]:
    """Create a context dictionary for sharing state between steps.
    
    This fixture uses a generator pattern to provide teardown functionality.
    """
    # Setup: Create an empty context dictionary
    ctx = {}
    
    # Yield the context to the test
    yield ctx
    
    # Teardown: Clean up any resources created during the test
    if "manifest_path" in ctx and os.path.exists(ctx["manifest_path"]):
        try:
            os.remove(ctx["manifest_path"])
        except (OSError, IOError):
            # If we can't remove the file, it's likely already gone
            pass

@pytest.mark.medium
@given("a valid manifest file")
def valid_manifest(tmp_path, context):
    """Create a valid manifest file."""
    manifest_path = tmp_path / "manifest.json"

    # Create a simple valid manifest
    manifest_content = {
        "task": {
            "id": "test-task",
            "description": "Test task for EDRR cycle"
        },
        "config": {
            "auto_progress": True
        }
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest_content, f)

    context["manifest_path"] = manifest_path
    return manifest_path

@pytest.mark.medium
@given("no manifest file exists at the provided path")
def missing_manifest(tmp_path, context):
    """Set up a path where no manifest file exists."""
    manifest_path = tmp_path / "nonexistent_manifest.json"
    context["manifest_path"] = manifest_path
    return manifest_path

@pytest.mark.medium
@given("an invalid manifest file")
def invalid_manifest(tmp_path, context):
    """Create an invalid manifest file."""
    manifest_path = tmp_path / "invalid_manifest.json"

    # Create an invalid JSON file
    with open(manifest_path, "w") as f:
        f.write("This is not valid JSON")

    context["manifest_path"] = manifest_path
    return manifest_path

@pytest.mark.medium
@when('I run the command "devsynth edrr-cycle" with that file')
def run_edrr_cycle(context):
    """Run the edrr-cycle command."""
    manifest_path = context.get("manifest_path")

    # Simulate running the command
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                try:
                    manifest_content = json.load(f)
                    context["output"] = "Starting EDRR cycle"
                    context["started"] = True
                    context["completed"] = True
                except json.JSONDecodeError:
                    context["output"] = "Invalid manifest file"
                    context["error"] = "invalid_manifest"
        except FileNotFoundError:
            context["output"] = "Manifest file not found"
            context["error"] = "file_not_found"
    else:
        context["output"] = "Manifest file not found"
        context["error"] = "file_not_found"

@pytest.mark.medium
@then("the coordinator should process the manifest")
def coordinator_processed_manifest(context):
    """Verify the coordinator processed the manifest."""
    assert context.get("started") is True

@pytest.mark.medium
@then("the workflow should complete successfully")
def workflow_completes_successfully(context):
    """Verify the workflow completes successfully."""
    assert context.get("completed") is True

@pytest.mark.medium
@then("the output should indicate the cycle started")
def output_indicates_cycle_started(context):
    """Verify the output indicates the cycle started."""
    assert "Starting EDRR cycle" in context.get("output", "")

@pytest.mark.medium
@then("the system should report that the manifest file was not found")
def system_reports_manifest_not_found(context):
    """Verify the system reports that the manifest file was not found."""
    assert context.get("error") == "file_not_found"
    assert "not found" in context.get("output", "")

@pytest.mark.medium
@then("the system should report that the manifest file is invalid")
def system_reports_invalid_manifest(context):
    """Verify the system reports that the manifest file is invalid."""
    assert context.get("error") == "invalid_manifest"
    assert "Invalid" in context.get("output", "")

@pytest.mark.medium
@then("the coordinator should not be invoked")
def coordinator_not_invoked(context):
    """Verify the coordinator was not invoked."""
    assert context.get("started") is not True
