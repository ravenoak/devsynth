"""
A simple test script to verify that pytest-bdd works without relying on __init__.py.
"""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "edrr_cycle.feature"))


@pytest.fixture
def context():
    """Create a context for the test."""

    class Context:
        def __init__(self):
            self.manifest = None
            self.output = None
            self.started = False
            self.error_message = None

    return Context()


@given("a valid manifest file")
def valid_manifest(tmp_path, context):
    """Create a valid manifest file."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{" "project" ": " "demo" "}")
    context.manifest = manifest
    return manifest


@given("no manifest file exists at the provided path")
def missing_manifest(tmp_path, context):
    """Simulate a missing manifest file."""
    # Create a path to a non-existent file
    context.manifest = tmp_path / "nonexistent_manifest.json"
    # Ensure the file doesn't exist
    if context.manifest.exists():
        context.manifest.unlink()
    return context.manifest


@given("an invalid manifest file")
def invalid_manifest(tmp_path, context):
    """Create an invalid manifest file."""
    manifest = tmp_path / "invalid_manifest.json"
    # Write invalid JSON content
    manifest.write_text("{invalid json content")
    context.manifest = manifest
    return manifest


@when('I run the command "devsynth edrr-cycle" with that file')
def run_edrr_cycle(context):
    """Simulate running the edrr-cycle command."""
    if not context.manifest.exists():
        context.error_message = f"Error: Manifest file not found at {context.manifest}"
        context.started = False
    elif context.manifest.name == "invalid_manifest.json":
        context.error_message = f"Error: Invalid manifest file at {context.manifest}"
        context.started = False
    else:
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
def manifest_not_found_message(context):
    """Verify that the system reports that the manifest file was not found."""
    assert context.error_message is not None
    assert "Manifest file not found" in context.error_message


@then("the system should report that the manifest file is invalid")
def manifest_invalid_message(context):
    """Verify that the system reports that the manifest file is invalid."""
    assert context.error_message is not None
    assert "Invalid manifest file" in context.error_message


@then("the coordinator should not be invoked")
def coordinator_not_invoked(context):
    """Verify that the coordinator was not invoked."""
    assert context.started is False
