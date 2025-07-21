"""Steps for the alignment metrics command feature."""

from pytest_bdd import scenarios, given, then

from .cli_commands_steps import run_command  # noqa: F401

scenarios("../features/alignment_metrics_command.feature")


@given("alignment metrics calculation fails")
def metrics_fail(monkeypatch):
    """Force the alignment metrics command to raise an exception."""
    def _raise(*_args, **_kwargs):
        raise Exception("metrics failure")

    monkeypatch.setattr(
        "devsynth.application.cli.commands.alignment_metrics_cmd.calculate_alignment_coverage",
        _raise,
    )


@then("the system should display alignment metrics")
def check_metrics_output(command_context):
    """Verify that alignment metrics were printed."""
    output = command_context.get("output", "")
    assert "Alignment Metrics" in output or "Metrics report" in output
