from __future__ import annotations

import pytest
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from devsynth.application.cli.autocomplete import (
    COMMAND_DESCRIPTIONS,
    COMMAND_EXAMPLES,
    COMMANDS,
)
from devsynth.application.cli.help import (
    create_command_table,
    display_all_commands_help,
    display_command_examples,
    display_command_help,
    display_command_help_markdown,
    display_command_table,
    display_command_usage,
    format_command_help_markdown,
    get_all_commands_help,
    get_command_examples,
    get_command_help,
    get_command_usage,
)


@pytest.mark.medium
def test_get_command_help_returns_expected_result() -> None:
    """Test that get_command_help returns help text for a specific command.

    ReqID: N/A"""

    command = next(iter(COMMANDS))
    help_text = get_command_help(command)
    assert command in help_text
    assert COMMAND_DESCRIPTIONS.get(command, "") in help_text

    help_text = get_command_help("nonexistent")
    assert "nonexistent" in help_text
    assert "Command not found" in help_text


@pytest.mark.medium
def test_display_command_help_succeeds(rich_console: Console) -> None:
    """Display_command_help should render a panel containing command metadata."""

    command = next(iter(COMMANDS))
    display_command_help(command, rich_console)

    output = rich_console.export_text(clear=True)
    assert command in output
    assert COMMAND_DESCRIPTIONS.get(command, "") in output


@pytest.mark.medium
def test_get_all_commands_help_returns_expected_result() -> None:
    """Test that get_all_commands_help returns help text for all commands.

    ReqID: N/A"""

    help_text = get_all_commands_help()
    assert "Available Commands" in help_text
    for command in COMMANDS:
        assert command in help_text


@pytest.mark.medium
def test_display_all_commands_help_succeeds(rich_console: Console) -> None:
    """The CLI overview should include each command and description."""

    display_all_commands_help(rich_console)
    output = rich_console.export_text(clear=True)
    assert "DevSynth CLI Commands" in output
    for command in COMMANDS:
        assert command in output


@pytest.mark.medium
def test_create_command_table_succeeds() -> None:
    """Test that create_command_table creates a table of commands.

    ReqID: N/A"""

    table = create_command_table()
    assert isinstance(table, Table)

    commands = list(COMMANDS)[:3]
    table = create_command_table(commands)
    assert isinstance(table, Table)


@pytest.mark.medium
def test_display_command_table_succeeds(rich_console: Console) -> None:
    """Display_command_table should render a Rich table for the provided commands."""

    display_command_table(None, rich_console)
    default_output = rich_console.export_text(clear=True)
    assert "Command" in default_output

    commands = list(COMMANDS)[:3]
    display_command_table(commands, rich_console)
    subset_output = rich_console.export_text(clear=True)
    for command in commands:
        assert command in subset_output


@pytest.mark.medium
def test_format_command_help_markdown_succeeds() -> None:
    """Test that format_command_help_markdown formats help text as markdown.

    ReqID: N/A"""

    command = next(iter(COMMAND_EXAMPLES.keys()))
    markdown = format_command_help_markdown(command)
    assert isinstance(markdown, Markdown)
    assert command in markdown.markup
    assert COMMAND_DESCRIPTIONS.get(command, "") in markdown.markup

    markdown = format_command_help_markdown("nonexistent")
    assert isinstance(markdown, Markdown)
    assert "nonexistent" in markdown.markup
    assert "Command not found" in markdown.markup


@pytest.mark.medium
def test_display_command_help_markdown_succeeds(rich_console: Console) -> None:
    """Ensure Markdown help is rendered to the console."""

    command = next(iter(COMMANDS))
    display_command_help_markdown(command, rich_console)
    output = rich_console.export_text(clear=True)
    assert command in output


@pytest.mark.medium
def test_get_command_usage_returns_expected_result() -> None:
    """Test that get_command_usage returns usage information for a command.

    ReqID: N/A"""

    command = next(iter(COMMANDS))
    usage = get_command_usage(command)
    assert command in usage

    usage = get_command_usage("nonexistent")
    assert "nonexistent" in usage
    assert "Command not found" in usage


@pytest.mark.medium
def test_display_command_usage_succeeds(rich_console: Console) -> None:
    """Usage information should be printed to the console in bold blue text."""

    command = next(iter(COMMANDS))
    display_command_usage(command, rich_console)
    output = rich_console.export_text(clear=True)
    assert command in output


@pytest.mark.medium
def test_get_command_examples_returns_expected_result() -> None:
    """Test that get_command_examples returns examples for a command.

    ReqID: N/A"""

    command = next(iter(COMMAND_EXAMPLES.keys()))
    examples = get_command_examples(command)
    assert tuple(examples) == tuple(COMMAND_EXAMPLES.get(command, []))

    command_without_examples = next(
        (cmd for cmd in COMMANDS if cmd not in COMMAND_EXAMPLES),
        None,
    )
    if command_without_examples is not None:
        no_example_output = get_command_examples(command_without_examples)
        assert "No examples available" in " ".join(
            str(item) for item in no_example_output
        )

    unknown_examples = get_command_examples("nonexistent")
    assert "Command not found" in str(unknown_examples[0])


@pytest.mark.medium
def test_display_command_examples_succeeds(rich_console: Console) -> None:
    """Test that display_command_examples displays examples for a command.

    ReqID: N/A"""

    command = next(iter(COMMANDS))
    display_command_examples(command, rich_console)
    output = rich_console.export_text(clear=True)
    assert "Examples:" in output
    for example in COMMAND_EXAMPLES.get(command, []):
        assert example in output
