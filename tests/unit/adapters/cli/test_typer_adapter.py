import pytest
from unittest.mock import patch, MagicMock
import typer
from devsynth.adapters.cli.typer_adapter import build_app, _warn_if_features_disabled, show_help, parse_args, run_cli
from devsynth.application.cli.requirements_commands import requirements_app
from devsynth.application.cli import config_app
from devsynth.core.config_loader import load_config


def test_build_app_returns_expected_result():
    """Test that build_app returns a Typer application with commands registered.

ReqID: N/A"""
    app = build_app()
    assert isinstance(app, typer.Typer)
    command_names = [cmd.name for cmd in app.registered_commands]
    assert 'init' in command_names
    assert 'spec' in command_names
    assert 'test' in command_names
    assert 'code' in command_names
    assert 'run-pipeline' in command_names
    assert hasattr(app, 'callback')
    app_help = app.info.help
    assert 'DevSynth CLI' in app_help
    with patch('typer.Typer.add_typer') as mock_add_typer:
        test_app = build_app()
        assert mock_add_typer.call_count >= 2
        mock_add_typer.assert_any_call(requirements_app, name='requirements')
        mock_add_typer.assert_any_call(config_app, name='config', help=
            'Manage configuration settings')


@patch('devsynth.adapters.cli.typer_adapter.load_config')
@patch('devsynth.adapters.cli.typer_adapter.typer.echo')
def test_warn_if_features_disabled_all_disabled_succeeds(mock_echo,
    mock_load_config):
    """Test that _warn_if_features_disabled shows a warning when all features are disabled.

ReqID: N/A"""
    mock_config = MagicMock()
    mock_config.features = {'feature1': False, 'feature2': False}
    mock_load_config.return_value = mock_config
    _warn_if_features_disabled()
    mock_echo.assert_called_once()
    assert 'All optional features are disabled' in mock_echo.call_args[0][0]


@patch('devsynth.adapters.cli.typer_adapter.load_config')
@patch('devsynth.adapters.cli.typer_adapter.typer.echo')
def test_warn_if_features_disabled_some_enabled_succeeds(mock_echo,
    mock_load_config):
    """Test that _warn_if_features_disabled doesn't show a warning when some features are enabled.

ReqID: N/A"""
    mock_config = MagicMock()
    mock_config.features = {'feature1': True, 'feature2': False}
    mock_load_config.return_value = mock_config
    _warn_if_features_disabled()
    mock_echo.assert_not_called()


@patch('devsynth.adapters.cli.typer_adapter.load_config')
@patch('devsynth.adapters.cli.typer_adapter.typer.echo')
def test_warn_if_features_disabled_exception_raises_error(mock_echo,
    mock_load_config):
    """Test that _warn_if_features_disabled handles exceptions gracefully.

ReqID: N/A"""
    mock_load_config.side_effect = Exception('Config error')
    _warn_if_features_disabled()
    mock_echo.assert_not_called()


@patch('devsynth.adapters.cli.typer_adapter.Console')
@patch('devsynth.adapters.cli.typer_adapter.build_app')
def test_show_help_succeeds(mock_build_app, mock_console):
    """Test that show_help displays the CLI help message.

ReqID: N/A"""
    # Create a mock app with the necessary attributes
    mock_app = MagicMock()
    mock_app.info = MagicMock()
    mock_app.info.help = "Test help text"
    mock_app.registered_commands = []
    mock_app.registered_typers = []

    # Set up the mock build_app to return our mock app
    mock_build_app.return_value = mock_app

    # Create a mock console instance
    mock_console_instance = MagicMock()
    mock_console.return_value = mock_console_instance

    # Call the function under test
    show_help()

    # Verify that the console.print method was called
    assert mock_console_instance.print.call_count > 0

    # Verify that build_app was called
    mock_build_app.assert_called_once()


@patch('devsynth.adapters.cli.typer_adapter._warn_if_features_disabled')
@patch('devsynth.adapters.cli.typer_adapter.build_app')
def test_parse_args_has_expected(mock_build_app, mock_warn):
    """Test that parse_args calls the app with the provided arguments.

ReqID: N/A"""
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app
    parse_args(['init', '--path', './test'])
    mock_warn.assert_called_once()
    mock_app.assert_called_once_with(['init', '--path', './test'])


@patch('devsynth.adapters.cli.typer_adapter._warn_if_features_disabled')
@patch('devsynth.adapters.cli.typer_adapter.build_app')
def test_run_cli_succeeds(mock_build_app, mock_warn):
    """Test that run_cli calls the app.

ReqID: N/A"""
    mock_app = MagicMock()
    mock_build_app.return_value = mock_app
    run_cli()
    mock_warn.assert_called_once()
    mock_app.assert_called_once_with()
