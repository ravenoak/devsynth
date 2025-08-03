from unittest.mock import patch
import click
import typer
import typer.main
from typer.testing import CliRunner
import pytest
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
    """Tests for the Typer-based CLI.

    ReqID: N/A"""

    runner = CliRunner()

    @pytest.mark.medium
    def test_show_help_succeeds(self):
        """Test that show help succeeds.

        ReqID: N/A"""
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
    def test_cli_init_succeeds(self, mock_init_cmd):
        """Test that cli init succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ["init"])
        assert result.exit_code == 0
        mock_init_cmd.assert_called_once_with(wizard=False, bridge=None)

    @patch("devsynth.adapters.cli.typer_adapter.spec_cmd", autospec=True)
    def test_cli_spec_succeeds(self, mock_spec_cmd):
        """Test that cli spec succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ["spec", "--requirements-file", "reqs.md"])
        assert result.exit_code == 0
        mock_spec_cmd.assert_called_once_with("reqs.md", bridge=None)

    @patch("devsynth.adapters.cli.typer_adapter.test_cmd", autospec=True)
    def test_cli_test_succeeds(self, mock_test_cmd):
        """Test that cli test succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ["test", "--spec-file", "specs.md"])
        assert result.exit_code == 0
        mock_test_cmd.assert_called_once_with("specs.md", bridge=None)

    @patch("devsynth.adapters.cli.typer_adapter.code_cmd", autospec=True)
    def test_cli_code_succeeds(self, mock_code_cmd):
        """Test that cli code succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ["code"])
        assert result.exit_code == 0
        mock_code_cmd.assert_called_once_with(bridge=None)

    @patch("devsynth.adapters.cli.typer_adapter.run_pipeline_cmd", autospec=True)
    def test_cli_run_succeeds(self, mock_run_pipeline_cmd):
        """Test that cli run succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ["run-pipeline", "--target", "unit-tests"])
        assert result.exit_code == 0
        mock_run_pipeline_cmd.assert_called_once_with(
            target="unit-tests", report=None, bridge=None
        )

    def test_cli_config_succeeds(self):
        """Test that cli config succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(
            app, ["config", "--key", "model", "--value", "gpt-4"]
        )
        assert result.exit_code == 0
        assert "Configuration updated" in result.output

    def test_cli_enable_feature_succeeds(self):
        """Test that cli enable feature succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(
            app, ["config", "enable-feature", "code_generation"]
        )
        assert result.exit_code == 0

    def test_cli_edrr_cycle_succeeds(self):
        """Test that cli edrr cycle succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(
            app, ["edrr-cycle", "--manifest", "path/to/manifest.yaml"]
        )
        assert result.exit_code == 0

    @patch("devsynth.adapters.cli.typer_adapter.inspect_config_cmd", autospec=True)
    def test_cli_inspect_config_update_succeeds(self, mock_cmd):
        """Test that cli inspect config update succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(
            app, ["inspect-config", "--path", "./proj", "--update"]
        )
        assert result.exit_code == 0
        mock_cmd.assert_called_once_with("./proj", True, False)

    @patch("devsynth.adapters.cli.typer_adapter.inspect_config_cmd", autospec=True)
    def test_cli_inspect_config_prune_succeeds(self, mock_cmd):
        """Test that cli inspect config prune succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(
            app, ["inspect-config", "--path", "./proj", "--prune"]
        )
        assert result.exit_code == 0
        mock_cmd.assert_called_once_with("./proj", False, True)

    @patch("devsynth.application.cli.cli_commands._check_services", return_value=True)
    @patch(
        "devsynth.application.cli.cli_commands.generate_specs",
        side_effect=FileNotFoundError("missing"),
    )
    def test_cli_spec_invalid_file_succeeds(self, *_):
        """Test that cli spec invalid file succeeds.

        ReqID: N/A"""
        app = build_app()
        env = {"DEVSYNTH_AUTO_CONFIRM": "1"}
        result = self.runner.invoke(
            app, ["spec", "--requirements-file", "bad.md"], env=env
        )
        assert result.exit_code == 0
        assert "missing" in result.output

    @patch(
        "devsynth.application.cli.cli_commands.workflows.execute_command",
        return_value={"success": False, "message": "config missing"},
    )
    def test_cli_config_missing_succeeds(self, *_):
        """Test that cli config missing succeeds.

        ReqID: N/A"""
        app = build_app()
        result = self.runner.invoke(app, ["config", "--key", "model"])
        assert result.exit_code == 0
        assert "config missing" in result.output

    def test_parse_args_help_has_new_commands_succeeds(self, capsys, monkeypatch):
        """Test that parse args help has new commands succeeds.

        ReqID: N/A"""
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
