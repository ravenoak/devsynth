from unittest.mock import patch

import click
import typer
import typer.main
from typer.testing import CliRunner
import pytest

pytest.skip("Typer CLI tests skipped", allow_module_level=True)

from devsynth.adapters.cli.typer_adapter import build_app
from devsynth.interface.ux_bridge import UXBridge


@pytest.fixture(autouse=True)
def patch_typer_types(monkeypatch):
    """Allow Typer to handle custom parameter types used in the CLI."""

    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):
        if annotation in {UXBridge, typer.models.Context}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if origin in {UXBridge, typer.models.Context}:
            return click.STRING
        if annotation is dict or origin is dict:
            return click.STRING
        return orig(annotation=annotation, parameter_info=parameter_info)

    monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)


class TestTyperCLI:
    """Tests for the Typer-based CLI."""

    runner = CliRunner()

    def test_show_help(self):
        app = build_app()
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "DevSynth CLI" in result.output
        assert "init" in result.output
        assert "spec" in result.output
        assert "test" in result.output
        assert "code" in result.output
        assert "run-pipeline" in result.output
        assert "config" in result.output

    @patch("devsynth.adapters.cli.typer_adapter.init_cmd", autospec=True)
    def test_cli_init(self, mock_init_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["init", "--path", "./test-project"])
        assert result.exit_code == 0
        mock_init_cmd.assert_called_once_with(
            "./test-project",
            None,
            None,
            None,
            None,
            None,
            None,
            bridge=None,
        )

    @patch("devsynth.adapters.cli.typer_adapter.spec_cmd", autospec=True)
    def test_cli_spec(self, mock_spec_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["spec", "--requirements-file", "reqs.md"])
        assert result.exit_code == 0
        mock_spec_cmd.assert_called_once_with("reqs.md", bridge=None)

    @patch("devsynth.adapters.cli.typer_adapter.test_cmd", autospec=True)
    def test_cli_test(self, mock_test_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["test", "--spec-file", "specs.md"])
        assert result.exit_code == 0
        mock_test_cmd.assert_called_once_with("specs.md", bridge=None)

    @patch("devsynth.adapters.cli.typer_adapter.code_cmd", autospec=True)
    def test_cli_code(self, mock_code_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["code"])
        assert result.exit_code == 0
        mock_code_cmd.assert_called_once_with(bridge=None)

    @patch("devsynth.adapters.cli.typer_adapter.run_pipeline_cmd", autospec=True)
    def test_cli_run(self, mock_run_pipeline_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["run-pipeline", "--target", "unit-tests"])
        assert result.exit_code == 0
        mock_run_pipeline_cmd.assert_called_once_with("unit-tests", bridge=None)

    def test_cli_config(self):
        app = build_app()
        result = self.runner.invoke(
            app, ["config", "--key", "model", "--value", "gpt-4"]
        )
        assert result.exit_code == 0
        assert "Configuration updated" in result.output

    def test_cli_enable_feature(self):
        app = build_app()
        result = self.runner.invoke(
            app, ["config", "enable-feature", "code_generation"]
        )
        assert result.exit_code == 0

    def test_cli_edrr_cycle(self):
        app = build_app()
        result = self.runner.invoke(app, ["edrr-cycle", "path/to/manifest.yaml"])
        assert result.exit_code == 0

    @patch("devsynth.adapters.cli.typer_adapter.inspect_config_cmd", autospec=True)
    def test_cli_inspect_config_update(self, mock_cmd):
        app = build_app()
        result = self.runner.invoke(
            app,
            [
                "inspect-config",
                "--path",
                "./proj",
                "--update",
            ],
        )
        assert result.exit_code == 0
        mock_cmd.assert_called_once_with("./proj", True, False)

    @patch("devsynth.adapters.cli.typer_adapter.inspect_config_cmd", autospec=True)
    def test_cli_inspect_config_prune(self, mock_cmd):
        app = build_app()
        result = self.runner.invoke(
            app,
            [
                "inspect-config",
                "--path",
                "./proj",
                "--prune",
            ],
        )
        assert result.exit_code == 0
        mock_cmd.assert_called_once_with("./proj", False, True)

    @patch("devsynth.application.cli.cli_commands._check_services", return_value=True)
    @patch(
        "devsynth.application.cli.cli_commands.generate_specs",
        side_effect=FileNotFoundError("missing"),
    )
    def test_cli_spec_invalid_file(self, *_):
        app = build_app()
        result = self.runner.invoke(app, ["spec", "--requirements-file", "bad.md"])
        assert result.exit_code == 0
        assert "Error: missing" in result.output

    @patch(
        "devsynth.application.cli.cli_commands.workflows.execute_command",
        return_value={"success": False, "message": "config missing"},
    )
    def test_cli_config_missing(self, *_):
        app = build_app()
        result = self.runner.invoke(app, ["config", "--key", "model"])
        assert result.exit_code == 0
        assert "config missing" in result.output

    def test_parse_args_help_has_new_commands(self, capsys, monkeypatch):
        from devsynth.adapters.cli import typer_adapter as adapter

        def patched_get_click_type(*, annotation, parameter_info):
            if annotation in {UXBridge, typer.models.Context}:
                return click.STRING
            origin = getattr(annotation, "__origin__", None)
            if origin in {UXBridge, typer.models.Context, dict} or annotation is dict:
                return click.STRING
            return orig(annotation=annotation, parameter_info=parameter_info)

        orig = typer.main.get_click_type
        monkeypatch.setattr(typer.main, "get_click_type", patched_get_click_type)
        monkeypatch.setattr(adapter, "_warn_if_features_disabled", lambda: None)

        with pytest.raises(SystemExit) as exc:
            adapter.parse_args(["--help"])
        assert exc.value.code == 0
        output = capsys.readouterr().out
        assert "refactor" in output
        assert "inspect" in output
        assert "run-pipeline" in output
        lines = [line.strip() for line in output.splitlines()]
        assert all(not line.startswith("adaptive") for line in lines)
        assert all(
            not line.startswith("analyze ") and " analyze " not in line
            for line in lines
        )
