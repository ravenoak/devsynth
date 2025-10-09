"""Helpers for presenting command help information within the CLI."""

from __future__ import annotations

from collections.abc import Sequence

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from devsynth.application.cli.models import (
    CommandListData,
    CommandTableData,
    CommandTableRow,
)

from .autocomplete import COMMAND_DESCRIPTIONS, COMMAND_EXAMPLES, COMMANDS

_COMMAND_SET = frozenset(COMMANDS)


def _command_details(command: str) -> tuple[str, tuple[str, ...]]:
    """Return description and examples for ``command``."""

    description = COMMAND_DESCRIPTIONS.get(command, "No description available")
    examples = tuple(COMMAND_EXAMPLES.get(command, ()))
    return description, examples


def _build_command_rows(commands: Sequence[str] | None) -> CommandTableData:
    """Create table rows describing ``commands``."""

    selected = (
        sorted(COMMAND_DESCRIPTIONS.keys()) if commands is None else list(commands)
    )
    rows = []
    for command in selected:
        description, examples = _command_details(command)
        example = examples[0] if examples else ""
        rows.append(
            CommandTableRow(
                {
                    "Command": command,
                    "Description": description,
                    "Example": example,
                }
            )
        )
    return CommandTableData(rows=tuple(rows))


def _build_examples(command: str) -> CommandListData:
    """Return the example list for ``command``."""

    _, examples = _command_details(command)
    if not examples:
        return CommandListData.from_iterable((f"No examples available for {command}.",))
    return CommandListData.from_iterable(examples)


def _render_panel(console: Console, content: str, *, title: str) -> None:
    """Render ``content`` within a :class:`~rich.panel.Panel`."""

    console.print(Panel(content, title=title, border_style="blue"))


def get_command_help(command: str) -> str:
    """Return the textual help summary for ``command``."""

    if command not in _COMMAND_SET:
        return (
            f"Command: {command}\n\n"
            "Command not found. Use 'devsynth help' to see available commands."
        )

    description, examples = _command_details(command)

    help_text = f"Command: {command}\n\n"
    help_text += f"Description:\n  {description}\n\n"

    if examples:
        help_text += "Examples:\n"
        for example in examples:
            help_text += f"  {example}\n"

    return help_text


def display_command_help(command: str, console: Console) -> None:
    """Display detailed help text for ``command`` using ``console``."""

    help_text = get_command_help(command)
    _render_panel(console, help_text, title=f"Help: {command}")


def get_all_commands_help() -> str:
    """Return a textual overview of every registered command."""

    help_text = "Available Commands:\n\n"

    for command in sorted(COMMAND_DESCRIPTIONS.keys()):
        description = COMMAND_DESCRIPTIONS.get(command, "No description available")
        help_text += f"{command:15} {description}\n"

    help_text += (
        "\nUse 'devsynth <command> --help' for more information about a command."
    )
    return help_text


def display_all_commands_help(console: Console) -> None:
    """Render the overview of commands to ``console``."""

    help_text = get_all_commands_help()
    _render_panel(console, help_text, title="DevSynth CLI Commands")


def create_command_table(commands: Sequence[str] | None = None) -> Table:
    """Create a Rich table showing commands, descriptions, and examples."""

    data = _build_command_rows(commands)

    table = Table(title="DevSynth CLI Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    table.add_column("Example", style="green")

    for row in data:
        table.add_row(
            row.get_str("Command"),
            row.get_str("Description"),
            row.get_str("Example"),
        )

    return table


def display_command_table(commands: Sequence[str] | None, console: Console) -> None:
    """Display a table of commands with their descriptions."""

    table = create_command_table(commands)
    console.print(table)


def format_command_help_markdown(command: str) -> Markdown:
    """Return Markdown formatted help text for ``command``."""

    if command not in _COMMAND_SET:
        markdown_text = (
            f"# {command}\n\n"
            "Command not found. Use 'devsynth help' to see available commands."
        )
        return Markdown(markdown_text)

    description, examples = _command_details(command)

    markdown_text = f"# {command}\n\n"
    markdown_text += f"## Description\n\n{description}\n\n"

    if examples:
        markdown_text += "## Examples\n\n"
        for example in examples:
            markdown_text += f"```\n{example}\n```\n\n"

    return Markdown(markdown_text)


def display_command_help_markdown(command: str, console: Console) -> None:
    """Display Markdown formatted help text for ``command``."""

    markdown = format_command_help_markdown(command)
    console.print(markdown)


def get_command_usage(command: str) -> str:
    """Return usage information for ``command``."""

    if command not in _COMMAND_SET:
        return f"Command not found: {command}. Use 'devsynth help' to see available commands."

    _, examples = _command_details(command)
    if not examples:
        return f"Usage: devsynth {command}"

    example = examples[0]
    if example.startswith("devsynth "):
        example = example[len("devsynth ") :]

    return f"Usage: devsynth {example}"


def display_command_usage(command: str, console: Console) -> None:
    """Display usage information for ``command``."""

    usage = get_command_usage(command)
    console.print(f"[bold blue]{usage}[/bold blue]")


def get_command_examples(command: str) -> CommandListData:
    """Return example invocations for ``command``."""

    if command not in _COMMAND_SET:
        return CommandListData.from_iterable(
            (
                f"Command not found: {command}. Use 'devsynth help' to see available commands.",
            )
        )

    return _build_examples(command)


def display_command_examples(command: str, console: Console) -> None:
    """Display example invocations for ``command``."""

    examples = get_command_examples(command)

    first_example = examples[0]
    if (
        len(examples) == 1
        and isinstance(first_example, str)
        and "Command not found" in first_example
    ):
        console.print(f"[yellow]{first_example}[/yellow]")
        return

    if not examples:
        console.print("[yellow]No examples available for this command.[/yellow]")
        return

    output = "[bold blue]Examples:[/bold blue]\n"
    for example in examples:
        output += f"  [green]{example}[/green]\n"

    console.print(output)


__all__ = [
    "create_command_table",
    "display_all_commands_help",
    "display_command_examples",
    "display_command_help",
    "display_command_help_markdown",
    "display_command_table",
    "display_command_usage",
    "format_command_help_markdown",
    "get_all_commands_help",
    "get_command_examples",
    "get_command_help",
    "get_command_usage",
]
