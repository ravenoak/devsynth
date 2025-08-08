from pathlib import Path
from unittest.mock import MagicMock

import pytest

from devsynth.adapters.cli import typer_adapter


@pytest.mark.medium
def test_completion_cmd_outputs_script(monkeypatch):
    """completion_cmd outputs a completion script when not installing."""
    bridge = MagicMock()
    typer_adapter.completion_cmd(shell="bash", bridge=bridge)
    bridge.show_completion.assert_called_once()


@pytest.mark.medium
def test_completion_cmd_installs_script(tmp_path):
    """completion_cmd writes script to path when install=True."""
    bridge = MagicMock()
    target = tmp_path / "comp.sh"
    typer_adapter.completion_cmd(shell="bash", install=True, path=target, bridge=bridge)
    assert target.exists()
    bridge.show_completion.assert_called_once_with(str(target))
