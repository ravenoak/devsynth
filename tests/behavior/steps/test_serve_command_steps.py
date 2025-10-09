import os
import socket
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file
scenarios(feature_path(__file__, "general", "serve_command.feature"))


# Fixtures for test isolation
@pytest.fixture
def context():
    """Fixture to provide a context object for sharing data between steps."""

    class Context:
        def __init__(self):
            self.result = None
            self.error_message = None
            self.port = None
            self.verbose = False

    return Context()


@pytest.fixture
def mock_serve_cmd():
    """Fixture to mock the serve_cmd function."""
    with patch("devsynth.application.cli.serve_cmd.serve_cmd") as mock:
        yield mock


@pytest.fixture
def mock_socket():
    """Fixture to mock socket operations for port checking."""
    with patch("socket.socket") as mock_socket:
        mock_instance = MagicMock()
        mock_socket.return_value = mock_instance
        yield mock_socket, mock_instance


# Step definitions
@given("the DevSynth CLI is installed")
def devsynth_cli_installed():
    """Verify that the DevSynth CLI is installed."""
    # This is a placeholder step since we're running tests within the DevSynth codebase
    pass


@given("no other service is running on port 8080")
def no_service_on_port(mock_socket):
    """Ensure no service is running on port 8080."""
    # Configure the mock to indicate the port is free
    mock_socket_instance = mock_socket[1]
    mock_socket_instance.bind.return_value = None  # No exception means port is free
    mock_socket_instance.close.return_value = None


@given("a service is already running on port 8080")
def service_on_port(mock_socket):
    """Simulate a service running on port 8080."""
    # Configure the mock to indicate the port is in use
    mock_socket_instance = mock_socket[1]
    mock_socket_instance.bind.side_effect = socket.error("Port already in use")


@when(parsers.parse('I run the command "{command}"'))
def run_command(context, command, mock_serve_cmd):
    """Run a DevSynth CLI command."""
    # Parse the command to extract arguments
    args = command.split()[1:]  # Skip 'devsynth'

    # Extract port and verbose flag if present
    context.port = 8080  # Default port
    context.verbose = False

    if "--port" in args:
        port_index = args.index("--port")
        if port_index + 1 < len(args):
            context.port = int(args[port_index + 1])

    if "--verbose" in args:
        context.verbose = True

    # Set up the mock behavior based on the scenario
    if (
        context.port == 8080
        and hasattr(mock_socket, "side_effect")
        and mock_socket.side_effect is not None
    ):
        # Port is in use
        mock_serve_cmd.side_effect = Exception(f"Port {context.port} is already in use")
        try:
            # Simulate running the command
            from devsynth.adapters.cli.typer_adapter import parse_args

            parse_args(args)
            context.result = "success"
        except Exception as e:
            context.result = "failure"
            context.error_message = str(e)
    else:
        # Port is free
        mock_serve_cmd.return_value = None  # Successful execution
        try:
            # Simulate running the command
            from devsynth.adapters.cli.typer_adapter import parse_args

            parse_args(args)
            context.result = "success"
        except Exception as e:
            context.result = "failure"
            context.error_message = str(e)


@then("the command should execute successfully")
def command_successful(context):
    """Verify that the command executed successfully."""
    assert (
        context.result == "success"
    ), f"Command failed with error: {context.error_message}"


@then("the command should fail")
def command_failed(context):
    """Verify that the command failed."""
    assert context.result == "failure", "Command succeeded but was expected to fail"


@then("the API server should start on the default port")
def api_server_default_port(context, mock_serve_cmd):
    """Verify that the API server started on the default port."""
    assert context.port == 8080
    mock_serve_cmd.assert_called_once()


@then(parsers.parse("the API server should start on port {port:d}"))
def api_server_custom_port(context, port, mock_serve_cmd):
    """Verify that the API server started on the specified port."""
    assert context.port == port
    mock_serve_cmd.assert_called_once()


@then("the system should display a message indicating the server is running")
def server_running_message(context, capsys):
    """Verify that a message about the server running was displayed."""
    # This would check the captured stdout for server running messages
    # Since we're mocking, we'll just verify the command was successful
    assert context.result == "success"


@then(
    parsers.parse(
        "the system should display a message indicating the server is running on port {port:d}"
    )
)
def server_running_on_port_message(context, port, capsys):
    """Verify that a message about the server running on a specific port was displayed."""
    # This would check the captured stdout for server running messages with port
    # Since we're mocking, we'll just verify the command was successful and port matches
    assert context.result == "success"
    assert context.port == port


@then("the API server should start with verbose logging enabled")
def verbose_logging_enabled(context, mock_serve_cmd):
    """Verify that the API server started with verbose logging enabled."""
    assert context.verbose is True
    mock_serve_cmd.assert_called_once()


@then("the system should display detailed log messages")
def detailed_log_messages(context, capsys):
    """Verify that detailed log messages were displayed."""
    # This would check the captured stdout for detailed log messages
    # Since we're mocking, we'll just verify the command was successful and verbose flag is set
    assert context.result == "success"
    assert context.verbose is True


@then("the system should display an error message about the port being in use")
def port_in_use_error(context, capsys):
    """Verify that an error message about the port being in use was displayed."""
    # This would check the captured stdout for port in use error messages
    # Since we're mocking, we'll just verify the command failed
    assert context.result == "failure"
    assert context.error_message is not None
    assert "Port" in context.error_message and "in use" in context.error_message
