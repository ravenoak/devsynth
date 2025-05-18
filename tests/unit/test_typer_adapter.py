import sys
from unittest.mock import patch

import pytest

from devsynth.adapters.cli.typer_adapter import parse_args, run_cli, show_help


class TestTyperAdapter:
    """Tests for the Typer CLI adapter."""

    def test_show_help(self, capsys):
        """Test that show_help displays the correct information."""
        show_help()
        captured = capsys.readouterr()

        # Check that the output contains expected elements
        assert "DevSynth CLI" in captured.out
        assert "Commands:" in captured.out
        assert "init" in captured.out
        assert "spec" in captured.out
        assert "test" in captured.out
        assert "code" in captured.out
        assert "run" in captured.out
        assert "config" in captured.out
        assert "help" in captured.out

    def test_parse_args_init(self):
        """Test parsing init command arguments."""
        args = parse_args(["init", "--path", "./test-project"])
        assert args.command == "init"
        assert args.path == "./test-project"

    def test_parse_args_spec(self):
        """Test parsing spec command arguments."""
        args = parse_args(["spec", "--requirements-file", "custom-reqs.md"])
        assert args.command == "spec"
        assert args.requirements_file == "custom-reqs.md"

    def test_parse_args_test(self):
        """Test parsing test command arguments."""
        args = parse_args(["test", "--spec-file", "custom-specs.md"])
        assert args.command == "test"
        assert args.spec_file == "custom-specs.md"

    def test_parse_args_code(self):
        """Test parsing code command arguments."""
        args = parse_args(["code"])
        assert args.command == "code"

    def test_parse_args_run(self):
        """Test parsing run command arguments."""
        args = parse_args(["run", "--target", "unit-tests"])
        assert args.command == "run"
        assert args.target == "unit-tests"

    def test_parse_args_config(self):
        """Test parsing config command arguments."""
        args = parse_args(["config", "--key", "model", "--value", "gpt-4"])
        assert args.command == "config"
        assert args.key == "model"
        assert args.value == "gpt-4"

    @patch("devsynth.adapters.cli.typer_adapter.init_cmd")
    def test_run_cli_init(self, mock_init_cmd):
        """Test running the CLI with init command."""
        with patch.object(sys, 'argv', ['devsynth', 'init', '--path', './test-project']):
            run_cli()
            mock_init_cmd.assert_called_once_with('./test-project')

    @patch("devsynth.adapters.cli.typer_adapter.spec_cmd")
    def test_run_cli_spec(self, mock_spec_cmd):
        """Test running the CLI with spec command."""
        with patch.object(sys, 'argv', ['devsynth', 'spec', '--requirements-file', 'reqs.md']):
            run_cli()
            mock_spec_cmd.assert_called_once_with('reqs.md')

    @patch("devsynth.adapters.cli.typer_adapter.test_cmd")
    def test_run_cli_test(self, mock_test_cmd):
        """Test running the CLI with test command."""
        with patch.object(sys, 'argv', ['devsynth', 'test', '--spec-file', 'specs.md']):
            run_cli()
            mock_test_cmd.assert_called_once_with('specs.md')

    @patch("devsynth.adapters.cli.typer_adapter.code_cmd")
    def test_run_cli_code(self, mock_code_cmd):
        """Test running the CLI with code command."""
        with patch.object(sys, 'argv', ['devsynth', 'code']):
            run_cli()
            mock_code_cmd.assert_called_once()

    @patch("devsynth.adapters.cli.typer_adapter.run_cmd")
    def test_run_cli_run(self, mock_run_cmd):
        """Test running the CLI with run command."""
        with patch.object(sys, 'argv', ['devsynth', 'run', '--target', 'unit-tests']):
            run_cli()
            mock_run_cmd.assert_called_once_with('unit-tests')

    @patch("devsynth.adapters.cli.typer_adapter.config_cmd")
    def test_run_cli_config(self, mock_config_cmd):
        """Test running the CLI with config command."""
        with patch.object(sys, 'argv', ['devsynth', 'config', '--key', 'model', '--value', 'gpt-4']):
            run_cli()
            mock_config_cmd.assert_called_once_with('model', 'gpt-4', False)

    @patch("devsynth.adapters.cli.typer_adapter.show_help")
    def test_run_cli_help(self, mock_show_help):
        """Test running the CLI with help command."""
        with patch.object(sys, 'argv', ['devsynth', 'help']):
            run_cli()
            mock_show_help.assert_called_once()

    @patch("devsynth.adapters.cli.typer_adapter.show_help")
    def test_run_cli_no_args(self, mock_show_help):
        """Test running the CLI with no arguments."""
        with patch.object(sys, 'argv', ['devsynth']):
            run_cli()
            mock_show_help.assert_called_once()

    @patch("devsynth.adapters.cli.typer_adapter.show_help")
    def test_run_cli_invalid_command(self, mock_show_help):
        """Test running the CLI with an invalid command."""
        with patch.object(sys, 'argv', ['devsynth', 'invalid']):
            run_cli()
            mock_show_help.assert_called_once()

    @patch("devsynth.adapters.cli.typer_adapter.init_cmd")
    def test_run_cli_error_handling(self, mock_init_cmd):
        """Test error handling in the CLI."""
        mock_init_cmd.side_effect = Exception("Test error")

        with patch.object(sys, 'argv', ['devsynth', 'init']):
            with pytest.raises(SystemExit) as excinfo:
                run_cli()

            assert excinfo.value.code == 1
