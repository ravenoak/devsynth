"""Colorized output utilities used across the DevSynth CLI."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import Optional, Union

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from devsynth.application.cli.models import (
    CommandListData,
    CommandTableData,
    CommandTableRow,
    ManifestSummary,
)


class OutputType(str, Enum):
    """Enum for different types of output."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"
    CODE = "code"
    COMMAND = "command"
    RESULT = "result"
    HEADER = "header"
    SUBHEADER = "subheader"


# Color styles for different output types
OUTPUT_STYLES = {
    OutputType.INFO: "blue",
    OutputType.SUCCESS: "green",
    OutputType.WARNING: "yellow",
    OutputType.ERROR: "red",
    OutputType.DEBUG: "magenta",
    OutputType.CODE: "cyan",
    OutputType.COMMAND: "green",
    OutputType.RESULT: "blue",
    OutputType.HEADER: "bold blue",
    OutputType.SUBHEADER: "bold cyan",
}


def colorize(message: str, output_type: Union[OutputType, str]) -> str:
    """Colorize a message based on its output type.

    Args:
        message: The message to colorize
        output_type: The type of output

    Returns:
        The colorized message
    """
    if isinstance(output_type, str):
        output_type = OutputType(output_type)

    style = OUTPUT_STYLES.get(output_type, "default")
    return f"[{style}]{message}[/{style}]"


def print_message(
    message: str,
    output_type: Union[OutputType, str] = OutputType.INFO,
    console: Optional[Console] = None,
) -> None:
    """Print a colorized message.

    Args:
        message: The message to print
        output_type: The type of output
        console: The Rich console to use for output
    """
    if console is None:
        console = Console()

    colorized_message = colorize(message, output_type)
    console.print(colorized_message)


def print_info(message: str, console: Optional[Console] = None) -> None:
    """Print an informational message.

    Args:
        message: The message to print
        console: The Rich console to use for output
    """
    print_message(message, OutputType.INFO, console)


def print_success(message: str, console: Optional[Console] = None) -> None:
    """Print a success message.

    Args:
        message: The message to print
        console: The Rich console to use for output
    """
    print_message(message, OutputType.SUCCESS, console)


def print_warning(message: str, console: Optional[Console] = None) -> None:
    """Print a warning message.

    Args:
        message: The message to print
        console: The Rich console to use for output
    """
    print_message(message, OutputType.WARNING, console)


def print_error(message: str, console: Optional[Console] = None) -> None:
    """Print an error message.

    Args:
        message: The message to print
        console: The Rich console to use for output
    """
    print_message(message, OutputType.ERROR, console)


def print_debug(message: str, console: Optional[Console] = None) -> None:
    """Print a debug message.

    Args:
        message: The message to print
        console: The Rich console to use for output
    """
    print_message(message, OutputType.DEBUG, console)


def print_code(
    code: str,
    language: str = "python",
    console: Optional[Console] = None,
) -> None:
    """Print code with syntax highlighting.

    Args:
        code: The code to print
        language: The programming language of the code
        console: The Rich console to use for output
    """
    if console is None:
        console = Console()

    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def print_command(command: str, console: Optional[Console] = None) -> None:
    """Print a command.

    Args:
        command: The command to print
        console: The Rich console to use for output
    """
    print_message(command, OutputType.COMMAND, console)


def print_result(result: str, console: Optional[Console] = None) -> None:
    """Print a command result.

    Args:
        result: The result to print
        console: The Rich console to use for output
    """
    print_message(result, OutputType.RESULT, console)


def print_header(header: str, console: Optional[Console] = None) -> None:
    """Print a header.

    Args:
        header: The header to print
        console: The Rich console to use for output
    """
    print_message(header, OutputType.HEADER, console)


def print_subheader(subheader: str, console: Optional[Console] = None) -> None:
    """Print a subheader.

    Args:
        subheader: The subheader to print
        console: The Rich console to use for output
    """
    print_message(subheader, OutputType.SUBHEADER, console)


def print_panel(
    message: str,
    title: Optional[str] = None,
    output_type: Union[OutputType, str] = OutputType.INFO,
    console: Optional[Console] = None,
) -> None:
    """Print a message in a panel.

    Args:
        message: The message to print
        title: The title of the panel
        output_type: The type of output
        console: The Rich console to use for output
    """
    if console is None:
        console = Console()

    if isinstance(output_type, str):
        output_type = OutputType(output_type)

    style = OUTPUT_STYLES.get(output_type, "default")
    console.print(Panel(message, title=title, border_style=style))


def _ensure_table_data(
    data: CommandTableData | Sequence[CommandTableRow] | ManifestSummary,
) -> CommandTableData:
    if isinstance(data, ManifestSummary):
        return data.as_table()
    if isinstance(data, CommandTableData):
        return data
    return CommandTableData.from_iterable(tuple(data))


def print_table(
    data: CommandTableData | Sequence[CommandTableRow] | ManifestSummary,
    columns: Optional[Sequence[str]] = None,
    title: Optional[str] = None,
    console: Optional[Console] = None,
) -> None:
    """Print data in a table.

    Args:
        data: The data to print
        columns: The columns to include, or None for all columns
        title: The title of the table
        console: The Rich console to use for output
    """
    if console is None:
        console = Console()

    table_data = _ensure_table_data(data)

    if not table_data:
        console.print("[yellow]No data to display[/yellow]")
        return

    selected_columns = (
        list(columns) if columns is not None else list(table_data[0].keys())
    )

    table = Table(title=title)
    for column in selected_columns:
        table.add_column(column)

    for row in table_data:
        table.add_row(*[str(row.get(column, "")) for column in selected_columns])

    console.print(table)


def print_list(
    items: CommandListData | Sequence[object],
    *,
    console: Optional[Console] = None,
) -> None:
    """Render a bullet list using the list data model."""

    if console is None:
        console = Console()

    list_data = (
        items
        if isinstance(items, CommandListData)
        else CommandListData.from_iterable(tuple(items))
    )
    if not list_data:
        console.print("[yellow]No items to display[/yellow]")
        return

    for item in list_data:
        console.print(f"• {item}")


def print_markdown(
    markdown: str,
    console: Optional[Console] = None,
) -> None:
    """Print Markdown-formatted text.

    Args:
        markdown: The Markdown-formatted text to print
        console: The Rich console to use for output
    """
    if console is None:
        console = Console()

    console.print(Markdown(markdown))


def format_output(
    message: str,
    output_type: Union[OutputType, str] = OutputType.INFO,
) -> Text:
    """Format a message based on its output type.

    Args:
        message: The message to format
        output_type: The type of output

    Returns:
        The formatted message
    """
    if isinstance(output_type, str):
        output_type = OutputType(output_type)

    style = OUTPUT_STYLES.get(output_type, "default")
    return Text(message, style=style)
