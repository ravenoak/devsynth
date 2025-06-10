from unittest.mock import patch, mock_open

import pytest

from devsynth.application.cli.cli_commands import (
    code_cmd,
    config_cmd,
    init_cmd,
    run_cmd,
    spec_cmd,
    test_cmd,
    analyze_cmd,
)


class TestCLICommands:
    """Tests for the CLI command functions."""

    @pytest.fixture
    def mock_workflow_manager(self):
        """Create a mock workflow manager."""
        with patch("devsynth.application.cli.cli_commands.workflow_manager") as mock:
            yield mock

    @pytest.fixture
    def mock_console(self):
        """Create a mock console."""
        with patch("devsynth.application.cli.cli_commands.console") as mock:
            yield mock

    def test_init_cmd_success(self, mock_workflow_manager, mock_console):
        """Test successful project initialization."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Project initialized successfully",
        }

        # Execute
        init_cmd("./test-project")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "init", {"path": "./test-project"}
        )
        # Check that one of the print calls contains the expected message
        success_message = (
            "[green]Initialized DevSynth project in ./test-project[/green]"
        )
        assert any(
            call.args[0] == success_message
            for call in mock_console.print.call_args_list
        )

    def test_init_cmd_failure(self, mock_workflow_manager, mock_console):
        """Test failed project initialization."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": False,
            "message": "Path already exists",
        }

        # Execute
        init_cmd("./test-project")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "init", {"path": "./test-project"}
        )
        mock_console.print.assert_called_once_with(
            "[red]Error:[/red] Path already exists", highlight=False
        )

    def test_init_cmd_exception(self, mock_workflow_manager, mock_console):
        """Test exception handling in project initialization."""
        # Setup
        mock_workflow_manager.execute_command.side_effect = Exception("Test error")

        # Execute
        init_cmd("./test-project")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "init", {"path": "./test-project"}
        )
        mock_console.print.assert_called_once_with(
            "[red]Error:[/red] Test error", highlight=False
        )

    def test_spec_cmd_success(self, mock_workflow_manager, mock_console):
        """Test successful spec generation."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Specs generated successfully",
        }

        # Execute
        spec_cmd("requirements.md")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "spec", {"requirements_file": "requirements.md"}
        )
        # Check that one of the print calls contains the expected message
        success_message = (
            "[green]Specifications generated from requirements.md.[/green]"
        )
        assert any(
            call.args[0] == success_message
            for call in mock_console.print.call_args_list
        )

    def test_test_cmd_success(self, mock_workflow_manager, mock_console):
        """Test successful test generation."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Tests generated successfully",
        }

        # Execute
        test_cmd("specs.md")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "test", {"spec_file": "specs.md"}
        )
        # Check that one of the print calls contains the expected message
        success_message = "[green]Tests generated from specs.md.[/green]"
        assert any(
            call.args[0] == success_message
            for call in mock_console.print.call_args_list
        )

    def test_code_cmd_success(self, mock_workflow_manager, mock_console):
        """Test successful code generation."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Code generated successfully",
        }

        # Execute
        code_cmd()

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with("code", {})
        # Check that one of the print calls contains the expected message
        success_message = "[green]Code generated successfully.[/green]"
        assert any(
            call.args[0] == success_message
            for call in mock_console.print.call_args_list
        )

    def test_run_cmd_success_with_target(self, mock_workflow_manager, mock_console):
        """Test successful run with target."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Target executed successfully",
        }

        # Execute
        run_cmd("unit-tests")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "run", {"target": "unit-tests"}
        )
        mock_console.print.assert_called_once_with(
            "[green]Executed target: unit-tests[/green]"
        )

    def test_run_cmd_success_without_target(self, mock_workflow_manager, mock_console):
        """Test successful run without target."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Execution complete",
        }

        # Execute
        run_cmd()

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "run", {"target": None}
        )
        mock_console.print.assert_called_once_with("[green]Execution complete.[/green]")

    def test_config_cmd_set_value(self, mock_workflow_manager, mock_console):
        """Test setting a configuration value."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Configuration updated",
        }

        # Execute
        config_cmd("model", "gpt-4")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "config", {"key": "model", "value": "gpt-4"}
        )
        mock_console.print.assert_called_once_with(
            "[green]Configuration updated: model = gpt-4[/green]"
        )

    def test_config_cmd_get_value(self, mock_workflow_manager, mock_console):
        """Test getting a configuration value."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "value": "gpt-4",
        }

        # Execute
        config_cmd("model")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "config", {"key": "model", "value": None}
        )
        mock_console.print.assert_called_once_with("[blue]model:[/blue] gpt-4")

    def test_config_cmd_list_all(self, mock_workflow_manager, mock_console):
        """Test listing all configuration values."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "config": {"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000},
        }

        # Execute
        config_cmd()

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "config", {"key": None, "value": None}
        )
        assert mock_console.print.call_count == 4  # Header + 3 config items

    def test_init_cmd_with_name_template(self, mock_workflow_manager, mock_console):
        """Init command with additional parameters."""
        mock_workflow_manager.execute_command.return_value = {"success": True}
        init_cmd(path=".", name="proj", template="web-app")
        mock_workflow_manager.execute_command.assert_called_once_with(
            "init", {"path": ".", "name": "proj", "template": "web-app"}
        )

    @patch("devsynth.application.cli.cli_commands.Path.mkdir")
    @patch("devsynth.application.cli.cli_commands.yaml.safe_dump")
    @patch("builtins.open", new_callable=mock_open, read_data="projectName: ex")
    @patch("devsynth.application.cli.cli_commands.Confirm.ask")
    def test_init_cmd_writes_features(
        self,
        mock_confirm,
        mock_open_file,
        mock_yaml_dump,
        mock_mkdir,
        mock_workflow_manager,
        mock_console,
    ):
        """Init command writes feature flags to project.yaml."""
        mock_workflow_manager.execute_command.return_value = {"success": True}
        mock_confirm.side_effect = [True, False, False, False, False, False]

        init_cmd(path="./proj", name="proj")

        mock_workflow_manager.execute_command.assert_called_once_with(
            "init", {"path": "./proj", "name": "proj"}
        )
        assert mock_yaml_dump.called
        dumped = mock_yaml_dump.call_args[0][0]
        assert dumped["features"]["code_generation"] is True

    def test_analyze_cmd_file(self, mock_workflow_manager, mock_console):
        """Analyze command with input file."""
        mock_workflow_manager.execute_command.return_value = {"success": True}
        analyze_cmd("requirements.md")
        mock_workflow_manager.execute_command.assert_called_once_with(
            "analyze", {"input": "requirements.md"}
        )

    def test_analyze_cmd_interactive(self, mock_workflow_manager, mock_console):
        """Analyze command in interactive mode."""
        mock_workflow_manager.execute_command.return_value = {"success": True}
        analyze_cmd(interactive=True)
        mock_workflow_manager.execute_command.assert_called_once_with(
            "analyze", {"interactive": True}
        )
