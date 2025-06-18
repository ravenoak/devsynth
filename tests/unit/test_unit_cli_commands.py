from unittest.mock import patch, mock_open
import os
import yaml

import pytest

from devsynth.application.cli import cli_commands
from devsynth.application.cli.cli_commands import (
    code_cmd,
    config_cmd,
    init_cmd,
    run_pipeline_cmd,
    spec_cmd,
    test_cmd,
    inspect_cmd,
    refactor_cmd,
)

ORIG_CHECK_SERVICES = cli_commands._check_services


class TestCLICommands:
    """Tests for the CLI command functions."""

    @pytest.fixture(autouse=True)
    def service_check(self):
        with patch(
            "devsynth.application.cli.cli_commands._check_services", return_value=True
        ):
            yield

    @pytest.fixture
    def mock_workflow_manager(self):
        """Create a mock workflow executor."""
        with patch("devsynth.core.workflows.execute_command") as mock:
            yield mock

    @pytest.fixture
    def mock_bridge(self):
        """Create a mock UX bridge."""
        with patch("devsynth.application.cli.cli_commands.bridge") as mock:
            yield mock

    def test_init_cmd_success(self, mock_workflow_manager, mock_bridge):
        """Test successful project initialization."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Project initialized successfully",
        }

        # Execute
        with patch(
            "devsynth.application.cli.cli_commands.bridge.ask_question",
            side_effect=[
                "./test-project",  # project_root
                "single_package",  # structure
                "python",  # language
                "",  # goals
                "",  # constraints path
            ],
        ), patch(
            "devsynth.application.cli.cli_commands.bridge.confirm_choice",
            return_value=False,
        ):
            init_cmd("./test-project")

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "init",
            {
                "path": "./test-project",
                "project_root": "./test-project",
                "language": "python",
                "constraints": "",
                "goals": "",
                "structure": "single_package",
            },
        )
        # Check that one of the print calls contains the expected message
        success_message = (
            "[green]Initialized DevSynth project in ./test-project[/green]"
        )
        assert any(
            call.args[0] == success_message
            for call in mock_bridge.display_result.call_args_list
        )

    def test_init_cmd_failure(self, mock_workflow_manager, mock_bridge):
        """Test failed project initialization."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": False,
            "message": "Path already exists",
        }

        # Execute
        with patch(
            "devsynth.application.cli.cli_commands.bridge.ask_question",
            side_effect=[
                "./test-project",
                "single_package",
                "python",
                "",
                "",
            ],
        ), patch(
            "devsynth.application.cli.cli_commands.bridge.confirm_choice",
            return_value=False,
        ):
            init_cmd("./test-project")

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "init",
            {
                "path": "./test-project",
                "project_root": "./test-project",
                "language": "python",
                "constraints": "",
                "goals": "",
                "structure": "single_package",
            },
        )
        mock_bridge.display_result.assert_called_once_with(
            "[red]Error:[/red] Path already exists", highlight=False
        )

    def test_init_cmd_exception(self, mock_workflow_manager, mock_bridge):
        """Test exception handling in project initialization."""
        # Setup
        mock_workflow_manager.side_effect = Exception("Test error")

        # Execute
        with patch(
            "devsynth.application.cli.cli_commands.bridge.ask_question",
            side_effect=[
                "./test-project",
                "single_package",
                "python",
                "",
                "",
            ],
        ), patch(
            "devsynth.application.cli.cli_commands.bridge.confirm_choice",
            return_value=False,
        ):
            init_cmd("./test-project")

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "init",
            {
                "path": "./test-project",
                "project_root": "./test-project",
                "language": "python",
                "constraints": "",
                "goals": "",
                "structure": "single_package",
            },
        )
        mock_bridge.display_result.assert_called_once_with(
            "[red]Error:[/red] Test error", highlight=False
        )

    def test_spec_cmd_success(self, mock_workflow_manager, mock_bridge):
        """Test successful spec generation."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Specs generated successfully",
        }

        # Execute
        spec_cmd("requirements.md")

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "spec", {"requirements_file": "requirements.md"}
        )
        # Check that one of the print calls contains the expected message
        success_message = (
            "[green]Specifications generated from requirements.md.[/green]"
        )
        assert any(
            call.args[0] == success_message
            for call in mock_bridge.display_result.call_args_list
        )

    def test_test_cmd_success(self, mock_workflow_manager, mock_bridge):
        """Test successful test generation."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Tests generated successfully",
        }

        # Execute
        test_cmd("specs.md")

        # Verify
        mock_workflow_manager.assert_called_once_with("test", {"spec_file": "specs.md"})
        # Check that one of the print calls contains the expected message
        success_message = "[green]Tests generated from specs.md.[/green]"
        assert any(
            call.args[0] == success_message
            for call in mock_bridge.display_result.call_args_list
        )

    def test_code_cmd_success(self, mock_workflow_manager, mock_bridge):
        """Test successful code generation."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Code generated successfully",
        }

        # Execute
        code_cmd()

        # Verify
        mock_workflow_manager.assert_called_once_with("code", {})
        # Check that one of the print calls contains the expected message
        success_message = "[green]Code generated successfully.[/green]"
        assert any(
            call.args[0] == success_message
            for call in mock_bridge.display_result.call_args_list
        )

    def test_run_pipeline_cmd_success_with_target(
        self, mock_workflow_manager, mock_bridge
    ):
        """Test successful run with target."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Target executed successfully",
        }

        # Execute
        run_pipeline_cmd("unit-tests")

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "run-pipeline", {"target": "unit-tests"}
        )
        mock_bridge.display_result.assert_called_once_with(
            "[green]Executed target: unit-tests[/green]"
        )

    def test_run_pipeline_cmd_success_without_target(
        self, mock_workflow_manager, mock_bridge
    ):
        """Test successful run without target."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Execution complete",
        }

        # Execute
        run_pipeline_cmd()

        # Verify
        mock_workflow_manager.assert_called_once_with("run-pipeline", {"target": None})
        mock_bridge.display_result.assert_called_once_with(
            "[green]Execution complete.[/green]"
        )

    def test_config_cmd_set_value(self, mock_workflow_manager, mock_bridge):
        """Test setting a configuration value."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Configuration updated",
        }

        # Execute
        config_cmd("model", "gpt-4")

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "config", {"key": "model", "value": "gpt-4"}
        )
        mock_bridge.display_result.assert_called_once_with(
            "[green]Configuration updated: model = gpt-4[/green]"
        )

    def test_config_cmd_get_value(self, mock_workflow_manager, mock_bridge):
        """Test getting a configuration value."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "value": "gpt-4",
        }

        # Execute
        config_cmd("model")

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "config", {"key": "model", "value": None}
        )
        mock_bridge.display_result.assert_called_once_with("[blue]model:[/blue] gpt-4")

    def test_config_cmd_list_all(self, mock_workflow_manager, mock_bridge):
        """Test listing all configuration values."""
        # Setup
        mock_workflow_manager.return_value = {
            "success": True,
            "config": {"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000},
        }

        # Execute
        config_cmd()

        # Verify
        mock_workflow_manager.assert_called_once_with(
            "config", {"key": None, "value": None}
        )
        assert mock_bridge.display_result.call_count == 4  # Header + 3 config items

    def test_enable_feature_cmd(self, tmp_path, mock_bridge):
        """enable_feature_cmd should toggle a flag in project.yaml."""
        dev_dir = tmp_path / ".devsynth"
        dev_dir.mkdir()
        config_file = dev_dir / "project.yaml"
        config_file.write_text("features:\n  code_generation: false\n")

        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            cli_commands.enable_feature_cmd("code_generation")
        finally:
            os.chdir(cwd)

        data = yaml.safe_load(config_file.read_text())
        assert data["features"]["code_generation"] is True
        assert any(
            "Feature 'code_generation' enabled." == call.args[0]
            for call in mock_bridge.display_result.call_args_list
        )

    def test_init_cmd_with_name_template(self, mock_workflow_manager, mock_bridge):
        """Init command with additional parameters."""
        mock_workflow_manager.return_value = {"success": True}
        with patch(
            "devsynth.application.cli.cli_commands.bridge.ask_question",
            side_effect=[
                ".",
                "single_package",
                "python",
                "",
                "",
            ],
        ), patch(
            "devsynth.application.cli.cli_commands.bridge.confirm_choice",
            return_value=False,
        ):
            init_cmd(path=".", name="proj", template="web-app")
        mock_workflow_manager.assert_called_once_with(
            "init",
            {
                "path": ".",
                "name": "proj",
                "template": "web-app",
                "project_root": ".",
                "language": "python",
                "constraints": "",
                "goals": "",
                "structure": "single_package",
            },
        )

    @patch("devsynth.application.cli.cli_commands.Path.mkdir")
    @patch("devsynth.application.cli.cli_commands.yaml.safe_dump")
    @patch("builtins.open", new_callable=mock_open, read_data="projectName: ex")
    @patch("devsynth.application.cli.cli_commands.bridge.confirm_choice")
    def test_init_cmd_writes_features(
        self,
        mock_confirm,
        mock_open_file,
        mock_yaml_dump,
        mock_mkdir,
        mock_workflow_manager,
        mock_bridge,
    ):
        """Init command writes feature flags to project.yaml."""
        mock_workflow_manager.return_value = {"success": True}
        mock_confirm.side_effect = [True, False, False, False, False, False]

        with patch(
            "devsynth.application.cli.cli_commands.bridge.ask_question",
            side_effect=[
                "./proj",
                "single_package",
                "python",
                "",
                "",
            ],
        ):
            init_cmd(path="./proj", name="proj")

        mock_workflow_manager.assert_called_once_with(
            "init",
            {
                "path": "./proj",
                "name": "proj",
                "project_root": "./proj",
                "language": "python",
                "constraints": "",
                "goals": "",
                "structure": "single_package",
            },
        )
        assert mock_yaml_dump.called
        dumped = mock_yaml_dump.call_args[0][0]
        assert dumped["features"]["code_generation"] is True

    @patch("devsynth.application.cli.cli_commands.Path.mkdir")
    @patch("devsynth.application.cli.cli_commands.yaml.safe_dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch(
        "devsynth.application.cli.cli_commands.bridge.confirm_choice",
        return_value=False,
    )
    def test_init_cmd_writes_config_file(
        self,
        mock_confirm,
        mock_open_file,
        mock_yaml_dump,
        mock_mkdir,
        mock_workflow_manager,
        mock_bridge,
    ):
        """init_cmd should create .devsynth/devsynth.yml."""
        mock_workflow_manager.return_value = {"success": True}

        with patch(
            "devsynth.application.cli.cli_commands.bridge.ask_question",
            side_effect=[
                "./proj",
                "single_package",
                "python",
                "",
                "",
            ],
        ):
            init_cmd(path="./proj", name="proj")

        mock_mkdir.assert_called_once_with(exist_ok=True)
        mock_open_file.assert_called()
        opened_path = Path(mock_open_file.call_args[0][0])
        assert opened_path.name == "devsynth.yml"

    def test_inspect_cmd_file(self, mock_workflow_manager, mock_bridge):
        """Inspect command with input file."""
        mock_workflow_manager.return_value = {"success": True}
        inspect_cmd("requirements.md")
        mock_workflow_manager.assert_called_once_with(
            "inspect",
            {"input": "requirements.md", "interactive": False},
        )

    def test_inspect_cmd_interactive(self, mock_workflow_manager, mock_bridge):
        """Inspect command in interactive mode."""
        mock_workflow_manager.return_value = {"success": True}
        inspect_cmd(interactive=True)
        mock_workflow_manager.assert_called_once_with("inspect", {"interactive": True})

    def test_spec_cmd_missing_openai_key(self, mock_workflow_manager, mock_bridge):
        """spec_cmd should warn when OpenAI API key is missing."""

        class DummySettings:
            vector_store_enabled = False
            memory_store_type = "chromadb"
            provider_type = "openai"
            openai_api_key = None
            lm_studio_endpoint = None

        with patch(
            "devsynth.application.cli.cli_commands.get_settings",
            return_value=DummySettings,
        ), patch(
            "devsynth.application.cli.cli_commands._check_services",
            new=ORIG_CHECK_SERVICES,
        ):
            spec_cmd("req.md")
            mock_workflow_manager.assert_not_called()
            assert any(
                "OPENAI_API_KEY" in call.args[0]
                for call in mock_bridge.display_result.call_args_list
            )

    def test_spec_cmd_missing_chromadb_package(
        self, mock_workflow_manager, mock_bridge
    ):
        """spec_cmd should warn when ChromaDB package is unavailable."""

        class DummySettings:
            vector_store_enabled = True
            memory_store_type = "chromadb"
            provider_type = "openai"
            openai_api_key = "key"
            lm_studio_endpoint = None

        with patch(
            "devsynth.application.cli.cli_commands.get_settings",
            return_value=DummySettings,
        ), patch(
            "devsynth.application.cli.cli_commands.importlib.util.find_spec",
            return_value=None,
        ), patch(
            "devsynth.application.cli.cli_commands._check_services",
            new=ORIG_CHECK_SERVICES,
        ):
            spec_cmd("req.md")
            mock_workflow_manager.assert_not_called()
            assert any(
                "chromadb" in call.args[0].lower()
                for call in mock_bridge.display_result.call_args_list
            )

    def test_config_key_autocomplete(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / ".devsynth"
        cfg_dir.mkdir()
        (cfg_dir / "devsynth.yml").write_text("language: python\nmodel: gpt-4\n")
        monkeypatch.chdir(tmp_path)

        result = cli_commands.config_key_autocomplete(None, "l")
        assert "language" in result

    def test_check_services_warns(self, monkeypatch, capsys):
        class DummySettings:
            vector_store_enabled = False
            memory_store_type = "chromadb"
            provider_type = "openai"
            openai_api_key = None
            lm_studio_endpoint = None

        monkeypatch.setattr(cli_commands, "get_settings", lambda: DummySettings)
        res = cli_commands._check_services()
        output = capsys.readouterr().out
        assert res is False
        assert "OPENAI_API_KEY" in output

    def test_doctor_cmd_invokes_loader(self):
        with patch(
            "devsynth.application.cli.commands.doctor_cmd.load_config"
        ) as mock_load, patch(
            "devsynth.application.cli.commands.doctor_cmd.bridge.print"
        ) as mock_print:
            cli_commands.doctor_cmd("config")
            mock_load.assert_called_once()
            assert mock_print.called

    def test_check_cmd_alias(self):
        with patch("devsynth.application.cli.cli_commands.doctor_cmd") as mock_doctor:
            cli_commands.check_cmd("config")
            mock_doctor.assert_called_once_with("config")

    def test_gather_cmd_creates_file(self, tmp_path):
        from devsynth.application.cli.cli_commands import gather_cmd

        answers = ["goal", "constraint", "medium"]

        class Bridge(cli_commands.UXBridge):
            def __init__(self):
                self.calls = 0

            def ask_question(self, *args, **kwargs):
                ans = answers[self.calls]
                self.calls += 1
                return ans

            def confirm_choice(self, *a, **k):
                return True

            def display_result(self, *a, **k):
                pass

        bridge = Bridge()
        output = tmp_path / "requirements_plan.yaml"
        gather_cmd(output_file=str(output), bridge=bridge)
        assert output.exists()
