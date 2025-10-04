"""Step definitions for run-tests CLI behavior tests.

SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullets for CLI behavior (reporting, segmentation, optional providers, coverage enforcement).
"""

import os
from pathlib import Path

import pytest
from pytest_bdd import parsers, then


@pytest.mark.fast
@then("the command should exit successfully")
def command_exits_successfully(command_context):
    """Confirm CLI success per coverage enforcement gate.

    SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "Successful runs enforce a minimum coverage threshold of DEFAULT_COVERAGE_THRESHOLD (90%) whenever coverage instrumentation is active; the CLI prints a success banner when the gate is met and exits with an error if coverage falls below the limit."
    """
    assert command_context.get("exit_code", 1) == 0


@pytest.mark.fast
@then(parsers.parse('a test HTML report should exist under "{reports_dir}"'))
def report_exists_under(reports_dir: str):
    """Verify report artifacts for the --report CLI flag.

    SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "--report emits HTML and JSON coverage artifacts summarizing executed speed profiles for audit trails."
    """

    base = Path(reports_dir)
    assert base.exists(), f"Reports dir {reports_dir} does not exist"
    htmls = list(base.glob("*.html"))
    assert htmls, f"No HTML reports found under {reports_dir}"


@pytest.mark.fast
@then("the segmentation should be reflected in the invocation")
def segmentation_reflected(command_context):
    """Ensure segmentation arguments mirror CLI contract.

    SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "--segment runs tests in batches; --segment-size sets batch size (default 50)."
    """

    call = command_context.get("run_tests_call")
    assert call is not None, "run_tests invocation was not captured"
    args = call["args"]
    # Signature: target, speeds, verbose, report, parallel, segment, segment_size, maxfail
    assert args[5] is True, f"Expected segment flag set, got {args[5]!r}"
    assert args[6] == 5, f"Expected segment_size=5, got {args[6]}"


@pytest.mark.fast
@then("the CLI should request segmentation without explicit speeds")
def segmentation_without_speeds(command_context):
    """Segmentation fallback keeps speeds unset while honoring size hints.

    SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "--segment runs tests in batches; --segment-size sets batch size (default 50)."
    """

    call = command_context.get("run_tests_call")
    assert call is not None, "run_tests invocation was not captured"
    args = call["args"]
    assert args[1] is None, "Expected no explicit speed categories"
    assert bool(args[5]) is True, "Segment flag should remain truthy"
    assert args[6] == 3, f"Expected segment_size=3, got {args[6]}"


@pytest.mark.fast
@then("plugin autoload should be disabled in the environment")
def plugin_autoload_disabled():
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"


@pytest.mark.fast
@then(
    parsers.parse('the command should fail with a helpful message containing "{text}"')
)
def command_fails_with_message(text: str, command_context):
    """Capture coverage enforcement failures beneath the threshold.

    SpecRef: docs/specifications/devsynth-run-tests-command.md §Specification bullet "Successful runs enforce a minimum coverage threshold of DEFAULT_COVERAGE_THRESHOLD (90%) whenever coverage instrumentation is active; the CLI prints a success banner when the gate is met and exits with an error if coverage falls below the limit."
    """

    command_context["expect_failure"] = True
    raw_code = command_context.get("raw_exit_code", command_context.get("exit_code", 0))
    assert raw_code != 0
    output = command_context.get("output", "")
    assert text in output
