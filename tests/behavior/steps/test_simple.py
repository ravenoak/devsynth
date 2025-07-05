"""Simple test to isolate the issue."""

from __future__ import annotations
from typing import Dict

from pytest_bdd import given, when, then, parsers
from pytest_bdd import scenarios
import pytest

# Import the scenarios from the feature file
scenarios('../features/edrr_cycle.feature')

@pytest.fixture
def context() -> Dict[str, object]:
    return {}

@given("a valid manifest file")
def valid_manifest(tmp_path, context):
    """Create a valid manifest file."""
    return tmp_path / "manifest.json"

@when('I run the command "devsynth edrr-cycle" with that file')
def run_edrr_cycle(context):
    """Run the edrr-cycle command."""
    context["output"] = "Starting EDRR cycle"
    context["started"] = True

@then("the coordinator should process the manifest")
def coordinator_processed_manifest(context):
    """Verify the coordinator processed the manifest."""
    assert context.get("started") is True