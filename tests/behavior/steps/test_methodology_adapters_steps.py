from typing import Any, Dict, List

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.methodology.adhoc import AdHocAdapter
from devsynth.methodology.base import BaseMethodologyAdapter, Phase
from devsynth.methodology.sprint import SprintAdapter
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios(feature_path(__file__, "general", "methodology_adapters.feature"))


# Define a fixture for the context
@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.config = {}
            self.methodology_type = None
            self.adapter = None
            self.current_phase = None
            self.phase_progression_result = None
            self.next_phase = None
            self.cycle_results = {}
            self.reports = []

    return Context()


# Background steps
@given("the DevSynth system is initialized")
def devsynth_initialized(context):
    # In a real implementation, this would initialize the DevSynth system
    # For testing purposes, we'll just set up a basic configuration
    context.config = {
        "methodologyConfiguration": {
            "type": "sprint",
            "phases": {
                "expand": {"skipable": False},
                "differentiate": {"skipable": True},
                "refine": {"skipable": False},
                "retrospect": {"skipable": False},
            },
            "settings": {},
        }
    }


@given("the methodology configuration is loaded from manifest.yaml")
def methodology_config_loaded(context):
    """Ensure that the methodology configuration is available."""
    assert "methodologyConfiguration" in context.config


# Sprint Adapter Configuration steps
@when(
    parsers.parse(
        'I set the methodology type to "{methodology_type}" in the configuration'
    )
)
def set_methodology_type(context, methodology_type):
    context.methodology_type = methodology_type
    context.config["methodologyConfiguration"]["type"] = methodology_type


@when(parsers.parse("I configure the sprint duration to {duration:d} weeks"))
def configure_sprint_duration(context, duration):
    context.config["methodologyConfiguration"]["settings"]["sprintDuration"] = duration


@when("I configure the ceremony mappings:")
def configure_ceremony_mappings(context, table):
    ceremony_mappings = {}
    for row in table:
        ceremony_mappings[row["ceremony"]] = row["edrr_phase"]

    context.config["methodologyConfiguration"]["settings"][
        "ceremonyMapping"
    ] = ceremony_mappings


@then(parsers.parse('the methodology adapter should be of type "{adapter_type}"'))
def check_adapter_type(context, adapter_type):
    if adapter_type == "SprintAdapter":
        context.adapter = SprintAdapter(context.config["methodologyConfiguration"])
        assert isinstance(context.adapter, SprintAdapter)
    elif adapter_type == "AdHocAdapter":
        context.adapter = AdHocAdapter(context.config["methodologyConfiguration"])
        assert isinstance(context.adapter, AdHocAdapter)
    else:
        assert False, f"Unknown adapter type: {adapter_type}"


@then(parsers.parse("the sprint duration should be {duration:d} weeks"))
def check_sprint_duration(context, duration):
    assert context.adapter.config["settings"]["sprintDuration"] == duration


@then("the ceremony mappings should be correctly configured")
def check_ceremony_mappings(context):
    ceremony_mapping = context.adapter.config["settings"]["ceremonyMapping"]
    assert "planning" in ceremony_mapping
    assert "dailyStandup" in ceremony_mapping
    assert "review" in ceremony_mapping
    assert "retrospective" in ceremony_mapping
    assert ceremony_mapping["planning"] == "retrospect.iteration_planning"
    assert ceremony_mapping["dailyStandup"] == "phase_progression_tracking"
    assert ceremony_mapping["review"] == "refine.outputs_review"
    assert ceremony_mapping["retrospective"] == "retrospect.process_evaluation"


# Ad-Hoc Adapter Configuration steps
@when("I configure the phase settings:")
def configure_phase_settings(context, table):
    phase_settings = {}
    for row in table:
        phase_name = row["phase"]
        skipable = row["skipable"].lower() == "true"
        phase_settings[phase_name] = {"skipable": skipable}

    context.config["methodologyConfiguration"]["phases"] = phase_settings


@then("the phase settings should be correctly configured")
def check_phase_settings(context):
    phases = context.adapter.config["phases"]
    assert "expand" in phases
    assert "differentiate" in phases
    assert "refine" in phases
    assert "retrospect" in phases
    assert phases["expand"]["skipable"] is False
    assert phases["differentiate"]["skipable"] is True
    assert phases["refine"]["skipable"] is False
    assert phases["retrospect"]["skipable"] is False


# Phase Progression steps
@given(parsers.parse('the methodology type is set to "{methodology_type}"'))
def methodology_type_set(context, methodology_type):
    context.methodology_type = methodology_type
    context.config["methodologyConfiguration"]["type"] = methodology_type

    if methodology_type == "sprint":
        context.adapter = SprintAdapter(context.config["methodologyConfiguration"])
    elif methodology_type == "adhoc":
        context.adapter = AdHocAdapter(context.config["methodologyConfiguration"])
    else:
        assert False, f"Unknown methodology type: {methodology_type}"


@given(parsers.parse('the current phase is "{phase}"'))
def current_phase_set(context, phase):
    context.current_phase = getattr(Phase, phase.upper())


@given("all required activities for the phase are completed")
def required_activities_completed(context):
    # In a real implementation, this would check if all required activities are completed
    # For testing purposes, we'll mock this by setting up the context appropriately
    if context.methodology_type == "sprint":
        # Mock the _get_required_activities method to return an empty list (all activities completed)
        context.adapter._get_required_activities = lambda phase: []


@given("the phase time allocation is not exceeded")
def phase_time_not_exceeded(context):
    # In a real implementation, this would check if the phase time allocation is not exceeded
    # For testing purposes, we'll mock this by setting up the context appropriately
    if context.methodology_type == "sprint":
        # Mock the time check to return True (time not exceeded)
        context.adapter._is_phase_time_exceeded = lambda phase: False


@given("the user has explicitly requested to progress to the next phase")
def user_requested_progression(context):
    # In a real implementation, this would check if the user has requested progression
    # For testing purposes, we'll mock this by setting up the context appropriately
    if context.methodology_type == "adhoc":
        # Set the user_requested_progression flag to True
        context.adapter.user_requested_progression = True


@when("the system checks if it should progress to the next phase")
def check_phase_progression(context):
    phase_context = {}  # In a real implementation, this would contain relevant context
    phase_results = {}  # In a real implementation, this would contain phase results

    context.phase_progression_result = context.adapter.should_progress_to_next_phase(
        context.current_phase, phase_context, phase_results
    )

    # Determine the next phase
    if context.phase_progression_result:
        phases = list(Phase)
        current_index = phases.index(context.current_phase)
        if current_index < len(phases) - 1:
            context.next_phase = phases[current_index + 1]
        else:
            context.next_phase = None


@then(parsers.parse("the result should be {result}"))
def check_progression_result(context, result):
    expected_result = result.lower() == "true"
    assert context.phase_progression_result == expected_result


@then(parsers.parse('the next phase should be "{phase}"'))
def check_next_phase(context, phase):
    expected_phase = getattr(Phase, phase.upper())
    assert context.next_phase == expected_phase


# Report Generation steps
@given("a complete EDRR cycle has been executed")
def complete_cycle_executed(context):
    # In a real implementation, this would set up the results of a complete EDRR cycle
    # For testing purposes, we'll create a mock cycle results dictionary
    context.cycle_results = {
        "expand": {
            "artifacts_discovered": 150,
            "files_processed": 200,
            "duration_seconds": 120,
        },
        "differentiate": {
            "inconsistencies_found": 10,
            "gaps_identified": 5,
            "duration_seconds": 90,
        },
        "refine": {
            "relationships_created": 75,
            "outdated_items_archived": 15,
            "duration_seconds": 180,
        },
        "retrospect": {
            "insights_captured": 8,
            "improvements_identified": 12,
            "duration_seconds": 60,
        },
    }


@when("the system generates reports for the cycle")
def generate_reports(context):
    context.reports = context.adapter.generate_reports(context.cycle_results)


@then("a sprint review report should be generated")
def check_sprint_review_report(context):
    assert any("Sprint Review" in report["title"] for report in context.reports)


@then("a sprint retrospective report should be generated")
def check_sprint_retrospective_report(context):
    assert any("Sprint Retrospective" in report["title"] for report in context.reports)


@then("a summary report should be generated")
def check_summary_report(context):
    assert any("Summary" in report["title"] for report in context.reports)


@then("the reports should contain the cycle results")
@then("the report should contain the cycle results")
def check_report_contents(context):
    # Check that at least one report contains key metrics from the cycle results
    for report in context.reports:
        if "content" in report:
            content = report["content"]
            if (
                "artifacts_discovered: 150" in content
                or "inconsistencies_found: 10" in content
                or "relationships_created: 75" in content
                or "insights_captured: 8" in content
            ):
                break
    else:
        assert False, "No report contains cycle results metrics"
