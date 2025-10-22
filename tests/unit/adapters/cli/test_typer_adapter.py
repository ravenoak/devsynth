from unittest.mock import MagicMock, patch

from types import SimpleNamespace

import pytest
import typer
from typer.testing import CliRunner

from devsynth.adapters.cli.typer_adapter import (
    CommandHelp,
    _format_cli_error,
    _warn_if_features_disabled,
    build_app,
    parse_args,
    run_cli,
    show_help,
)
from devsynth.application.cli import config_app
from devsynth.application.cli.commands.completion_cmd import completion_cmd
from devsynth.application.cli.requirements_commands import requirements_app


def dummy_hook(event: str) -> None:  # pragma: no cover - used for hook registration
    pass


@pytest.mark.medium
def test_build_app_returns_expected_result():
    """Test that build_app returns a Typer application with commands registered.

    ReqID: N/A"""
    app = build_app()
    assert isinstance(app, typer.Typer)
    command_names = [cmd.name for cmd in app.registered_commands]
    assert "init" in command_names
    assert "spec" in command_names
    assert "test" in command_names
    assert "code" in command_names
    assert "run-pipeline" in command_names
    assert hasattr(app, "callback")
    app_help = app.info.help
    assert "DevSynth CLI" in app_help
    with patch("typer.Typer.add_typer") as mock_add_typer:
        test_app = build_app()
        assert mock_add_typer.call_count >= 2
        mock_add_typer.assert_any_call(requirements_app, name="requirements")
        mock_add_typer.assert_any_call(
            config_app, name="config", help="Manage configuration settings"
        )


@patch("devsynth.adapters.cli.typer_adapter.load_config")
@patch("devsynth.adapters.cli.typer_adapter.typer.echo")
@pytest.mark.medium
def test_warn_if_features_disabled_all_disabled_succeeds(mock_echo, mock_load_config):
    """Test that _warn_if_features_disabled shows a warning when all features are disabled.

    ReqID: N/A"""
    mock_config = MagicMock()
    mock_config.features = {"feature1": False, "feature2": False}
    mock_load_config.return_value = mock_config
    _warn_if_features_disabled()
    mock_echo.assert_called_once()
    assert "All optional features are disabled" in mock_echo.call_args[0][0]


@patch("devsynth.adapters.cli.typer_adapter.load_config")
@patch("devsynth.adapters.cli.typer_adapter.typer.echo")
@pytest.mark.medium
def test_warn_if_features_disabled_some_enabled_succeeds(mock_echo, mock_load_config):
    """Test that _warn_if_features_disabled doesn't show a warning when some features are enabled.

    ReqID: N/A"""
    mock_config = MagicMock()
    mock_config.features = {"feature1": True, "feature2": False}
    mock_load_config.return_value = mock_config
    _warn_if_features_disabled()
    mock_echo.assert_not_called()


@patch("devsynth.adapters.cli.typer_adapter.load_config")
@patch("devsynth.adapters.cli.typer_adapter.typer.echo")
@pytest.mark.medium
def test_warn_if_features_disabled_exception_raises_error(mock_echo, mock_load_config):
    """Test that _warn_if_features_disabled handles exceptions gracefully.

    ReqID: N/A"""
    mock_load_config.side_effect = Exception("Config error")
    _warn_if_features_disabled()
    mock_echo.assert_not_called()


@patch("devsynth.adapters.cli.typer_adapter.Console")
@patch("devsynth.adapters.cli.typer_adapter.build_app")
@pytest.mark.medium
def test_show_help_succeeds(mock_build_app, mock_console):
    """Test that show_help displays the CLI help message.

    ReqID: N/A"""
    mock_app = MagicMock()
    mock_app.info = MagicMock()
    mock_app.info.help = "Test help text"
    mock_app.registered_commands = []
    mock_app.registered_groups = []
    mock_build_app.return_value = mock_app
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance
    show_help()
    assert mock_console_instance.print.call_count > 0
    mock_build_app.assert_called_once()


@patch("devsynth.adapters.cli.typer_adapter.Console")
@patch("devsynth.adapters.cli.typer_adapter.build_app")
@pytest.mark.medium
def test_show_help_table_mode(mock_build_app, mock_console):
    """Table render mode should render commands without error.

    ReqID: N/A"""

    command = SimpleNamespace(name="init", help="Init projects")
    mock_app = SimpleNamespace(
        info=SimpleNamespace(help="Test"),
        registered_commands=[command],
        registered_groups=[],
    )
    mock_build_app.return_value = mock_app
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance

    show_help(render_mode="table", group_filter=["config"])

    assert mock_console_instance.print.call_count > 0
    mock_build_app.assert_called_once()


@pytest.mark.fast
def test_show_help_invalid_mode_raises() -> None:
    """Passing an unsupported render mode should raise a ValueError.

    ReqID: N/A"""

    with pytest.raises(ValueError):
        show_help(render_mode="invalid")  # type: ignore[arg-type]


@patch("devsynth.adapters.cli.typer_adapter._warn_if_features_disabled")
@patch("devsynth.adapters.cli.typer_adapter.build_app")
@pytest.mark.medium
def test_parse_args_has_expected(mock_build_app, mock_warn):
    """Test that parse_args calls the app with the provided arguments.

    ReqID: N/A"""
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app
    parse_args(["init", "--path", "./test"])
    mock_warn.assert_called_once()
    mock_app.assert_called_once_with(["init", "--path", "./test"])


@patch("devsynth.adapters.cli.typer_adapter._warn_if_features_disabled")
@patch("devsynth.adapters.cli.typer_adapter.build_app")
@pytest.mark.medium
def test_run_cli_succeeds(mock_build_app, mock_warn):
    """Test that run_cli calls the app.

    ReqID: N/A"""
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app
    run_cli()
    mock_warn.assert_called_once()
    mock_app.assert_called_once_with()


@patch("devsynth.adapters.cli.typer_adapter.typer_completion.get_completion_script")
@pytest.mark.medium
def test_completion_cmd_displays_script(mock_get_script):
    """Test that completion_cmd shows generated script."""

    mock_get_script.return_value = "script"
    bridge = MagicMock()
    progress = MagicMock()
    bridge.create_progress.return_value = progress

    completion_cmd(shell="bash", install=False, bridge=bridge)

    bridge.create_progress.assert_called_once()
    bridge.show_completion.assert_called_once_with("script")
    progress.complete.assert_called_once()


@patch("devsynth.adapters.cli.typer_adapter.register_dashboard_hook")
@pytest.mark.medium
def test_dashboard_hook_option_registers(mock_reg):
    """Global --dashboard-hook registers provided callback."""
    runner = CliRunner()
    path = "tests.unit.adapters.cli.test_typer_adapter:dummy_hook"
    result = runner.invoke(build_app(), ["--dashboard-hook", path])
    assert result.exit_code == 0
    mock_reg.assert_called_once()


@pytest.mark.fast
def test_format_cli_error_usage_hint() -> None:
    """_format_cli_error should sanitize usage errors and append guidance."""

    message = _format_cli_error("unknown <flag>", kind="usage")

    assert message.startswith("Usage error: unknown &lt;flag&gt;")
    assert message.endswith("Run 'devsynth --help' for usage.")


@pytest.mark.fast
def test_format_cli_error_runtime_hint() -> None:
    """_format_cli_error should provide actionable runtime guidance."""

    message = _format_cli_error("failed <step>", kind="runtime")

    assert message.startswith("Error: failed &lt;step&gt;")
    assert message.endswith("Re-run with --help for usage or check logs.")


@pytest.mark.fast
def test_command_help_format_includes_sections() -> None:
    """CommandHelp.format should assemble all optional sections."""

    help_text = CommandHelp(
        summary="Summary",
        description="Details",
        examples=[{"command": "devsynth foo", "description": "does foo"}],
        notes=["remember bar"],
        options={"--flag": "toggle"},
    ).format()

    assert "Summary" in help_text
    assert "Details" in help_text
    assert "$ devsynth foo" in help_text
    assert "does foo" in help_text
    assert "remember bar" in help_text
    assert "--flag: toggle" in help_text
