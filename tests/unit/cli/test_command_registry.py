import typer
from typer.testing import CliRunner

import devsynth.adapters.cli.typer_adapter as adapter


def test_build_app_registers_commands_from_registry(monkeypatch):
    """Commands in COMMAND_REGISTRY should be registered with the CLI."""
    called = {}

    def sample_cmd():
        called["ran"] = True

    monkeypatch.setattr(adapter, "COMMAND_REGISTRY", {"sample": sample_cmd})
    monkeypatch.setattr(adapter, "config_app", typer.Typer())
    monkeypatch.setattr(adapter, "requirements_app", typer.Typer())
    monkeypatch.setattr(adapter, "_patch_typer_types", lambda: None)

    app = adapter.build_app()
    result = CliRunner().invoke(app, ["sample"])
    assert result.exit_code == 0
    assert called.get("ran")


def test_enable_feature_not_top_level():
    """The enable-feature command is managed under config and not at top level."""
    app = adapter.build_app()
    result = CliRunner().invoke(app, ["--help"])
    assert "enable-feature" not in result.output
