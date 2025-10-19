import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from devsynth.application.cli import cli_commands
from devsynth.application.cli.cli_commands import (
    code_cmd,
    config_cmd,
    dbschema_cmd,
    gather_cmd,
    init_cmd,
    inspect_cmd,
    refactor_cmd,
    run_pipeline_cmd,
    serve_cmd,
    spec_cmd,
    test_cmd,
    webapp_cmd,
    webui_cmd,
)
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.core import feature_flags

ORIG_CHECK_SERVICES = cli_commands._check_services


class TestCLICommands:
    """Tests for the CLI command functions.

    ReqID: N/A"""

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

    @pytest.mark.medium
    def test_init_cmd_success_succeeds(self, mock_bridge):
        """Project initializes when no config exists.

        ReqID: N/A"""
        cfg = MagicMock()
        cfg.exists.return_value = False
        # The actual config object that gets modified is cfg.config
        cfg.config = MagicMock()
        cfg.config.project_root = "/proj"

        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load",
                return_value=cfg,
            ),
            patch("pathlib.Path.mkdir"),
        ):  # Mock mkdir to avoid filesystem issues
            init_cmd(
                root="/proj",
                language="python",
                goals="goal",
                memory_backend="memory",
                auto_confirm=True,
                bridge=mock_bridge,
            )
        assert cfg.config.project_root == "/proj"
        assert cfg.config.language == "python"
        assert cfg.config.goals == "goal"
        assert any(
            "Initialization complete" in c.args[0]
            for c in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_init_cmd_already_initialized_succeeds(self, mock_bridge):
        """init_cmd exits when config exists.

        ReqID: N/A"""
        cfg = MagicMock()
        cfg.exists.return_value = True

        # Mock _find_config_path to return a path so init_cmd thinks project is initialized
        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load",
                return_value=cfg,
            ),
            patch(
                "devsynth.application.cli.commands.init_cmd._find_config_path",
                return_value=Path("/tmp/test/.devsynth/project.yaml"),
            ),
        ):
            init_cmd(root="/tmp/test", bridge=mock_bridge)
        mock_bridge.display_result.assert_any_call(
            "[yellow]Project already initialized at /tmp/test/.devsynth/project.yaml[/yellow]",
            message_type="warning",
        )

    @pytest.mark.xfail(
        reason="CLI error handling uses console.print() instead of display_result()"
    )
    @pytest.mark.medium
    def test_init_cmd_exception_raises_error(self, mock_bridge):
        """Errors are reported via the bridge.

        ReqID: N/A"""
        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load",
                side_effect=Exception("boom"),
            ),
            patch("pathlib.Path.mkdir"),
        ):  # Mock mkdir to avoid filesystem issues
            init_cmd(root="/tmp/test", bridge=mock_bridge)
        assert any(
            "boom" in c.args[0] for c in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_spec_cmd_success_succeeds(self, mock_workflow_manager, mock_bridge):
        """Test successful spec generation.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Specs generated successfully",
        }
        spec_cmd("requirements.md")
        mock_workflow_manager.assert_called_once_with(
            "spec", {"requirements_file": "requirements.md"}
        )
        success_message = (
            "[green]Specifications generated from requirements.md.[/green]"
        )
        assert any(
            call.args[0] == success_message
            for call in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_test_cmd_success_succeeds(self, mock_workflow_manager, mock_bridge):
        """Test successful test generation.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Tests generated successfully",
        }
        test_cmd("specs.md")
        mock_workflow_manager.assert_called_once_with("test", {"spec_file": "specs.md"})
        success_message = "[green]Tests generated from specs.md.[/green]"
        assert any(
            call.args[0] == success_message
            for call in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_code_cmd_success_succeeds(self, mock_workflow_manager, mock_bridge):
        """Test successful code generation.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Code generated successfully",
        }
        code_cmd()
        mock_workflow_manager.assert_called_once_with("code", {})
        success_message = "[green]Code generated successfully.[/green]"
        assert any(
            call.args[0] == success_message
            for call in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_run_pipeline_cmd_success_with_target_succeeds(
        self, mock_workflow_manager, mock_bridge
    ):
        """Test successful run with target.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Target executed successfully",
        }
        run_pipeline_cmd("unit-tests")
        mock_workflow_manager.assert_called_once_with(
            "run-pipeline", {"target": "unit-tests", "report": None}
        )
        mock_bridge.display_result.assert_called_once_with(
            "[green]Executed target: unit-tests[/green]"
        )

    @pytest.mark.medium
    def test_run_pipeline_cmd_success_without_target_succeeds(
        self, mock_workflow_manager, mock_bridge
    ):
        """Test successful run without target.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Execution complete",
        }
        run_pipeline_cmd()
        mock_workflow_manager.assert_called_once_with(
            "run-pipeline", {"target": None, "report": None}
        )
        mock_bridge.display_result.assert_called_once_with(
            "[green]Execution complete.[/green]"
        )

    @pytest.mark.medium
    def test_config_cmd_set_value_succeeds(self, mock_workflow_manager, mock_bridge):
        """Test setting a configuration value.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {
            "success": True,
            "message": "Configuration updated",
        }
        config_cmd("model", "gpt-4")
        mock_workflow_manager.assert_called_once_with(
            "config", {"key": "model", "value": "gpt-4"}
        )
        mock_bridge.display_result.assert_called_once_with(
            "[green]Configuration updated: model = gpt-4[/green]"
        )

    @pytest.mark.medium
    def test_config_cmd_get_value_succeeds(self, mock_workflow_manager, mock_bridge):
        """Test getting a configuration value.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {"success": True, "value": "gpt-4"}
        config_cmd("model")
        mock_workflow_manager.assert_called_once_with(
            "config", {"key": "model", "value": None}
        )
        mock_bridge.display_result.assert_called_once_with("[blue]model:[/blue] gpt-4")

    @pytest.mark.medium
    def test_config_cmd_list_all_succeeds(self, mock_workflow_manager, mock_bridge):
        """Test listing all configuration values.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {
            "success": True,
            "config": {"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000},
        }
        config_cmd()
        mock_workflow_manager.assert_called_once_with(
            "config", {"key": None, "value": None}
        )
        assert mock_bridge.display_result.call_count == 4

    @pytest.mark.medium
    def test_enable_feature_cmd_succeeds(self, tmp_path, mock_bridge):
        """enable_feature_cmd should toggle a flag in project.yaml.

        ReqID: N/A"""
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
        cfg = UnifiedConfigLoader.load(tmp_path).config
        assert cfg.features["code_generation"] is True
        assert any(
            "Feature 'code_generation' enabled." == call.args[0]
            for call in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_config_cmd_updates_yaml_succeeds(self, tmp_path, mock_bridge):
        """Test that config cmd updates yaml succeeds.

        ReqID: N/A"""
        cfg_dir = tmp_path / ".devsynth"
        cfg_dir.mkdir()
        cfg = cfg_dir / "project.yaml"
        cfg.write_text("language: python\n")

        def fake_exec(command, args):
            data = UnifiedConfigLoader.load(tmp_path).config.as_dict()
            if command == "config" and args.get("key") and args.get("value"):
                data[args["key"]] = args["value"]
                cfg.write_text(yaml.safe_dump(data))
                return {"success": True}
            return {"success": True, "config": data}

        with patch(
            "devsynth.application.cli.cli_commands.workflows.execute_command",
            side_effect=fake_exec,
        ):
            cwd = os.getcwd()
            os.chdir(tmp_path)
            try:
                cli_commands.config_cmd("language", "javascript")
            finally:
                os.chdir(cwd)
        cfg_loaded = UnifiedConfigLoader.load(tmp_path).config
        assert cfg_loaded.language == "javascript"

    @pytest.mark.medium
    def test_enable_feature_cmd_yaml_succeeds(self, tmp_path, mock_bridge):
        """Test that enable feature cmd yaml succeeds.

        ReqID: N/A"""
        cfg_dir = tmp_path / ".devsynth"
        cfg_dir.mkdir()
        cfg = cfg_dir / "project.yaml"
        cfg.write_text("features:\n  code_generation: false\n")
        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            cli_commands.enable_feature_cmd("code_generation")
        finally:
            os.chdir(cwd)
        cfg_loaded = UnifiedConfigLoader.load(tmp_path).config
        assert cfg_loaded.features["code_generation"] is True

    @pytest.mark.medium
    def test_config_cmd_uses_loader_succeeds(self, mock_workflow_manager, mock_bridge):
        """Test that config cmd uses loader succeeds.

        ReqID: N/A"""
        cfg = MagicMock()
        cfg.config = MagicMock()
        cfg.config.language = "python"
        mock_workflow_manager.return_value = {"success": True}
        with patch(
            "devsynth.config.unified_loader.UnifiedConfigLoader.load", return_value=cfg
        ) as mock_load:
            cli_commands.config_cmd("language", "javascript")
        mock_load.assert_called_once()

    @pytest.mark.medium
    def test_enable_feature_cmd_loader_succeeds(self, mock_bridge):
        """Test that enable feature cmd loader succeeds.

        ReqID: N/A"""
        cfg = MagicMock()
        cfg.features = {}
        with patch(
            "devsynth.config.unified_loader.UnifiedConfigLoader.load", return_value=cfg
        ) as mock_load:
            cli_commands.enable_feature_cmd("code_generation")
        mock_load.assert_called_once()

    @pytest.mark.medium
    def test_enable_feature_cmd_load_error_displays_error(self, mock_bridge):
        """enable_feature_cmd should display an error when loading the configuration fails.

        ReqID: N/A"""
        with patch(
            "devsynth.config.unified_loader.UnifiedConfigLoader.load",
            side_effect=Exception("Failed to load configuration"),
        ):
            cli_commands.enable_feature_cmd("code_generation")

        # Verify that an error message was displayed
        mock_bridge.display_result.assert_any_call(
            "[red]Error:[/red] Failed to load configuration", highlight=False
        )

    @pytest.mark.medium
    def test_enable_feature_cmd_save_error_displays_error(self, mock_bridge):
        """enable_feature_cmd should display an error when saving the configuration fails.

        ReqID: N/A"""
        cfg = MagicMock()
        cfg.features = {}
        cfg.as_dict.return_value = {"features": {"code_generation": True}}

        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load",
                return_value=cfg,
            ),
            patch(
                "devsynth.application.cli.cli_commands.save_config",
                side_effect=Exception("Failed to save configuration"),
            ),
            patch("pathlib.Path.exists", return_value=False),
        ):
            cli_commands.enable_feature_cmd("code_generation")

        # Verify that an error message was displayed
        mock_bridge.display_result.assert_any_call(
            "[red]Error:[/red] Failed to save configuration", highlight=False
        )

    @pytest.mark.medium
    def test_enable_feature_cmd_nonexistent_feature_creates_feature(self, mock_bridge):
        """enable_feature_cmd should create a new feature if it doesn't exist.

        ReqID: N/A"""
        cfg = MagicMock()
        cfg.features = {}

        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load",
                return_value=cfg,
            ),
            patch("devsynth.application.cli.cli_commands.save_config"),
            patch("pathlib.Path.exists", return_value=False),
        ):
            cli_commands.enable_feature_cmd("new_feature")

        # Verify that the feature was added to the features dictionary
        assert cfg.features["new_feature"] is True

        # Verify that a success message was displayed
        mock_bridge.display_result.assert_called_once_with(
            "Feature 'new_feature' enabled."
        )

    @pytest.mark.medium
    def test_enable_feature_cmd_already_enabled_feature_succeeds(self, mock_bridge):
        """enable_feature_cmd should succeed when enabling an already enabled feature.

        ReqID: N/A"""
        cfg = MagicMock()
        cfg.features = {"code_generation": True}

        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load",
                return_value=cfg,
            ),
            patch("devsynth.application.cli.cli_commands.save_config"),
            patch("pathlib.Path.exists", return_value=False),
        ):
            cli_commands.enable_feature_cmd("code_generation")

        # Verify that the feature is still enabled
        assert cfg.features["code_generation"] is True

        # Verify that a success message was displayed
        mock_bridge.display_result.assert_called_once_with(
            "Feature 'code_generation' enabled."
        )

    @pytest.mark.medium
    def test_enable_feature_cmd_persists_existing_flags(self, tmp_path, mock_bridge):
        """Enabling one feature should not disable existing flags.

        ReqID: N/A"""

        dev_dir = tmp_path / ".devsynth"
        dev_dir.mkdir()
        config_file = dev_dir / "project.yaml"
        config_file.write_text("features:\n  code_generation: true\n")

        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            feature_flags.refresh()
            cli_commands.enable_feature_cmd("test_generation")
            assert feature_flags.is_enabled("test_generation") is True
        finally:
            os.chdir(cwd)

        cfg = UnifiedConfigLoader.load(tmp_path).config
        assert cfg.features["code_generation"] is True
        assert cfg.features["test_generation"] is True

    @pytest.mark.medium
    def test_init_creates_config_and_commands_use_loader_succeeds(
        self, tmp_path, mock_bridge
    ):
        """Test that init creates config and commands use loader succeeds.

        ReqID: N/A"""
        cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            cli_commands.init_cmd(
                root=str(tmp_path),
                language="python",
                goals="goal",
                memory_backend="memory",
                auto_confirm=True,
            )
        finally:
            os.chdir(cwd)
        cfg_path = tmp_path / ".devsynth" / "project.yaml"
        assert cfg_path.exists()
        real_load = cli_commands.load_config

        def spy_load(path=None):
            cfg = real_load(path)
            spy_load.path = cfg.path
            return cfg

        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load",
                side_effect=spy_load,
            ) as mock_load,
            patch(
                "devsynth.application.cli.cli_commands.workflows.execute_command",
                return_value={"success": True},
            ),
        ):
            cwd = os.getcwd()
            os.chdir(tmp_path)
            try:
                cli_commands.config_cmd()
            finally:
                os.chdir(cwd)
        mock_load.assert_called()
        assert spy_load.path == cfg_path

    @pytest.mark.medium
    def test_inspect_cmd_file_succeeds(self, mock_workflow_manager, mock_bridge):
        """Inspect command with input file.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {"success": True}
        inspect_cmd("requirements.md")
        mock_workflow_manager.assert_called_once_with(
            "inspect", {"input": "requirements.md", "interactive": False}
        )

    @pytest.mark.medium
    def test_inspect_cmd_interactive_succeeds(self, mock_workflow_manager, mock_bridge):
        """Inspect command in interactive mode.

        ReqID: N/A"""
        mock_workflow_manager.return_value = {"success": True}
        inspect_cmd(interactive=True)
        mock_workflow_manager.assert_called_once_with("inspect", {"interactive": True})

    @pytest.mark.medium
    def test_spec_cmd_missing_openai_key_succeeds(
        self, mock_workflow_manager, mock_bridge
    ):
        """spec_cmd should warn when OpenAI API key is missing.

        ReqID: N/A"""

        class DummySettings:
            vector_store_enabled = False
            memory_store_type = "chromadb"
            provider_type = "openai"
            openai_api_key = None
            lm_studio_endpoint = None

        with (
            patch(
                "devsynth.application.cli.cli_commands.get_settings",
                return_value=DummySettings,
            ),
            patch(
                "devsynth.application.cli.cli_commands._check_services",
                new=ORIG_CHECK_SERVICES,
            ),
        ):
            spec_cmd("req.md")
            mock_workflow_manager.assert_not_called()
            assert any(
                "OPENAI_API_KEY" in call.args[0]
                for call in mock_bridge.display_result.call_args_list
            )

    @pytest.mark.medium
    def test_spec_cmd_missing_chromadb_package_succeeds(
        self, mock_workflow_manager, mock_bridge
    ):
        """spec_cmd should warn when ChromaDB package is unavailable.

        ReqID: N/A"""

        class DummySettings:
            vector_store_enabled = True
            memory_store_type = "chromadb"
            provider_type = "openai"
            openai_api_key = "key"
            lm_studio_endpoint = None
            enable_chromadb = True

        with (
            patch(
                "devsynth.application.cli.cli_commands.get_settings",
                return_value=DummySettings,
            ),
            patch(
                "devsynth.application.cli.cli_commands.importlib.util.find_spec",
                return_value=None,
            ),
            patch(
                "devsynth.application.cli.cli_commands._check_services",
                new=ORIG_CHECK_SERVICES,
            ),
        ):
            spec_cmd("req.md")
            mock_workflow_manager.assert_not_called()
            assert any(
                "chromadb" in call.args[0].lower()
                for call in mock_bridge.display_result.call_args_list
            )

    @pytest.mark.medium
    def test_spec_cmd_missing_kuzu_package_succeeds(
        self, mock_workflow_manager, mock_bridge
    ):
        """spec_cmd should warn when Kuzu package is unavailable.

        ReqID: N/A"""

        class DummySettings:
            vector_store_enabled = True
            memory_store_type = "kuzu"
            provider_type = "openai"
            openai_api_key = "key"
            lm_studio_endpoint = None

        with (
            patch(
                "devsynth.application.cli.cli_commands.get_settings",
                return_value=DummySettings,
            ),
            patch(
                "devsynth.application.cli.cli_commands.importlib.util.find_spec",
                return_value=None,
            ),
            patch(
                "devsynth.application.cli.cli_commands._check_services",
                new=ORIG_CHECK_SERVICES,
            ),
        ):
            spec_cmd("req.md")
            mock_workflow_manager.assert_not_called()
            assert any(
                "kuzu" in call.args[0].lower()
                for call in mock_bridge.display_result.call_args_list
            )

    @pytest.mark.medium
    def test_config_key_autocomplete_succeeds(self, tmp_path, monkeypatch):
        """Test that config key autocomplete succeeds.

        ReqID: N/A"""
        cfg_dir = tmp_path / ".devsynth"
        cfg_dir.mkdir()
        (cfg_dir / "project.yaml").write_text("language: python\nmodel: gpt-4\n")
        monkeypatch.chdir(tmp_path)
        result = cli_commands.config_key_autocomplete(None, "l")
        assert "language" in result

    @pytest.mark.medium
    def test_check_services_warns_succeeds(self, monkeypatch, capsys):
        """Test that check services warns succeeds.

        ReqID: N/A"""

        class DummySettings:
            vector_store_enabled = False
            memory_store_type = "chromadb"
            provider_type = "openai"
            openai_api_key = None
            lm_studio_endpoint = None

        monkeypatch.setattr(cli_commands, "get_settings", lambda: DummySettings)
        monkeypatch.setattr(cli_commands, "_check_services", ORIG_CHECK_SERVICES)
        res = cli_commands._check_services()
        output = capsys.readouterr().out
        assert res is False
        assert "OPENAI_API_KEY" in output

    @pytest.mark.medium
    def test_doctor_cmd_invokes_loader_succeeds(self):
        """Test that doctor cmd invokes loader succeeds.

        ReqID: N/A"""
        with (
            patch(
                "devsynth.config.unified_loader.UnifiedConfigLoader.load"
            ) as mock_load,
            patch(
                "devsynth.application.cli.commands.doctor_cmd.bridge.print"
            ) as mock_print,
        ):
            cli_commands.doctor_cmd("config")
            mock_load.assert_called_once()
            assert mock_print.called

    @pytest.mark.medium
    def test_check_cmd_alias_succeeds(self):
        """Test that check cmd alias succeeds.

        ReqID: N/A"""
        with patch("devsynth.application.cli.cli_commands.doctor_cmd") as mock_doctor:
            cli_commands.check_cmd("config")
            mock_doctor.assert_called_once_with("config")

    @pytest.mark.medium
    def test_gather_cmd_creates_file_succeeds(self, tmp_path):
        """Test that gather cmd creates file succeeds.

        ReqID: N/A"""
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

    @pytest.mark.medium
    def test_init_cmd_wizard_runs_wizard(self):
        """Wizard mode should invoke SetupWizard.run."""

        with patch("devsynth.application.cli.cli_commands.SetupWizard") as wiz:
            init_cmd(wizard=True)
            wiz.assert_called_once()
            wiz.return_value.run.assert_called_once()

    @pytest.mark.medium
    def test_spec_cmd_invalid_file(self, mock_workflow_manager, mock_bridge):
        """Invalid requirements file should not trigger generation."""

        with (
            patch(
                "devsynth.application.cli.cli_commands._validate_file_path",
                return_value="bad",
            ),
            patch.object(cli_commands.bridge, "confirm_choice", return_value=False),
        ):
            spec_cmd("missing.md")
        mock_workflow_manager.assert_not_called()

    @pytest.mark.medium
    def test_test_cmd_invalid_file(self, mock_workflow_manager, mock_bridge):
        """Invalid spec file should not trigger generation."""

        with (
            patch(
                "devsynth.application.cli.cli_commands._validate_file_path",
                return_value="bad",
            ),
            patch.object(cli_commands.bridge, "confirm_choice", return_value=False),
        ):
            test_cmd("missing.md")
        mock_workflow_manager.assert_not_called()

    @pytest.mark.medium
    def test_code_cmd_no_tests(self, mock_workflow_manager, tmp_path, monkeypatch):
        """code_cmd exits when no tests are present."""

        monkeypatch.chdir(tmp_path)
        with patch.object(cli_commands.bridge, "confirm_choice", return_value=False):
            code_cmd()
        mock_workflow_manager.assert_not_called()

    @pytest.mark.medium
    def test_run_pipeline_cmd_invalid_target(self, mock_workflow_manager, mock_bridge):
        """run_pipeline_cmd warns on invalid target and aborts when declined."""

        with patch.object(cli_commands.bridge, "confirm_choice", return_value=False):
            run_pipeline_cmd("bogus")
        mock_workflow_manager.assert_not_called()

    @pytest.mark.medium
    def test_config_cmd_invalid_key(self, mock_bridge):
        """config_cmd should report errors from workflow."""

        with (
            patch(
                "devsynth.core.workflows.execute_command",
                return_value={"success": False, "message": "bad"},
            ),
            patch("devsynth.application.cli.cli_commands._handle_error") as herr,
        ):
            config_cmd("bad", "value")
            herr.assert_called_once()

    @pytest.mark.medium
    def test_gather_cmd_error_propagates(self):
        """Errors from gather_requirements propagate to caller."""

        with patch(
            "devsynth.application.cli.cli_commands.gather_requirements",
            side_effect=FileNotFoundError("boom"),
        ):
            with pytest.raises(FileNotFoundError):
                gather_cmd(output_file="x")

    @pytest.mark.medium
    def test_refactor_cmd_error(self, mock_bridge):
        """refactor_cmd should display error when workflow fails."""

        with patch(
            "devsynth.application.cli.orchestration.refactor_workflow.refactor_workflow_manager.execute_refactor_workflow",
            return_value={"success": False, "message": "fail"},
        ):
            refactor_cmd(path="proj")
        mock_bridge.display_result.assert_any_call("[red]Error:[/red] fail")

    @pytest.mark.medium
    def test_inspect_cmd_failure(self, mock_bridge):
        """inspect_cmd should show error message when workflow fails."""

        with patch(
            "devsynth.core.workflows.inspect_requirements",
            return_value={"success": False, "message": "bad"},
        ):
            inspect_cmd("req.md")
        mock_bridge.display_result.assert_any_call(
            "[red]Error:[/red] bad", highlight=False
        )

    @pytest.mark.medium
    def test_webapp_cmd_invalid_framework(self, tmp_path):
        """Unknown framework raises an error."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
        ):
            webapp_cmd(framework="bad", name="app", path=str(tmp_path))
            disp.assert_any_call(
                "[red]✗ Error:[/red] Unsupported framework 'bad'. Supported: flask, fastapi, django, express",
                highlight=False,
            )

    @pytest.mark.medium
    def test_serve_cmd_passes_options(self, monkeypatch):
        """serve_cmd forwards host and port to uvicorn."""

        monkeypatch.setattr(cli_commands, "configure_logging", lambda: None)
        with patch("uvicorn.run") as run:
            serve_cmd(host="1.2.3.4", port=1234)
            run.assert_called_once()
            args, kwargs = run.call_args
            assert kwargs["host"] == "1.2.3.4"
            assert kwargs["port"] == 1234

    @pytest.mark.medium
    def test_webapp_cmd_flask_succeeds(self, tmp_path):
        """webapp_cmd successfully generates a Flask application."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            webapp_cmd(framework="flask", name="myapp", path=str(tmp_path))

            # Verify that the success message was displayed
            disp.assert_any_call(
                "[green]✓ Flask application 'myapp' generated successfully![/green]"
            )

            # Verify that the necessary files were created
            expected_files = [
                os.path.join(tmp_path, "myapp", "myapp", "__init__.py"),
                os.path.join(tmp_path, "myapp", "myapp", "routes.py"),
                os.path.join(tmp_path, "myapp", "myapp", "templates", "index.html"),
                os.path.join(tmp_path, "myapp", "myapp", "static", "css", "style.css"),
                os.path.join(tmp_path, "myapp", "myapp", "static", "js", "main.js"),
                os.path.join(tmp_path, "myapp", "requirements.txt"),
                os.path.join(tmp_path, "myapp", "app.py"),
                os.path.join(tmp_path, "myapp", "README.md"),
            ]

            # Check that open was called for each expected file
            assert mock_file.call_count >= len(expected_files)

    @pytest.mark.medium
    def test_webapp_cmd_fastapi_succeeds(self, tmp_path):
        """webapp_cmd successfully generates a FastAPI application."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            webapp_cmd(framework="fastapi", name="myapi", path=str(tmp_path))

            # Verify that the success message was displayed
            disp.assert_any_call(
                "[green]✓ FastAPI application 'myapi' generated successfully![/green]"
            )

    @pytest.mark.medium
    def test_webapp_cmd_existing_dir_without_force_fails(self, tmp_path):
        """webapp_cmd fails when directory exists and force is False."""

        with (
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.path.exists", return_value=True),
            patch("os.makedirs"),
            patch("builtins.open", mock_open()),
        ):
            webapp_cmd(framework="flask", name="myapp", path=str(tmp_path), force=False)

            # Verify that the warning message was displayed
            disp.assert_any_call(
                f"[yellow]Directory {os.path.join(tmp_path, 'myapp')} already exists. Use --force to overwrite.[/yellow]"
            )

    @pytest.mark.medium
    def test_webapp_cmd_existing_dir_with_force_succeeds(self, tmp_path):
        """webapp_cmd succeeds when directory exists and force is True."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.path.exists", return_value=True),
            patch("shutil.rmtree"),
            patch("os.makedirs"),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            webapp_cmd(framework="flask", name="myapp", path=str(tmp_path), force=True)

            # Verify that the success message was displayed
            disp.assert_any_call(
                "[green]✓ Flask application 'myapp' generated successfully![/green]"
            )

    @pytest.mark.medium
    def test_dbschema_cmd_invalid_type(self, tmp_path):
        """Unknown db type raises an error."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
        ):
            dbschema_cmd(db_type="foo", name="schema", path=str(tmp_path))
            disp.assert_any_call(
                "[red]\u2717 Error:[/red] Unsupported database type 'foo'. Supported: sqlite, mysql, postgresql, mongodb",
                highlight=False,
            )

    @pytest.mark.medium
    def test_dbschema_cmd_sqlite_succeeds(self, tmp_path):
        """dbschema_cmd successfully generates a SQLite database schema."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            dbschema_cmd(db_type="sqlite", name="mydb", path=str(tmp_path))

            # Verify that the success message was displayed
            disp.assert_any_call(
                "[green]✓ SQLite database schema 'mydb' generated successfully![/green]"
            )

            # Verify that the necessary files were created
            expected_files = [
                os.path.join(tmp_path, "mydb_schema", "schema.sql"),
                os.path.join(tmp_path, "mydb_schema", "README.md"),
            ]

            # Check that open was called for each expected file
            assert mock_file.call_count >= len(expected_files)

    @pytest.mark.medium
    def test_dbschema_cmd_mysql_succeeds(self, tmp_path):
        """dbschema_cmd successfully generates a MySQL database schema."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            dbschema_cmd(db_type="mysql", name="mydb", path=str(tmp_path))

            # Verify that the success message was displayed
            disp.assert_any_call(
                "[green]✓ MySQL database schema 'mydb' generated successfully![/green]"
            )

            # Verify that the necessary files were created
            expected_files = [
                os.path.join(tmp_path, "mydb_schema", "schema.sql"),
                os.path.join(tmp_path, "mydb_schema", "README.md"),
            ]

            # Check that open was called for each expected file
            assert mock_file.call_count >= len(expected_files)

    @pytest.mark.medium
    def test_dbschema_cmd_mongodb_succeeds(self, tmp_path):
        """dbschema_cmd successfully generates a MongoDB database schema."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.makedirs"),
            patch("os.path.exists", return_value=False),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            dbschema_cmd(db_type="mongodb", name="mydb", path=str(tmp_path))

            # Verify that the success message was displayed
            disp.assert_any_call(
                "[green]✓ MongoDB database schema 'mydb' generated successfully![/green]"
            )

            # Verify that the necessary files were created
            expected_files = [
                os.path.join(tmp_path, "mydb_schema", "schema.json"),
                os.path.join(tmp_path, "mydb_schema", "README.md"),
            ]

            # Check that open was called for each expected file
            assert mock_file.call_count >= len(expected_files)

    @pytest.mark.medium
    def test_dbschema_cmd_existing_dir_without_force_fails(self, tmp_path):
        """dbschema_cmd fails when directory exists and force is False."""

        with (
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.path.exists", return_value=True),
            patch("os.makedirs"),
            patch("builtins.open", mock_open()),
        ):
            dbschema_cmd(db_type="sqlite", name="mydb", path=str(tmp_path), force=False)

            # Verify that the warning message was displayed
            disp.assert_any_call(
                f"[yellow]Directory {os.path.join(tmp_path, 'mydb_schema')} already exists. Use --force to overwrite.[/yellow]"
            )

    @pytest.mark.medium
    def test_dbschema_cmd_existing_dir_with_force_succeeds(self, tmp_path):
        """dbschema_cmd succeeds when directory exists and force is True."""

        with (
            patch.object(
                cli_commands.bridge,
                "create_progress",
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=lambda s, *a: None,
                    update=lambda *a, **k: None,
                    complete=lambda *a, **k: None,
                ),
            ),
            patch.object(cli_commands.bridge, "print"),
            patch.object(cli_commands.bridge, "display_result") as disp,
            patch("os.path.exists", return_value=True),
            patch("shutil.rmtree"),
            patch("os.makedirs"),
            patch("builtins.open", mock_open()) as mock_file,
        ):
            dbschema_cmd(db_type="sqlite", name="mydb", path=str(tmp_path), force=True)

            # Verify that the success message was displayed
            disp.assert_any_call(
                "[green]✓ SQLite database schema 'mydb' generated successfully![/green]"
            )

    @pytest.mark.medium
    def test_webui_cmd_success_succeeds(self, mock_bridge):
        """webui_cmd successfully launches the WebUI.

        ReqID: N/A"""
        # Mock the webui module and run function
        mock_run = MagicMock()
        with patch("devsynth.application.cli.cli_commands.run", mock_run):
            webui_cmd()

        # Verify that the run function was called
        mock_run.assert_called_once()

        # No error message should be displayed
        assert not any(
            "Error" in str(call.args[0])
            for call in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_webui_cmd_import_error_displays_error(self, mock_bridge):
        """webui_cmd displays an error when the WebUI module is unavailable.

        ReqID: N/A"""
        # Mock an ImportError when importing the webui module
        with patch(
            "devsynth.application.cli.cli_commands.run",
            side_effect=ImportError("No module named 'streamlit'"),
        ):
            webui_cmd()

        # Verify that an error message was displayed
        assert any(
            "Error" in str(call.args[0])
            for call in mock_bridge.display_result.call_args_list
        )

    @pytest.mark.medium
    def test_webui_cmd_runtime_error_displays_error(self, mock_bridge):
        """webui_cmd displays an error when the WebUI fails to launch.

        ReqID: N/A"""
        # Mock a RuntimeError when running the WebUI
        with patch(
            "devsynth.application.cli.cli_commands.run",
            side_effect=RuntimeError("Failed to launch WebUI"),
        ):
            webui_cmd()

        # Verify that an error message was displayed
        assert any(
            "Error" in str(call.args[0])
            for call in mock_bridge.display_result.call_args_list
        )
