import io
from devsynth.interface.cli import CLIUXBridge
from devsynth.application.cli.cli_commands import completion_cmd


def test_completion_cmd_outputs_script_and_progress(capsys):
    """completion_cmd should print progress and the script."""
    bridge = CLIUXBridge()
    completion_cmd(shell="bash", bridge=bridge)
    captured = capsys.readouterr().out
    assert "devsynth" in captured
    assert "generating completion script" in captured.lower()
