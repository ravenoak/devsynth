import click
import pytest
import typer
import typer.main
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.interface.ux_bridge import UXBridge


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if (
            origin in {UXBridge, typer.models.Context}
            or annotation is dict
            or origin is dict
        ):
            return click.STRING
        return orig(annotation=annotation, parameter_info=parameter_info)

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)


def test_mvuu_dashboard_help_succeeds():
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["mvuu-dashboard", "--help"])
    assert result.exit_code == 0
    assert "MVUU traceability dashboard" in result.output
