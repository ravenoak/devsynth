from unittest.mock import patch

import pytest

from devsynth.application.cli.cli_commands import (code_cmd, config_cmd, init_cmd, run_cmd, spec_cmd, test_cmd)


class TestCLICommands:
    """Tests for the CLI command functions."""

    @pytest.fixture
    def mock_workflow_manager(self):
        """Create a mock workflow manager."""
        with patch('devsynth.application.cli.cli_commands.workflow_manager') as mock:
            yield mock

    @pytest.fixture
    def mock_console(self):
        """Create a mock console."""
        with patch('devsynth.application.cli.cli_commands.console') as mock:
            yield mock

    def test_init_cmd_success(self, mock_workflow_manager, mock_console):
        """Test successful project initialization."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Project initialized successfully"
        }

        # Execute
        init_cmd("./test-project")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "init", {"path": "./test-project"}
        )
        mock_console.print.assert_called_once_with(
            "[green]Initialized DevSynth project in ./test-project[/green]"
        )

    def test_init_cmd_failure(self, mock_workflow_manager, mock_console):
        """Test failed project initialization."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": False,
            "message": "Path already exists"
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
            "message": "Specs generated successfully"
        }

        # Execute
        spec_cmd("requirements.md")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "spec", {"requirements_file": "requirements.md"}
        )
        mock_console.print.assert_called_once_with(
            "[green]Specifications generated from requirements.md.[/green]"
        )

    def test_test_cmd_success(self, mock_workflow_manager, mock_console):
        """Test successful test generation."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Tests generated successfully"
        }

        # Execute
        test_cmd("specs.md")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "test", {"spec_file": "specs.md"}
        )
        mock_console.print.assert_called_once_with(
            "[green]Tests generated from specs.md.[/green]"
        )

    def test_code_cmd_success(self, mock_workflow_manager, mock_console):
        """Test successful code generation."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Code generated successfully"
        }

        # Execute
        code_cmd()

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "code", {}
        )
        mock_console.print.assert_called_once_with(
            "[green]Code generated successfully.[/green]"
        )

    def test_run_cmd_success_with_target(self, mock_workflow_manager, mock_console):
        """Test successful run with target."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Target executed successfully"
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
            "message": "Execution complete"
        }

        # Execute
        run_cmd()

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "run", {"target": None}
        )
        mock_console.print.assert_called_once_with(
            "[green]Execution complete.[/green]"
        )

    def test_config_cmd_set_value(self, mock_workflow_manager, mock_console):
        """Test setting a configuration value."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "message": "Configuration updated"
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
            "value": "gpt-4"
        }

        # Execute
        config_cmd("model")

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "config", {"key": "model", "value": None}
        )
        mock_console.print.assert_called_once_with(
            "[blue]model:[/blue] gpt-4"
        )

    def test_config_cmd_list_all(self, mock_workflow_manager, mock_console):
        """Test listing all configuration values."""
        # Setup
        mock_workflow_manager.execute_command.return_value = {
            "success": True,
            "config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }

        # Execute
        config_cmd()

        # Verify
        mock_workflow_manager.execute_command.assert_called_once_with(
            "config", {"key": None, "value": None}
        )
        assert mock_console.print.call_count == 4  # Header + 3 config items
