"""Steps for cross-interface consistency feature.

ReqID: FR-67
"""

from tests.behavior.feature_paths import feature_path
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when


pytestmark = [pytest.mark.fast]

# Load scenarios from the feature file
scenarios(feature_path(__file__, "general", "cross_interface_consistency.feature"))

OUTPUT_FORMATTER_DOC = (
    Path(__file__).parents[3]
    / "docs"
    / "implementation"
    / "output_formatter_invariants.md"
)

# Helper to access implementation functions from the test module without
# creating an import cycle.


def _impl(name: str):
    mod = importlib.import_module("tests.behavior.test_cross_interface_consistency")
    return getattr(mod, name)


@given("the CLI, WebUI, and Agent API are initialized")
def interfaces_initialized(cross_interface_context):
    return _impl("interfaces_initialized")(cross_interface_context)


@pytest.fixture
def cross_interface_context(monkeypatch):
    return _impl("cross_interface_context")(monkeypatch)


@when(parsers.parse("I invoke the {command} command with identical parameters via CLI"))
def invoke_cli_command(cross_interface_context, command):
    return _impl("invoke_cli_command")(cross_interface_context, command)


@when(
    parsers.parse("I invoke the {command} command with identical parameters via WebUI")
)
def invoke_webui_command(cross_interface_context, command):
    return _impl("invoke_webui_command")(cross_interface_context, command)


@when(
    parsers.parse(
        "I invoke the {command} command with identical parameters via Agent API"
    )
)
def invoke_api_command(cross_interface_context, command):
    return _impl("invoke_api_command")(cross_interface_context, command)


@when(parsers.parse("I invoke the {command} command with invalid parameters via CLI"))
def invoke_cli_command_invalid(cross_interface_context, command):
    return _impl("invoke_cli_command_invalid")(cross_interface_context, command)


@when(parsers.parse("I invoke the {command} command with invalid parameters via WebUI"))
def invoke_webui_command_invalid(cross_interface_context, command):
    return _impl("invoke_webui_command_invalid")(cross_interface_context, command)


@when(
    parsers.parse(
        "I invoke the {command} command with invalid parameters via Agent API"
    )
)
def invoke_api_command_invalid(cross_interface_context, command):
    return _impl("invoke_api_command_invalid")(cross_interface_context, command)


@when("I need to ask a question via CLI")
def ask_question_cli(cross_interface_context):
    return _impl("ask_question_cli")(cross_interface_context)


@when("I need to ask the same question via WebUI")
def ask_question_webui(cross_interface_context):
    return _impl("ask_question_webui")(cross_interface_context)


@when("I need to ask the same question via Agent API")
def ask_question_api(cross_interface_context):
    return _impl("ask_question_api")(cross_interface_context)


@when("I perform a long-running operation via CLI")
def long_running_cli(cross_interface_context):
    return _impl("long_running_cli")(cross_interface_context)


@when("I perform the same long-running operation via WebUI")
def long_running_webui(cross_interface_context):
    return _impl("long_running_webui")(cross_interface_context)


@when("I perform the same long-running operation via Agent API")
def long_running_api(cross_interface_context):
    return _impl("long_running_api")(cross_interface_context)


@then("all interfaces should produce identical results")
def verify_identical_results(cross_interface_context):
    return _impl("verify_identical_results")(cross_interface_context)


@then("all interfaces should use the same UXBridge methods")
def verify_same_uxbridge_methods(cross_interface_context):
    return _impl("verify_same_uxbridge_methods")(cross_interface_context)


@then("all interfaces should handle progress indicators consistently")
def verify_progress_consistency(cross_interface_context):
    return _impl("verify_progress_consistency")(cross_interface_context)


@then("all interfaces should report the same error")
def verify_same_error(cross_interface_context):
    return _impl("verify_same_error")(cross_interface_context)


@then("all interfaces should handle the error gracefully")
def verify_graceful_error_handling(cross_interface_context):
    return _impl("verify_graceful_error_handling")(cross_interface_context)


@then("all interfaces should present the question consistently")
def verify_question_consistency(cross_interface_context):
    return _impl("verify_question_consistency")(cross_interface_context)


@then("all interfaces should handle the response consistently")
def verify_response_consistency(cross_interface_context):
    return _impl("verify_response_consistency")(cross_interface_context)


@then("all interfaces should report progress consistently")
def verify_progress_reporting_consistency(cross_interface_context):
    return _impl("verify_progress_reporting_consistency")(cross_interface_context)


@then("all interfaces should indicate completion consistently")
def verify_completion_consistency(cross_interface_context):
    return _impl("verify_completion_consistency")(cross_interface_context)


@then("the output formatting invariants guide interface styling")
def verify_output_formatter_doc_present() -> None:
    """Ensure cross-interface scenarios can rely on the documented formatter contract."""

    assert OUTPUT_FORMATTER_DOC.is_file()
