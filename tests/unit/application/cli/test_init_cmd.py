"""Tests for the ``init`` CLI command and related help output."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
import typer

from devsynth.adapters.cli import typer_adapter
from devsynth.application.cli.cli_commands import init_cmd
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


def _run_init(
    tmp_path,
    monkeypatch,
    *,
    use_pyproject: bool = False,
    metrics_dashboard: bool = False,
):
    """Run ``init_cmd`` with patched prompts and confirmations.

    This helper simulates user interaction by monkeypatching the ``Prompt`` and
    ``Confirm`` calls used by the command. It returns any messages printed to
    the console so tests can assert against them.
    """

    monkeypatch.chdir(tmp_path)

    answers = iter([str(tmp_path), "python", "do stuff", "memory"])
    monkeypatch.setattr(
        "devsynth.interface.cli.Prompt.ask", lambda *a, **k: next(answers)
    )

    def mock_confirm(prompt, *args, **kwargs):
        text = str(prompt)
        if "offline" in text.lower():
            return False
        return True

    monkeypatch.setattr("devsynth.interface.cli.Confirm.ask", mock_confirm)

    printed: list[str] = []
    monkeypatch.setattr(
        "rich.console.Console.print",
        lambda self, msg="", *a, **k: printed.append(str(msg)),
    )

    if use_pyproject:
        (tmp_path / "pyproject.toml").write_text("")

    bridge = CLIUXBridge()
    init_cmd(metrics_dashboard=metrics_dashboard, bridge=bridge)

    return printed


def _load_config(path: Path) -> dict:
    """Load project configuration for the given path."""

    root = path.parent.parent if path.parent.name == ".devsynth" else path.parent
    return UnifiedConfigLoader.load(root).config.as_dict()


@pytest.mark.medium
def test_init_cmd_creates_config_succeeds(tmp_path, monkeypatch):
    """Init command creates configuration when none exists."""

    printed = _run_init(tmp_path, monkeypatch)

    cfg_file = tmp_path / ".devsynth" / "project.yaml"
    if not cfg_file.exists():
        cfg_file = tmp_path / "pyproject.toml"

    data = _load_config(cfg_file)

    assert data["project_root"] == str(tmp_path)
    assert data["language"] == "python"
    assert data["goals"] == "do stuff"
    assert data["memory_store_type"] == "memory"
    assert data["offline_mode"] is False
    assert any("Initialization complete" in msg for msg in printed)


@pytest.mark.medium
def test_init_cmd_idempotent_succeeds(tmp_path, monkeypatch):
    """Running init twice reports project already initialized."""

    _run_init(tmp_path, monkeypatch)
    printed = _run_init(tmp_path, monkeypatch)

    assert any("Project already initialized" in msg for msg in printed)


@pytest.mark.medium
def test_init_cmd_metrics_dashboard_option(tmp_path, monkeypatch):
    """``--metrics-dashboard`` prints dashboard instructions."""

    printed = _run_init(tmp_path, monkeypatch, metrics_dashboard=True)

    assert any("mvuu-dashboard" in msg for msg in printed)
    assert any("mvuu_dashboard: true" in msg for msg in printed)


@pytest.mark.medium
def test_init_cmd_wizard_option_invokes_setup(monkeypatch):
    """``--wizard`` flag runs the interactive ``SetupWizard``."""

    with patch("devsynth.application.cli.setup_wizard.SetupWizard") as wiz:
        init_cmd(wizard=True)
        wiz.assert_called_once()
        wiz.return_value.run.assert_called_once()


@pytest.mark.medium
def test_init_cmd_reports_progress(tmp_path, monkeypatch):
    """Init command reports progress steps."""

    monkeypatch.chdir(tmp_path)

    answers = iter([str(tmp_path), "python", "do stuff", "memory"])
    monkeypatch.setattr(
        "devsynth.interface.cli.Prompt.ask", lambda *a, **k: next(answers)
    )
    monkeypatch.setattr("devsynth.interface.cli.Confirm.ask", lambda *a, **k: False)

    class DummyProgress:
        def __init__(self) -> None:
            self.calls: list[dict] = []
            self.completed = False

        def update(self, **kwargs) -> None:
            self.calls.append(kwargs)

        def complete(self) -> None:
            self.completed = True

    progress = DummyProgress()

    monkeypatch.setattr("rich.console.Console.print", lambda self, *a, **k: None)

    bridge = CLIUXBridge()
    monkeypatch.setattr(bridge, "create_progress", lambda desc, total: progress)

    init_cmd(bridge=bridge)

    assert progress.calls[0]["description"] == "Saving configuration"
    assert progress.calls[0]["status"] == "writing config"
    assert progress.calls[1]["description"] == "Generating project files"
    assert progress.calls[1]["status"] == "scaffolding"
    assert progress.completed


@pytest.mark.medium
def test_init_cmd_defaults_non_interactive_skips_prompts(tmp_path, monkeypatch):
    """``--defaults`` and ``--non-interactive`` skip prompts and use defaults."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DEVSYNTH_NONINTERACTIVE", raising=False)

    bridge = CLIUXBridge()
    bridge.ask_question = MagicMock()
    bridge.confirm_choice = MagicMock()

    printed: list[str] = []
    monkeypatch.setattr(
        "rich.console.Console.print",
        lambda self, msg="", *a, **k: printed.append(str(msg)),
    )

    init_cmd(defaults=True, non_interactive=True, bridge=bridge)

    cfg_file = tmp_path / ".devsynth" / "project.yaml"
    data = _load_config(cfg_file)

    assert data["project_root"] == str(tmp_path)
    assert data["language"] == "python"
    assert data["goals"] == ""
    assert data["memory_store_type"] == "memory"
    assert data["offline_mode"] is False
    bridge.ask_question.assert_not_called()
    bridge.confirm_choice.assert_not_called()
    assert any("Initialization complete" in msg for msg in printed)


@pytest.mark.medium
def test_init_cmd_env_non_interactive_skips_prompts(tmp_path, monkeypatch):
    """Environment variables trigger non-interactive defaults."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEVSYNTH_NONINTERACTIVE", "1")
    monkeypatch.setenv("DEVSYNTH_AUTO_CONFIRM", "1")

    bridge = CLIUXBridge()
    bridge.ask_question = MagicMock()
    bridge.confirm_choice = MagicMock()

    printed: list[str] = []
    monkeypatch.setattr(
        "rich.console.Console.print",
        lambda self, msg="", *a, **k: printed.append(str(msg)),
    )

    init_cmd(bridge=bridge)

    cfg_file = tmp_path / ".devsynth" / "project.yaml"
    data = _load_config(cfg_file)

    assert data["project_root"] == str(tmp_path)
    assert data["language"] == "python"
    assert data["goals"] == ""
    assert data["memory_store_type"] == "memory"
    assert data["offline_mode"] is False
    bridge.ask_question.assert_not_called()
    bridge.confirm_choice.assert_not_called()
    assert any("Initialization complete" in msg for msg in printed)


@pytest.mark.medium
def test_cli_help_lists_renamed_commands_succeeds(capsys, monkeypatch):
    """``devsynth --help`` lists renamed commands and omits old ones."""

    orig_get_click_type = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):  # pragma: no cover
        if annotation in {UXBridge, typer.models.Context, object}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if origin in {UXBridge, typer.models.Context, dict, list}:
            return click.STRING
        if annotation in {dict, list}:
            return click.STRING
        return orig_get_click_type(annotation=annotation, parameter_info=parameter_info)

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)
    monkeypatch.setattr(typer_adapter, "_warn_if_features_disabled", lambda: None)

    with pytest.raises(SystemExit) as exc:
        typer_adapter.parse_args(["--help"])
    assert exc.value.code == 0

    output = capsys.readouterr().out
    lines = [line.strip() for line in output.splitlines()]

    assert "refactor" in output
    assert "inspect" in output
    assert "run-pipeline" in output
    assert all(not line.startswith("adaptive") for line in lines)
    assert all(
        not line.startswith("analyze ") and " analyze " not in line for line in lines
    )
