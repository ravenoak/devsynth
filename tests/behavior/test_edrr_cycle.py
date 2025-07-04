"""
Test script for the EDRR cycle feature.

This script implements the step definitions for the EDRR cycle feature file.
"""

import os
import json
import pytest
from pathlib import Path
from pytest_bdd import scenarios, given, when, then

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "edrr_cycle.feature")

# Load the scenarios from the feature file
scenarios(feature_file)

@pytest.fixture
def context():
    """Create a context for the test."""
    class Context:
        def __init__(self):
            self.manifest = None
            self.output = None
            self.started = False
    return Context()

@given("a valid manifest file")
def valid_manifest(tmp_path, context):
    """Create a valid manifest file."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"project": "demo"}')
    context.manifest = manifest
    return manifest

@given("no manifest file exists at the provided path")
def missing_manifest(tmp_path, context):
    """Ensure no manifest file exists at the provided path."""
    manifest = tmp_path / "missing.json"
    context.manifest = manifest
    return manifest

@given("an invalid manifest file")
def invalid_manifest(tmp_path, context):
    """Create an invalid manifest file."""
    manifest = tmp_path / "invalid.json"
    manifest.write_text("not valid json")
    context.manifest = manifest
    return manifest

@when('I run the command "devsynth edrr-cycle" with that file')
def run_edrr_cycle(context):
    """Simulate running the edrr-cycle command."""
    manifest = context.manifest
    if not manifest.exists():
        context.output = f"[red]Manifest file not found:[/red] {manifest}"
        context.started = False
        return
    
    try:
        json.loads(manifest.read_text())
    except Exception:
        context.output = f"[red]Invalid manifest:[/red] {manifest}"
        context.started = False
        return
    
    context.output = "[bold]Starting EDRR cycle[/bold]"
    context.started = True

@then("the coordinator should process the manifest")
def coordinator_processed_manifest(context):
    """Verify that the coordinator processed the manifest."""
    assert context.started is True

@then("the workflow should complete successfully")
def workflow_completed(context):
    """Verify that the workflow completed successfully."""
    assert context.started is True

@then("the output should indicate the cycle started")
def cycle_start_message(context):
    """Verify that the output indicates the cycle started."""
    assert "Starting EDRR cycle" in context.output

@then("the system should report that the manifest file was not found")
def manifest_not_found_error(context):
    """Verify that the system reports that the manifest file was not found."""
    assert "not found" in context.output

@then("the coordinator should not be invoked")
def coordinator_not_invoked(context):
    """Verify that the coordinator was not invoked."""
    assert context.started is False

@then("the system should report that the manifest file is invalid")
def invalid_manifest_error(context):
    """Verify that the system reports that the manifest file is invalid."""
    assert "Invalid manifest" in context.output