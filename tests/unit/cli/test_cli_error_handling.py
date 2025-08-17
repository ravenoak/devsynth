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
def test_main_handles_run_cli_errors(monkeypatch):
    def failing_run_cli():
        raise RuntimeError("boom")

    handled = {}

    def fake_handle_error(_bridge, err):
        handled["error"] = err

    monkeypatch.setattr("devsynth.adapters.cli.typer_adapter.run_cli", failing_run_cli)
    monkeypatch.setattr(
        "devsynth.application.cli.errors.handle_error", fake_handle_error
    )

    from devsynth.cli import main

    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 1
    assert isinstance(handled["error"], RuntimeError)
