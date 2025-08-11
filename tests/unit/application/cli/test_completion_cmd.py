from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from devsynth.adapters.cli import typer_adapter


@pytest.mark.medium
def test_completion_cmd_outputs_script(monkeypatch):
    """completion_cmd outputs a completion script when not installing."""
    bridge = MagicMock()
    monkeypatch.setattr(
        "devsynth.adapters.cli.typer_adapter.typer_completion.get_completion_script",
        lambda **_: "script",
    )
    typer_adapter.completion_cmd(shell="bash", bridge=bridge)
    bridge.show_completion.assert_called_once_with("script")


@pytest.mark.medium
def test_completion_cmd_installs_script(tmp_path, monkeypatch):
    """completion_cmd writes script to path when install=True."""
    bridge = MagicMock()
    target = tmp_path / "comp.sh"
    monkeypatch.setattr(
        "devsynth.adapters.cli.typer_adapter.typer_completion.get_completion_script",
        lambda **_: "script",
    )
    typer_adapter.completion_cmd(shell="bash", install=True, path=target, bridge=bridge)
    assert target.exists()
    bridge.show_completion.assert_called_once_with(str(target))


@pytest.mark.medium
def test_cli_supports_install_completion():
    """The Typer app exposes the --install-completion option."""
    runner = CliRunner()
    result = runner.invoke(typer_adapter.build_app(), ["--install-completion", "bash"])
    assert result.exit_code == 0
