import click
import pytest
import typer
import typer.main

from devsynth.interface.ux_bridge import UXBridge


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if origin in {UXBridge, typer.models.Context}:
            return click.STRING
        return orig(annotation=annotation, parameter_info=parameter_info)

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)


@pytest.mark.fast
def test_get_command_help_includes_examples():
    from devsynth.application.cli.help import get_command_help

    text = get_command_help("check")
    assert "devsynth check" in text


@pytest.mark.fast
def test_get_command_help_unknown_command():
    from devsynth.application.cli.help import get_command_help

    text = get_command_help("unknown")
    assert "Command: unknown" in text
    assert "Command not found" in text
