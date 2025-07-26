"""Steps for the alignment metrics command feature."""

from pytest_bdd import scenarios, given, then

from .cli_commands_steps import (  # noqa: F401
    run_command,
    devsynth_cli_installed,
    valid_devsynth_project,
    check_workflow_success,
)
from .test_analyze_commands_steps import check_error_message  # noqa: F401

scenarios("../features/general/alignment_metrics_command.feature")


@given("alignment metrics calculation fails")
def metrics_fail(monkeypatch):
    """Force the alignment metrics command to raise an exception."""
    def _raise(*_args, **_kwargs):
        raise Exception("metrics failure")

    import importlib

    mod = importlib.import_module(
        "devsynth.application.cli.commands.alignment_metrics_cmd"
    )
    monkeypatch.setattr(mod, "calculate_alignment_coverage", _raise)


@then("the system should display alignment metrics")
def check_metrics_output(command_context):
    """Verify that alignment metrics were printed."""
    output = command_context.get("output", "")
    assert "Alignment Metrics" in output or "Metrics report" in output
