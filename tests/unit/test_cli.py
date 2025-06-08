from unittest.mock import patch

from typer.testing import CliRunner

from devsynth.adapters.cli.argparse_adapter import build_app


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
        assert "run" in result.output
        assert "config" in result.output

    @patch("devsynth.adapters.cli.argparse_adapter.init_cmd", autospec=True)
    def test_cli_init(self, mock_init_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["init", "--path", "./test-project"])
        assert result.exit_code == 0
        mock_init_cmd.assert_called_once_with("./test-project")

    @patch("devsynth.adapters.cli.argparse_adapter.spec_cmd", autospec=True)
    def test_cli_spec(self, mock_spec_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["spec", "--requirements-file", "reqs.md"])
        assert result.exit_code == 0
        mock_spec_cmd.assert_called_once_with("reqs.md")

    @patch("devsynth.adapters.cli.argparse_adapter.test_cmd", autospec=True)
    def test_cli_test(self, mock_test_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["test", "--spec-file", "specs.md"])
        assert result.exit_code == 0
        mock_test_cmd.assert_called_once_with("specs.md")

    @patch("devsynth.adapters.cli.argparse_adapter.code_cmd", autospec=True)
    def test_cli_code(self, mock_code_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["code"])
        assert result.exit_code == 0
        mock_code_cmd.assert_called_once_with()

    @patch("devsynth.adapters.cli.argparse_adapter.run_cmd", autospec=True)
    def test_cli_run(self, mock_run_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["run", "--target", "unit-tests"])
        assert result.exit_code == 0
        mock_run_cmd.assert_called_once_with("unit-tests")

    @patch("devsynth.adapters.cli.argparse_adapter.config_cmd", autospec=True)
    def test_cli_config(self, mock_config_cmd):
        app = build_app()
        result = self.runner.invoke(app, ["config", "--key", "model", "--value", "gpt-4"])
        assert result.exit_code == 0
        mock_config_cmd.assert_called_once_with("model", "gpt-4", False)
