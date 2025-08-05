import click
import pytest
import typer
import typer.main
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.interface.ux_bridge import UXBridge


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    """Allow Typer to handle custom parameter types."""
    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context} or annotation is object:
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


def test_mvu_lint_cli_success(monkeypatch):
    """CLI should report success when no errors are returned."""
    runner = CliRunner()
    app = build_app()
    monkeypatch.setattr(
        "devsynth.application.cli.commands.mvu_lint_cmd.mvuu_enforcement_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.mvu_lint_cmd.lint_range",
        lambda _rev: [],
    )
    result = runner.invoke(app, ["mvu", "lint"])
    assert result.exit_code == 0
    assert "All commit messages valid" in result.output


def test_mvu_lint_cli_failure(monkeypatch):
    """CLI should exit with error when linter reports problems."""
    runner = CliRunner()
    app = build_app()
    monkeypatch.setattr(
        "devsynth.application.cli.commands.mvu_lint_cmd.mvuu_enforcement_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.mvu_lint_cmd.lint_range",
        lambda _rev: ["abc123: error"],
    )
    result = runner.invoke(app, ["mvu", "lint"])
    assert result.exit_code == 1
    assert "abc123" in result.output


def test_mvu_lint_cli_skips_when_flag_disabled(monkeypatch):
    """CLI should skip linting when MVUU enforcement is disabled."""
    runner = CliRunner()
    app = build_app()

    def fail_if_called(*_args, **_kwargs):  # pragma: no cover - safety
        raise AssertionError("lint_range should not be called when disabled")

    monkeypatch.setattr(
        "devsynth.application.cli.commands.mvu_lint_cmd.mvuu_enforcement_enabled",
        lambda: False,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.mvu_lint_cmd.lint_range",
        fail_if_called,
    )
    result = runner.invoke(app, ["mvu", "lint"])
    assert result.exit_code == 0
    assert "MVUU enforcement disabled" in result.output
