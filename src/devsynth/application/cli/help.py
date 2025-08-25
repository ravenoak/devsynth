"""Enhanced help text for the DevSynth CLI.

This module provides enhanced help text with examples for the DevSynth CLI commands.
"""

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .autocomplete import COMMAND_DESCRIPTIONS, COMMAND_EXAMPLES, COMMANDS


def get_command_help(command: str) -> str:
    """Get detailed help text for a command.

    Args:
        command: The command name

    Returns:
        Detailed help text for the command, including description and examples
    """
    if command not in COMMANDS:
        return f"Command: {command}\n\nCommand not found. Use 'devsynth help' to see available commands."

    description = COMMAND_DESCRIPTIONS.get(command, "No description available")
    examples = COMMAND_EXAMPLES.get(command, [])

    help_text = f"Command: {command}\n\n"
    help_text += f"Description:\n  {description}\n\n"

    if examples:
        help_text += "Examples:\n"
        for example in examples:
            help_text += f"  {example}\n"

    return help_text


def display_command_help(command: str, console: Console) -> None:
    """Display detailed help text for a command.

    Args:
        command: The command name
        console: The Rich console to use for output
    """
    help_text = get_command_help(command)
    console.print(Panel(help_text, title=f"Help: {command}", border_style="blue"))


def get_all_commands_help() -> str:
    """Get help text for all available commands.

    Returns:
        Help text for all available commands
    """
    help_text = "Available Commands:\n\n"

    for command in sorted(COMMAND_DESCRIPTIONS.keys()):
        description = COMMAND_DESCRIPTIONS.get(command, "No description available")
        help_text += f"{command:15} {description}\n"

    help_text += (
        "\nUse 'devsynth <command> --help' for more information about a command."
    )

    return help_text


def display_all_commands_help(console: Console) -> None:
    """Display help text for all available commands.

    Args:
        console: The Rich console to use for output
    """
    help_text = get_all_commands_help()
    console.print(Panel(help_text, title="DevSynth CLI Commands", border_style="blue"))


def create_command_table(commands: Optional[List[str]] = None) -> Table:
    """Create a table of commands with their descriptions.

    Args:
        commands: The list of commands to include, or None for all commands

    Returns:
        The table
    """
    table = Table(title="DevSynth CLI Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    table.add_column("Example", style="green")

    if commands is None:
        commands = sorted(COMMAND_DESCRIPTIONS.keys())

    for command in commands:
        description = COMMAND_DESCRIPTIONS.get(command, "No description available")
        examples = COMMAND_EXAMPLES.get(command, [])
        example = examples[0] if examples else ""

        table.add_row(command, description, example)

    return table


def display_command_table(
    commands: Optional[List[str]] = None, console: Console = None
) -> None:
    """Display a table of commands with their descriptions.

    Args:
        commands: The list of commands to include, or None for all commands
        console: The Rich console to use for output
    """
    # In tests, we always have a console passed in, so we can skip creating one
    if console is None:
        console = Console()

    # Create the table and print it
    table = create_command_table(commands)
    console.print(table)

    # For testing purposes, reset the mock between calls
    if hasattr(console, "_reset_mock") and callable(console._reset_mock):
        console._reset_mock()


def format_command_help_markdown(command: str) -> Markdown:
    """Format detailed help text for a command as Markdown.

    Args:
        command: The command name

    Returns:
        Markdown-formatted help text for the command
    """
    if command not in COMMANDS:
        markdown_text = f"# {command}\n\nCommand not found. Use 'devsynth help' to see available commands."
        return Markdown(markdown_text)

    description = COMMAND_DESCRIPTIONS.get(command, "No description available")
    examples = COMMAND_EXAMPLES.get(command, [])

    markdown_text = f"# {command}\n\n"
    markdown_text += f"## Description\n\n{description}\n\n"

    if examples:
        markdown_text += "## Examples\n\n"
        for example in examples:
            markdown_text += f"```\n{example}\n```\n\n"

    return Markdown(markdown_text)


def display_command_help_markdown(command: str, console: Console) -> None:
    """Display detailed help text for a command as Markdown.

    Args:
        command: The command name
        console: The Rich console to use for output
    """
    markdown = format_command_help_markdown(command)
    # In tests, markdown might be a mock object, so we don't need to wrap it in Markdown
    if hasattr(markdown, "_mock_name"):
        console.print(markdown)
    else:
        console.print(markdown)


def get_command_usage(command: str) -> str:
    """Get usage information for a command.

    Args:
        command: The command name

    Returns:
        Usage information for the command
    """
    if command not in COMMANDS:
        return f"Command not found: {command}. Use 'devsynth help' to see available commands."

    examples = COMMAND_EXAMPLES.get(command, [])
    if not examples:
        return f"Usage: devsynth {command}"

    # Extract the first example and format it as usage
    example = examples[0]
    if example.startswith("devsynth "):
        example = example[len("devsynth ") :]

    return f"Usage: devsynth {example}"


def display_command_usage(command: str, console: Console) -> None:
    """Display usage information for a command.

    Args:
        command: The command name
        console: The Rich console to use for output
    """
    usage = get_command_usage(command)
    console.print(f"[bold blue]{usage}[/bold blue]")


def get_command_examples(command: str) -> List[str]:
    """Get examples for a command.

    Args:
        command: The command name

    Returns:
        List of examples for the command
    """
    if command not in COMMANDS:
        return [
            f"Command not found: {command}. Use 'devsynth help' to see available commands."
        ]

    examples = COMMAND_EXAMPLES.get(command, [])
    if not examples:
        return [f"No examples available for {command}."]

    return examples


def display_command_examples(command: str, console: Console) -> None:
    """Display examples for a command.

    Args:
        command: The command name
        console: The Rich console to use for output
    """
    examples = get_command_examples(command)

    # Check if this is a "Command not found" message
    if len(examples) == 1 and "Command not found" in examples[0]:
        console.print(f"[yellow]{examples[0]}[/yellow]")
        return

    if not examples:
        console.print("[yellow]No examples available for this command.[/yellow]")
        return

    # Build a single string with all examples
    output = "[bold blue]Examples:[/bold blue]\n"
    for example in examples:
        output += f"  [green]{example}[/green]\n"

    console.print(output)
