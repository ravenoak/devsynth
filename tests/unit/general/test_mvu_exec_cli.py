import subprocess

import click
import pytest
import typer.main
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.interface.ux_bridge import UXBridge

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    """Allow Typer to handle custom parameter types."""

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


def test_mvu_exec_cli_success(monkeypatch):
    """CLI should output combined streams on success."""

    def fake_run(cmd, capture_output, text):
        class Result:
            returncode = 0
            stdout = "hi"
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["mvu", "exec", "echo", "hi"])
    assert result.exit_code == 0
    assert "hi" in result.output


def test_mvu_exec_cli_failure(monkeypatch):
    """CLI should propagate non-zero exit codes."""

    def fake_run(cmd, capture_output, text):
        class Result:
            returncode = 1
            stdout = ""
            stderr = "err"

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = CliRunner()
    app = build_app()
    result = runner.invoke(app, ["mvu", "exec", "cmd"])
    assert result.exit_code == 1
    assert "err" in result.output
