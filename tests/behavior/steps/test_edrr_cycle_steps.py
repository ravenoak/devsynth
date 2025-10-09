"""Step definitions for the ``edrr_cycle.feature`` file."""

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.application.orchestration.workflow import workflow_manager
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "edrr_cycle.feature"))


@pytest.fixture
def context():
    """Context object for storing state between steps."""

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
    """Execute the edrr-cycle command through the workflow manager."""
    manifest = context.manifest
    result = workflow_manager.execute_command("edrr-cycle", {"manifest": str(manifest)})
    context.output = result.get("message")
    context.started = result.get("success", False)


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
    assert "Starting EDRR cycle" in (context.output or "")


@then("the system should report that the manifest file was not found")
def manifest_not_found_error(context):
    """Verify that the system reports that the manifest file was not found."""
    assert "not found" in (context.output or "")


@then("the coordinator should not be invoked")
def coordinator_not_invoked(context):
    """Verify that the coordinator was not invoked."""
    assert context.started is False


@then("the system should report that the manifest file is invalid")
def invalid_manifest_error(context):
    """Verify that the system reports that the manifest file is invalid."""
    assert "Invalid manifest" in (context.output or "")
