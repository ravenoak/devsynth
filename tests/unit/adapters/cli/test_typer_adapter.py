import pytest
from unittest.mock import patch, MagicMock
import typer

from devsynth.adapters.cli.typer_adapter import (
    build_app, _warn_if_features_disabled, show_help, parse_args, run_cli
)
from devsynth.core.config_loader import load_config


def test_build_app():
    """Test that build_app returns a Typer application with commands registered."""
    app = build_app()
    assert isinstance(app, typer.Typer)
    
    # Check that some expected commands are registered
    command_names = [cmd.name for cmd in app.registered_commands]
    assert "init" in command_names
    assert "spec" in command_names
    assert "test" in command_names
    assert "code" in command_names
    assert "run-pipeline" in command_names
    
    # Check that some expected sub-apps are registered
    sub_app_names = [app.name for app in app.registered_typer_instances]
    assert "requirements" in sub_app_names
    assert "config" in sub_app_names


@patch("devsynth.adapters.cli.typer_adapter.load_config")
@patch("devsynth.adapters.cli.typer_adapter.typer.echo")
def test_warn_if_features_disabled_all_disabled(mock_echo, mock_load_config):
    """Test that _warn_if_features_disabled shows a warning when all features are disabled."""
    mock_config = MagicMock()
    mock_config.features = {"feature1": False, "feature2": False}
    mock_load_config.return_value = mock_config
    
    _warn_if_features_disabled()
    
    mock_echo.assert_called_once()
    assert "All optional features are disabled" in mock_echo.call_args[0][0]


@patch("devsynth.adapters.cli.typer_adapter.load_config")
@patch("devsynth.adapters.cli.typer_adapter.typer.echo")
def test_warn_if_features_disabled_some_enabled(mock_echo, mock_load_config):
    """Test that _warn_if_features_disabled doesn't show a warning when some features are enabled."""
    mock_config = MagicMock()
    mock_config.features = {"feature1": True, "feature2": False}
    mock_load_config.return_value = mock_config
    
    _warn_if_features_disabled()
    
    mock_echo.assert_not_called()


@patch("devsynth.adapters.cli.typer_adapter.load_config")
@patch("devsynth.adapters.cli.typer_adapter.typer.echo")
def test_warn_if_features_disabled_exception(mock_echo, mock_load_config):
    """Test that _warn_if_features_disabled handles exceptions gracefully."""
    mock_load_config.side_effect = Exception("Config error")
    
    _warn_if_features_disabled()
    
    mock_echo.assert_not_called()


@patch("devsynth.adapters.cli.typer_adapter.build_app")
def test_show_help(mock_build_app):
    """Test that show_help displays the CLI help message."""
    mock_app = MagicMock()
    mock_app.side_effect = SystemExit()
    mock_build_app.return_value = mock_app
    
    # This should not raise an exception
    show_help()
    
    mock_app.assert_called_once_with(["--help"])


@patch("devsynth.adapters.cli.typer_adapter._warn_if_features_disabled")
@patch("devsynth.adapters.cli.typer_adapter.build_app")
def test_parse_args(mock_build_app, mock_warn):
    """Test that parse_args calls the app with the provided arguments."""
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app
    
    parse_args(["init", "--path", "./test"])
    
    mock_warn.assert_called_once()
    mock_app.assert_called_once_with(["init", "--path", "./test"])


@patch("devsynth.adapters.cli.typer_adapter._warn_if_features_disabled")
@patch("devsynth.adapters.cli.typer_adapter.build_app")
def test_run_cli(mock_build_app, mock_warn):
    """Test that run_cli calls the app."""
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app
    
    run_cli()
    
    mock_warn.assert_called_once()
    mock_app.assert_called_once_with()