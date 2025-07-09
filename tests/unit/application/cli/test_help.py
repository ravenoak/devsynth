import pytest
from unittest.mock import patch, MagicMock, call
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from devsynth.application.cli.help import get_command_help, display_command_help, get_all_commands_help, display_all_commands_help, create_command_table, display_command_table, format_command_help_markdown, display_command_help_markdown, get_command_usage, display_command_usage, get_command_examples, display_command_examples
from devsynth.application.cli.autocomplete import COMMANDS, COMMAND_DESCRIPTIONS, COMMAND_EXAMPLES


def test_get_command_help_returns_expected_result():
    """Test that get_command_help returns help text for a specific command.

ReqID: N/A"""
    command = next(iter(COMMANDS))
    help_text = get_command_help(command)
    assert command in help_text
    assert COMMAND_DESCRIPTIONS.get(command, '') in help_text
    help_text = get_command_help('nonexistent')
    assert 'nonexistent' in help_text
    assert 'Command not found' in help_text


def test_display_command_help_succeeds():
    """Test that display_command_help displays help text for a specific command.

ReqID: N/A"""
    console = MagicMock(spec=Console)
    command = next(iter(COMMANDS))
    with patch('devsynth.application.cli.help.get_command_help'
        ) as mock_get_help:
        mock_get_help.return_value = f'Help for {command}'
        display_command_help(command, console)
        mock_get_help.assert_called_once_with(command)
        console.print.assert_called_once()


def test_get_all_commands_help_returns_expected_result():
    """Test that get_all_commands_help returns help text for all commands.

ReqID: N/A"""
    help_text = get_all_commands_help()
    assert 'Available Commands' in help_text
    for command in COMMANDS:
        assert command in help_text


def test_display_all_commands_help_succeeds():
    """Test that display_all_commands_help displays help text for all commands.

ReqID: N/A"""
    console = MagicMock(spec=Console)
    with patch('devsynth.application.cli.help.get_all_commands_help'
        ) as mock_get_help:
        mock_get_help.return_value = 'Help for all commands'
        display_all_commands_help(console)
        mock_get_help.assert_called_once()
        console.print.assert_called_once()


def test_create_command_table_succeeds():
    """Test that create_command_table creates a table of commands.

ReqID: N/A"""
    table = create_command_table()
    assert isinstance(table, Table)
    commands = list(COMMANDS)[:3]
    table = create_command_table(commands)
    assert isinstance(table, Table)


def test_display_command_table_succeeds():
    """Test that display_command_table displays a table of commands.

ReqID: N/A"""
    # Test case 1: No commands specified
    console1 = MagicMock(spec=Console)
    with patch('devsynth.application.cli.help.create_command_table'
        ) as mock_create_table:
        mock_table = MagicMock(spec=Table)
        mock_create_table.return_value = mock_table
        display_command_table(console=console1)
        mock_create_table.assert_called_once_with(None)
        console1.print.assert_called_once_with(mock_table)

    # Test case 2: Commands specified
    console2 = MagicMock(spec=Console)
    commands = list(COMMANDS)[:3]
    with patch('devsynth.application.cli.help.create_command_table'
        ) as mock_create_table:
        mock_table = MagicMock(spec=Table)
        mock_create_table.return_value = mock_table
        display_command_table(commands, console2)
        mock_create_table.assert_called_once_with(commands)
        console2.print.assert_called_once_with(mock_table)


def test_format_command_help_markdown_succeeds():
    """Test that format_command_help_markdown formats help text as markdown.

ReqID: N/A"""
    command = next(iter(COMMAND_EXAMPLES.keys()))
    markdown = format_command_help_markdown(command)
    assert isinstance(markdown, Markdown)
    assert command in markdown.markup
    assert COMMAND_DESCRIPTIONS.get(command, '') in markdown.markup
    markdown = format_command_help_markdown('nonexistent')
    assert isinstance(markdown, Markdown)
    assert 'nonexistent' in markdown.markup
    assert 'Command not found' in markdown.markup


def test_display_command_help_markdown_succeeds():
    """Test that display_command_help_markdown displays help text as markdown.

ReqID: N/A"""
    console = MagicMock(spec=Console)
    command = next(iter(COMMANDS))
    with patch('devsynth.application.cli.help.format_command_help_markdown'
        ) as mock_format:
        mock_markdown = MagicMock(spec=Markdown)
        mock_format.return_value = mock_markdown
        display_command_help_markdown(command, console)
        mock_format.assert_called_once_with(command)
        console.print.assert_called_once_with(mock_markdown)


def test_get_command_usage_returns_expected_result():
    """Test that get_command_usage returns usage information for a command.

ReqID: N/A"""
    command = next(iter(COMMANDS))
    usage = get_command_usage(command)
    assert command in usage
    usage = get_command_usage('nonexistent')
    assert 'nonexistent' in usage
    assert 'Command not found' in usage


def test_display_command_usage_succeeds():
    """Test that display_command_usage displays usage information for a command.

ReqID: N/A"""
    console = MagicMock(spec=Console)
    command = next(iter(COMMANDS))
    with patch('devsynth.application.cli.help.get_command_usage'
        ) as mock_get_usage:
        mock_get_usage.return_value = f'Usage for {command}'
        display_command_usage(command, console)
        mock_get_usage.assert_called_once_with(command)
        console.print.assert_called_once()


def test_get_command_examples_returns_expected_result():
    """Test that get_command_examples returns examples for a command.

ReqID: N/A"""
    command = next(iter(COMMAND_EXAMPLES.keys()))
    examples = get_command_examples(command)
    # Check that all examples for the command are in the returned list
    for example in COMMAND_EXAMPLES.get(command, []):
        assert example in examples
    command_without_examples = next((cmd for cmd in COMMANDS if cmd not in
        COMMAND_EXAMPLES), None)
    if command_without_examples:
        examples = get_command_examples(command_without_examples)
        assert 'No examples available' in str(examples)
    examples = get_command_examples('nonexistent')
    assert 'nonexistent' in str(examples[0]) if examples else False
    assert 'Command not found' in str(examples[0]) if examples else False


def test_display_command_examples_succeeds():
    """Test that display_command_examples displays examples for a command.

ReqID: N/A"""
    console = MagicMock(spec=Console)
    command = next(iter(COMMANDS))
    with patch('devsynth.application.cli.help.get_command_examples'
        ) as mock_get_examples:
        mock_get_examples.return_value = f'Examples for {command}'
        display_command_examples(command, console)
        mock_get_examples.assert_called_once_with(command)
        console.print.assert_called_once()
