import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import app


@pytest.mark.fast
def test_cli_help_exits_zero_and_shows_summary():
    """Verify that `devsynth --help` exits with code 0 and displays help text.

    This test satisfies docs/tasks.md item 14: "Verify help output: poetry run devsynth --help exits 0".
    It uses Typer's CliRunner to simulate invoking the CLI with the --help flag.
    """
    runner = CliRunner()
    result = runner.invoke(
        app, ["--help"]
    )  # Typer returns SystemExit(0) translated to exit_code 0

    # Exit code should be zero for help output
    assert (
        result.exit_code == 0
    ), f"Expected exit code 0, got {result.exit_code}: {result.output}"

    # Help text should contain a recognizable summary string
    assert "DevSynth CLI" in result.output or "Usage:" in result.output, (
        "Expected help output to contain CLI summary or usage section.\n"
        f"Output was:\n{result.output}"
    )
