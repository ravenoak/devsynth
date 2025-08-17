import io

import pytest

from devsynth.application.cli.cli_commands import completion_cmd
from devsynth.interface.cli import CLIUXBridge


@pytest.mark.fast
def test_completion_cmd_outputs_script_and_progress(capsys):
    """completion_cmd should print progress and the script."""
    bridge = CLIUXBridge()
    completion_cmd(shell="bash", bridge=bridge)
    captured = capsys.readouterr().out
    assert "devsynth" in captured
    assert "generating completion script" in captured.lower()
