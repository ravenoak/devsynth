from pathlib import Path
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.application.cli.cli_commands import init_cmd
from devsynth.interface.cli import CLIUXBridge
import pytest
from unittest.mock import patch


def _run_init(tmp_path, monkeypatch, *, use_pyproject=False):
    """Helper to run init_cmd with patched bridge."""
    monkeypatch.chdir(tmp_path)
    answers = iter([str(tmp_path), 'python', 'do stuff', 'memory'])
    confirms = iter([False, False, False, False, False, False, False, True])
    monkeypatch.setattr('devsynth.interface.cli.Prompt.ask', lambda *a, **k:
        next(answers))
    monkeypatch.setattr('devsynth.interface.cli.Confirm.ask', lambda *a, **
        k: next(confirms))
    printed = []
    monkeypatch.setattr('rich.console.Console.print', lambda self, msg, *,
        highlight=False: printed.append(msg))
    if use_pyproject:
        (tmp_path / 'pyproject.toml').write_text('')
    bridge = CLIUXBridge()
    init_cmd(bridge=bridge)
    return printed


def _load_config(path: Path):
    root = (path.parent.parent if path.parent.name == '.devsynth' else path
        .parent)
    return UnifiedConfigLoader.load(root).config.as_dict()


def test_init_cmd_creates_config_succeeds(tmp_path, monkeypatch):
    """Test that init cmd creates config succeeds.

ReqID: N/A"""
    printed = _run_init(tmp_path, monkeypatch)
    cfg_file = tmp_path / '.devsynth' / 'project.yaml'
    if not cfg_file.exists():
        cfg_file = tmp_path / '.devsynth' / 'project.yaml'
    if not cfg_file.exists():
        cfg_file = tmp_path / 'pyproject.toml'
    data = _load_config(cfg_file)
    assert data['project_root'] == str(tmp_path)
    assert data['language'] == 'python'
    assert data['goals'] == 'do stuff'
    assert data['memory_store_type'] == 'memory'
    assert data['offline_mode'] is False
    assert any('Initialization complete' in msg for msg in printed)


def test_init_cmd_idempotent_succeeds(tmp_path, monkeypatch):
    """Test that init cmd idempotent succeeds.

ReqID: N/A"""
    _run_init(tmp_path, monkeypatch)
    printed = _run_init(tmp_path, monkeypatch)
    assert any('Project already initialized' in msg for msg in printed)


def test_init_cmd_wizard_option_invokes_setup(monkeypatch):
    """--wizard flag should run the SetupWizard."""

    with patch('devsynth.application.cli.setup_wizard.SetupWizard') as wiz:
        init_cmd(wizard=True)
        wiz.assert_called_once()
        wiz.return_value.run.assert_called_once()


def test_cli_help_lists_renamed_commands_succeeds(capsys, monkeypatch):
    """Verify CLI help shows updated command names.

ReqID: N/A"""
    from devsynth.adapters.cli import typer_adapter
    from devsynth.interface.ux_bridge import UXBridge
    import click
    import typer
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context}:
            return click.STRING
        origin = getattr(annotation, '__origin__', None)
        if origin in {UXBridge, typer.models.Context, dict
            } or annotation is dict:
            return click.STRING
        return orig(annotation=annotation, parameter_info=parameter_info)
    monkeypatch.setattr(typer.main, 'get_click_type', patched_get_click_type)
    monkeypatch.setattr(typer_adapter, '_warn_if_features_disabled', lambda :
        None)
    with pytest.raises(SystemExit) as exc:
        typer_adapter.parse_args(['--help'])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    lines = [line.strip() for line in output.splitlines()]
    assert 'refactor' in output
    assert 'inspect' in output
    assert 'run-pipeline' in output
    assert all(not line.startswith('adaptive') for line in lines)
    assert all(not line.startswith('analyze ') and ' analyze ' not in line for
        line in lines)
