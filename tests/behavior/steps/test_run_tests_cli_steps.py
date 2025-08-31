"""Step definitions for run-tests CLI behavior tests."""

import os
from pathlib import Path

import pytest
from pytest_bdd import parsers, then


@pytest.mark.fast
@then("the command should exit successfully")
def command_exits_successfully(command_context):
    """Verify that the command exited with a zero status code."""
    assert command_context.get("exit_code", 1) == 0


@pytest.mark.fast
@then(parsers.parse('a test HTML report should exist under "{reports_dir}"'))
def report_exists_under(reports_dir: str):
    base = Path(reports_dir)
    assert base.exists(), f"Reports dir {reports_dir} does not exist"
    htmls = list(base.glob("*.html"))
    assert htmls, f"No HTML reports found under {reports_dir}"


@pytest.mark.fast
@then("the segmentation should be reflected in the invocation")
def segmentation_reflected(command_context):
    call = command_context.get("run_tests_call")
    assert call is not None, "run_tests invocation was not captured"
    args = call["args"]
    # Signature: target, speeds, verbose, report, parallel, segment, segment_size, maxfail
    assert args[5] == 2, f"Expected segment=2, got {args[5]}"
    assert args[6] == 5, f"Expected segment_size=5, got {args[6]}"


@pytest.mark.fast
@then("plugin autoload should be disabled in the environment")
def plugin_autoload_disabled():
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"


@pytest.mark.fast
@then(
    parsers.parse('the command should fail with a helpful message containing "{text}"')
)
def command_fails_with_message(text: str, command_context):
    assert command_context.get("exit_code", 0) != 0
    output = command_context.get("output", "")
    assert text in output
