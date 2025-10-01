import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.application.cli.autocomplete import generate_completion_script

# Resource gating: these tests exercise the CLI layer

pytestmark = pytest.mark.requires_resource("cli")


@pytest.mark.medium
def test_help_notes_include_completion_message():
    runner = CliRunner()
    result = runner.invoke(build_app(), ["--help"])
    assert result.exit_code == 0
    assert "Shell completion is available" in result.output


@pytest.mark.medium
def test_completion_command_outputs_script():
    runner = CliRunner()
    result = runner.invoke(build_app(), ["completion", "--shell", "bash"])
    assert result.exit_code == 0
    # The script should contain the environment variable used by Click for completion
    assert "_DEVSYNTH_COMPLETE" in result.output


@pytest.mark.medium
def test_generate_completion_script_returns_text():
    script = generate_completion_script("zsh")
    assert "devsynth" in script and len(script) > 0
