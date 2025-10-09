"""Standardized command output formatting for DevSynth CLI.

This module provides standardized formatting for different types of command output,
ensuring consistent output across all CLI commands.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum, auto
from typing import cast

import yaml
from rich.box import MINIMAL, ROUNDED, SIMPLE, SQUARE, Box
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from devsynth.application.cli.models import (
    CommandDisplay,
    CommandListData,
    CommandResultData,
    CommandTableData,
    CommandTableRow,
    ManifestSummary,
)
from devsynth.interface.output_formatter import OutputFormat, OutputFormatter
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class CommandOutputType(Enum):
    """Types of command output."""

    RESULT = auto()  # General command result
    SUCCESS = auto()  # Success message
    ERROR = auto()  # Error message
    WARNING = auto()  # Warning message
    INFO = auto()  # Informational message
    DATA = auto()  # Data output (table, list, etc.)
    HELP = auto()  # Help text
    DEBUG = auto()  # Debug information


class CommandOutputStyle(Enum):
    """Styles for command output."""

    MINIMAL = auto()  # Minimal styling (plain text)
    SIMPLE = auto()  # Simple styling (basic formatting)
    STANDARD = auto()  # Standard styling (default)
    DETAILED = auto()  # Detailed styling (more information)
    COMPACT = auto()  # Compact styling (less whitespace)
    EXPANDED = auto()  # Expanded styling (more whitespace)


class StandardizedOutputFormatter:
    """Standardized output formatter for DevSynth CLI commands.

    This class provides standardized formatting for different types of command output,
    ensuring consistent output across all CLI commands.
    """

    def __init__(
        self,
        console: Console | None = None,
        base_formatter: OutputFormatter | None = None,
    ):
        """Initialize the standardized output formatter.

        Args:
            console: Optional Rich console for output
            base_formatter: Optional base output formatter to use
        """
        self.console = console or Console()
        self.base_formatter = base_formatter or OutputFormatter(console)

        # Define standard styles for different output types
        self.styles = {
            CommandOutputType.RESULT: Style(color="white"),
            CommandOutputType.SUCCESS: Style(color="green", bold=True),
            CommandOutputType.ERROR: Style(color="red", bold=True),
            CommandOutputType.WARNING: Style(color="yellow", bold=True),
            CommandOutputType.INFO: Style(color="blue"),
            CommandOutputType.DATA: Style(color="cyan"),
            CommandOutputType.HELP: Style(color="magenta"),
            CommandOutputType.DEBUG: Style(dim=True),
        }

        # Define standard boxes for different output styles
        self.boxes = {
            CommandOutputStyle.MINIMAL: None,
            CommandOutputStyle.SIMPLE: SIMPLE,
            CommandOutputStyle.STANDARD: ROUNDED,
            CommandOutputStyle.DETAILED: SQUARE,
            CommandOutputStyle.COMPACT: MINIMAL,
            CommandOutputStyle.EXPANDED: ROUNDED,
        }

        # Define standard padding for different output styles
        self.padding = {
            CommandOutputStyle.MINIMAL: (0, 0),
            CommandOutputStyle.SIMPLE: (0, 1),
            CommandOutputStyle.STANDARD: (1, 1),
            CommandOutputStyle.DETAILED: (1, 2),
            CommandOutputStyle.COMPACT: (0, 0),
            CommandOutputStyle.EXPANDED: (2, 2),
        }

        logger.debug("Initialized StandardizedOutputFormatter")

    def format_message(
        self,
        message: str,
        output_type: CommandOutputType = CommandOutputType.RESULT,
        output_style: CommandOutputStyle = CommandOutputStyle.STANDARD,
        title: str | None = None,
        subtitle: str | None = None,
        highlight: bool = False,
    ) -> CommandDisplay:
        """Format a message with standardized styling.

        Args:
            message: The message to format
            output_type: The type of output
            output_style: The style of output
            title: Optional title for the message
            subtitle: Optional subtitle for the message
            highlight: Whether to highlight the message

        Returns:
            The formatted message
        """
        # Get the style for the output type
        style = self.styles.get(output_type, self.styles[CommandOutputType.RESULT])

        # Get the box and padding for the output style
        box = self.boxes.get(output_style, self.boxes[CommandOutputStyle.STANDARD])
        padding = self.padding.get(
            output_style, self.padding[CommandOutputStyle.STANDARD]
        )

        # Format the message based on the output style
        if output_style == CommandOutputStyle.MINIMAL:
            renderable: str | Text | Panel = Text(message, style=style)
        elif output_style == CommandOutputStyle.SIMPLE:
            if highlight:
                renderable = Text(message, style=style)
            else:
                renderable = message
        else:
            # Standard, detailed, compact, or expanded styling
            # Check if the message contains Rich markup
            if "[" in message and "]" in message:
                # For Rich markup, pass the message directly
                content = message
            else:
                # Format the message using the base formatter
                content = self.base_formatter.format_message(
                    message,
                    message_type=(
                        output_type.name.lower()
                        if output_type != CommandOutputType.RESULT
                        else None
                    ),
                    highlight=highlight,
                )

            renderable = Panel(
                content,
                title=title,
                subtitle=subtitle,
                border_style=style,
                box=box,
                padding=padding,
                highlight=highlight,
            )

        return CommandDisplay(
            renderable=renderable,
            output_type=output_type,
            output_style=output_style,
            title=title,
            subtitle=subtitle,
        )

    def format_table(
        self,
        data: (
            CommandTableData
            | CommandTableRow
            | Sequence[CommandTableRow]
            | Mapping[str, object]
            | Sequence[Mapping[str, object]]
            | ManifestSummary
            | object
        ),
        output_style: CommandOutputStyle = CommandOutputStyle.STANDARD,
        title: str | None = None,
        subtitle: str | None = None,
        show_header: bool = True,
        box: Box | None = None,
        padding: tuple[int, int] | None = None,
    ) -> CommandDisplay:
        """Format data as a table with standardized styling.

        Args:
            data: The data to format as a table
            output_style: The style of output
            title: Optional title for the table
            subtitle: Optional subtitle for the table
            show_header: Whether to show the table header
            box: Optional box style for the table
            padding: Optional padding for the table cells

        Returns:
            The formatted table
        """
        # Get the box and padding for the output style
        if box is None:
            box = self.boxes.get(output_style, self.boxes[CommandOutputStyle.STANDARD])
        if padding is None:
            padding = self.padding.get(
                output_style, self.padding[CommandOutputStyle.STANDARD]
            )

        table = Table(
            title=title,
            caption=subtitle,
            show_header=show_header,
            box=box,
            padding=padding,
        )

        if isinstance(data, ManifestSummary):
            table_data = data.as_table()
        elif isinstance(data, CommandTableData):
            table_data = data
        elif isinstance(data, CommandTableRow):
            table_data = CommandTableData(rows=(data,))
        elif isinstance(data, Mapping):
            rows: list[CommandTableRow] = []
            for key, value in data.items():
                nested = value
                if isinstance(nested, (Mapping, Sequence)) and not isinstance(
                    nested, (str, bytes, bytearray)
                ):
                    nested = json.dumps(nested, indent=2)
                rows.append(CommandTableRow({"Key": str(key), "Value": nested}))
            table_data = CommandTableData(rows=tuple(rows))
            show_header = True
            table = Table(
                title=title,
                caption=subtitle,
                show_header=show_header,
                box=box,
                padding=padding,
            )
            table.add_column("Key")
            table.add_column("Value")
            for row in table_data:
                table.add_row(row.get_str("Key"), str(row.get("Value", "")))
            return CommandDisplay(
                renderable=table,
                output_type=CommandOutputType.DATA,
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )
        elif isinstance(data, Sequence) and not isinstance(
            data, (str, bytes, bytearray)
        ):
            if data and isinstance(data[0], CommandTableRow):
                command_rows = cast(Sequence[CommandTableRow], data)
                table_data = CommandTableData(rows=tuple(command_rows))
            elif data and isinstance(data[0], Mapping):
                mapping_rows = cast(Sequence[Mapping[str, object]], data)
                table_data = CommandTableData.from_iterable(
                    [CommandTableRow.from_mapping(row) for row in mapping_rows]
                )
            else:
                table.add_column("Items")
                for item in data:
                    table.add_row(str(item))
                return CommandDisplay(
                    renderable=table,
                    output_type=CommandOutputType.DATA,
                    output_style=output_style,
                    title=title,
                    subtitle=subtitle,
                )
        else:
            logger.warning("Unsupported data type for table formatting: %s", type(data))
            table.add_column("Data")
            table.add_row(str(data))
            return CommandDisplay(
                renderable=table,
                output_type=CommandOutputType.DATA,
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )

        if not table_data:
            table.add_column("Data")
            table.add_row("<empty>")
            return CommandDisplay(
                renderable=table,
                output_type=CommandOutputType.DATA,
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )

        if not table.columns:
            column_names = [str(column) for column in table_data[0].keys()]
            for column in column_names:
                table.add_column(column)
        else:
            column_names = [column.header or "" for column in table.columns]

        for row in table_data:
            table.add_row(*(str(row.get(column, "")) for column in column_names))

        return CommandDisplay(
            renderable=table,
            output_type=CommandOutputType.DATA,
            output_style=output_style,
            title=title,
            subtitle=subtitle,
        )

    def format_list(
        self,
        items: CommandListData | Sequence[object],
        output_style: CommandOutputStyle = CommandOutputStyle.STANDARD,
        title: str | None = None,
        subtitle: str | None = None,
        bullet: str = "•",
    ) -> CommandDisplay:
        """Format a list with standardized styling.

        Args:
            items: The list items to format
            output_style: The style of output
            title: Optional title for the list
            subtitle: Optional subtitle for the list
            bullet: The bullet character to use for list items

        Returns:
            The formatted list
        """
        # Format the list based on the output style
        if isinstance(items, CommandListData):
            list_data = items
        elif isinstance(items, Sequence) and not isinstance(
            items, (str, bytes, bytearray)
        ):
            list_data = CommandListData.from_iterable(tuple(items))
        else:
            list_data = CommandListData.from_iterable((items,))

        if output_style == CommandOutputStyle.MINIMAL:
            renderable: str | Text | Panel = "\n".join(
                [f"{bullet} {item}" for item in list_data]
            )
        elif output_style == CommandOutputStyle.SIMPLE:
            # Simple styling (basic formatting)
            text = Text()
            for item in list_data:
                text.append(f"{bullet} {item}\n")
            renderable = text
        else:
            # Standard, detailed, compact, or expanded styling
            # Get the box and padding for the output style
            box = self.boxes.get(output_style, self.boxes[CommandOutputStyle.STANDARD])
            padding = self.padding.get(
                output_style, self.padding[CommandOutputStyle.STANDARD]
            )

            # Create a tree for the list
            tree = Tree(title or "")
            for item in list_data:
                tree.add(str(item))

            # Create a panel with the tree
            renderable = Panel(
                tree,
                title=title,
                subtitle=subtitle,
                box=box,
                padding=padding,
            )

        return CommandDisplay(
            renderable=renderable,
            output_type=CommandOutputType.DATA,
            output_style=output_style,
            title=title,
            subtitle=subtitle,
        )

    def format_code(
        self,
        code: str,
        language: str = "python",
        output_style: CommandOutputStyle = CommandOutputStyle.STANDARD,
        title: str | None = None,
        subtitle: str | None = None,
        line_numbers: bool = True,
        word_wrap: bool = True,
    ) -> CommandDisplay:
        """Format code with standardized styling.

        Args:
            code: The code to format
            language: The programming language of the code
            output_style: The style of output
            title: Optional title for the code
            subtitle: Optional subtitle for the code
            line_numbers: Whether to show line numbers
            word_wrap: Whether to wrap long lines

        Returns:
            The formatted code
        """
        # Format the code based on the output style
        if output_style == CommandOutputStyle.MINIMAL:
            renderable: str | Syntax | Panel = code
        elif output_style == CommandOutputStyle.SIMPLE:
            # Simple styling (basic formatting)
            renderable = Syntax(
                code,
                language,
                theme="ansi_dark",
                line_numbers=False,
                word_wrap=word_wrap,
            )
        else:
            # Standard, detailed, compact, or expanded styling
            # Get the box and padding for the output style
            box = self.boxes.get(output_style, self.boxes[CommandOutputStyle.STANDARD])
            padding = self.padding.get(
                output_style, self.padding[CommandOutputStyle.STANDARD]
            )

            # Create a syntax object for the code
            syntax = Syntax(
                code,
                language,
                theme="ansi_dark",
                line_numbers=line_numbers,
                word_wrap=word_wrap,
            )

            # Create a panel with the syntax object
            renderable = Panel(
                syntax,
                title=title,
                subtitle=subtitle,
                box=box,
                padding=padding,
            )

        return CommandDisplay(
            renderable=renderable,
            output_type=CommandOutputType.DATA,
            output_style=output_style,
            title=title,
            subtitle=subtitle,
        )

    def format_help(
        self,
        command: str,
        description: str,
        usage: str,
        examples: CommandTableData | Sequence[CommandTableRow],
        options: CommandTableData | Sequence[CommandTableRow],
        output_style: CommandOutputStyle = CommandOutputStyle.STANDARD,
    ) -> CommandDisplay:
        """Format help text with standardized styling.

        Args:
            command: The command name
            description: The command description
            usage: The command usage
            examples: List of example dictionaries with 'description' and 'command' keys
            options: List of option dictionaries with 'name', 'description', and 'default' keys
            output_style: The style of output

        Returns:
            The formatted help text
        """
        # Format the help text based on the output style
        options_data = (
            options
            if isinstance(options, CommandTableData)
            else CommandTableData.from_iterable(list(options))
        )
        examples_data = (
            examples
            if isinstance(examples, CommandTableData)
            else CommandTableData.from_iterable(list(examples))
        )

        if output_style == CommandOutputStyle.MINIMAL:
            # Minimal styling (plain text)
            help_text = f"{command}\n\n{description}\n\nUsage:\n{usage}\n\nOptions:\n"
            for option in options_data:
                default = option.get("default")
                default_fragment = f" (default: {default})" if default else ""
                help_text += f"  {option.get_str('name')}: {option.get_str('description')}{default_fragment}\n"
            help_text += "\nExamples:\n"
            for example in examples_data:
                help_text += f"  {example.get_str('description')}:\n  {example.get_str('command')}\n\n"
            renderable: str | Text | Panel = help_text
        elif output_style == CommandOutputStyle.SIMPLE:
            # Simple styling (basic formatting)
            help_text = Text()
            help_text.append(f"{command}\n\n", style="bold")
            help_text.append(f"{description}\n\n")
            help_text.append("Usage:\n", style="bold")
            help_text.append(f"{usage}\n\n")
            help_text.append("Options:\n", style="bold")
            for option in options_data:
                default = option.get("default")
                default_fragment = f" (default: {default})" if default else ""
                help_text.append(f"  {option.get_str('name')}: ", style="bold")
                help_text.append(f"{option.get_str('description')}{default_fragment}\n")
            help_text.append("\nExamples:\n", style="bold")
            for example in examples_data:
                help_text.append(
                    f"  {example.get_str('description')}:\n", style="italic"
                )
                help_text.append(f"  {example.get_str('command')}\n\n")
            renderable = help_text
        else:
            # Standard, detailed, compact, or expanded styling
            # Get the box and padding for the output style
            box = self.boxes.get(output_style, self.boxes[CommandOutputStyle.STANDARD])
            padding = self.padding.get(
                output_style, self.padding[CommandOutputStyle.STANDARD]
            )

            # Create a table for the options
            options_table = Table(box=box, show_header=True, padding=padding)
            options_table.add_column("Option", style="bold")
            options_table.add_column("Description")
            options_table.add_column("Default", style="dim")

            for option in options_data:
                default = option.get("default", "")
                options_table.add_row(
                    option.get_str("name"), option.get_str("description"), str(default)
                )

            # Create a table for the examples
            examples_table = Table(box=box, show_header=True, padding=padding)
            examples_table.add_column("Description", style="bold")
            examples_table.add_column("Command", style="cyan")

            for example in examples_data:
                examples_table.add_row(
                    example.get_str("description"), example.get_str("command")
                )

            # Create a panel with the help text
            content = Text()
            content.append(f"{description}\n\n")
            content.append("Usage:\n", style="bold")
            content.append(f"{usage}\n\n")
            content.append("Options:\n", style="bold")

            # Add the options table
            from rich.console import Console

            console = Console(file=None)
            with console.capture() as capture:
                console.print(options_table)
            content.append(capture.get())

            content.append("\nExamples:\n", style="bold")

            # Add the examples table
            with console.capture() as capture:
                console.print(examples_table)
            content.append(capture.get())

            renderable = Panel(
                content,
                title=f"[bold]Command: {command}[/bold]",
                subtitle="[dim]Use --help for more information[/dim]",
                box=box,
                padding=padding,
            )

        return CommandDisplay(
            renderable=renderable,
            output_type=CommandOutputType.HELP,
            output_style=output_style,
            title=command,
            subtitle="Help",
        )

    def format_command_result(
        self,
        result: CommandResultData | object,
        output_type: CommandOutputType = CommandOutputType.RESULT,
        output_style: CommandOutputStyle = CommandOutputStyle.STANDARD,
        title: str | None = None,
        subtitle: str | None = None,
    ) -> CommandDisplay:
        """Format a command result with standardized styling.

        Args:
            result: The command result to format
            output_type: The type of output
            output_style: The style of output
            title: Optional title for the result
            subtitle: Optional subtitle for the result

        Returns:
            The formatted command result
        """
        # Format the result based on its type
        if isinstance(result, CommandDisplay):
            return result
        if isinstance(result, ManifestSummary):
            return self.format_table(
                result.as_table(),
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )
        if isinstance(result, str):
            # String result
            return self.format_message(
                result,
                output_type=output_type,
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )
        elif isinstance(result, Mapping):
            return self.format_table(
                result,
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )
        elif isinstance(result, Sequence) and not isinstance(
            result, (str, bytes, bytearray)
        ):
            if result and isinstance(result[0], (CommandTableRow, Mapping)):
                table_rows = cast(
                    Sequence[CommandTableRow | Mapping[str, object]],
                    result,
                )
                normalized_rows = CommandTableData.from_iterable(table_rows)
                return self.format_table(
                    normalized_rows,
                    output_style=output_style,
                    title=title,
                    subtitle=subtitle,
                )
            return self.format_list(
                result,
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )
        else:
            # Other types (convert to string)
            return self.format_message(
                str(result),
                output_type=output_type,
                output_style=output_style,
                title=title,
                subtitle=subtitle,
            )

    def display(
        self,
        content: CommandResultData | object,
        output_type: CommandOutputType = CommandOutputType.RESULT,
        output_style: CommandOutputStyle = CommandOutputStyle.STANDARD,
        title: str | None = None,
        subtitle: str | None = None,
    ) -> None:
        """Display content with standardized styling.

        Args:
            content: The content to display
            output_type: The type of output
            output_style: The style of output
            title: Optional title for the content
            subtitle: Optional subtitle for the content
        """
        # Format the content
        formatted_content = self.format_command_result(
            content,
            output_type=output_type,
            output_style=output_style,
            title=title,
            subtitle=subtitle,
        )

        # Display the formatted content
        self.console.print(formatted_content.renderable)


# Create a singleton instance for easy access
standardized_formatter = StandardizedOutputFormatter()
