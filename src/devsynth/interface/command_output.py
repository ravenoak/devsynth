"""Command output formatting utilities.

This module provides utilities for standardizing command output formatting
across all DevSynth commands and interfaces.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from devsynth.interface.output_formatter import OutputFormat, OutputFormatter


class MessageType(str, Enum):
    """Enum for message types."""

    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"
    INFO = "info"
    NORMAL = "normal"
    HEADING = "heading"


class CommandOutput:
    """Utility for standardizing command output formatting.

    This class provides a consistent interface for formatting command output
    across all DevSynth commands and interfaces.
    """

    def __init__(self, console: Console | None = None):
        """Initialize the command output formatter.

        Args:
            console: Optional Rich console to use for output
        """
        self.formatter = OutputFormatter(console)
        self.console = console

    def set_console(self, console: Console) -> None:
        """Set the console to use for output.

        Args:
            console: The Rich console to use
        """
        self.console = console
        self.formatter.set_console(console)

    def format_message(
        self,
        message: str,
        message_type: str | MessageType | None = None,
        highlight: bool = False,
    ) -> Any:
        """Format a message based on its type and highlight flag.

        Args:
            message: The message to format
            message_type: Optional message type override
            highlight: Whether to highlight the message

        Returns:
            The formatted message
        """
        # Convert MessageType enum to string if needed
        if isinstance(message_type, MessageType):
            message_type = message_type.value

        return self.formatter.format_message(message, message_type, highlight)

    def display_message(
        self,
        message: str,
        message_type: str | MessageType | None = None,
        highlight: bool = False,
    ) -> None:
        """Display a formatted message.

        Args:
            message: The message to display
            message_type: Optional message type override
            highlight: Whether to highlight the message
        """
        # Convert MessageType enum to string if needed
        if isinstance(message_type, MessageType):
            message_type = message_type.value

        formatted = self.format_message(message, message_type, highlight)

        if self.console:
            if isinstance(formatted, (Panel, Table, Syntax, Markdown)):
                self.console.print(formatted)
            elif isinstance(formatted, Text):
                self.console.print(formatted)
            else:
                self.console.print(str(formatted))
        else:
            print(str(formatted))

    def format_error(
        self, error: Exception | str, include_suggestions: bool = True
    ) -> Any:
        """Format an error message with optional suggestions.

        Args:
            error: The error to format
            include_suggestions: Whether to include actionable suggestions

        Returns:
            The formatted error message
        """
        error_str = str(error)

        if include_suggestions:
            # Add suggestions based on error type or content
            if "permission" in error_str.lower():
                error_str += "\n\nSuggestion: Check file permissions or run with elevated privileges."
            elif "not found" in error_str.lower():
                error_str += "\n\nSuggestion: Verify the file path or resource name."
            elif "timeout" in error_str.lower():
                error_str += "\n\nSuggestion: Check network connectivity or increase timeout settings."
            elif "api key" in error_str.lower():
                error_str += "\n\nSuggestion: Verify your API key is correctly set in the configuration."

        return self.format_message(error_str, MessageType.ERROR)

    def display_error(
        self, error: Exception | str, include_suggestions: bool = True
    ) -> None:
        """Display a formatted error message with optional suggestions.

        Args:
            error: The error to display
            include_suggestions: Whether to include actionable suggestions
        """
        formatted = self.format_error(error, include_suggestions)

        if self.console:
            self.console.print(formatted)
        else:
            print(str(formatted))

    def format_success(self, message: str) -> Any:
        """Format a success message.

        Args:
            message: The message to format

        Returns:
            The formatted success message
        """
        return self.format_message(message, MessageType.SUCCESS)

    def display_success(self, message: str) -> None:
        """Display a formatted success message.

        Args:
            message: The message to display
        """
        self.display_message(message, MessageType.SUCCESS)

    def format_warning(self, message: str) -> Any:
        """Format a warning message.

        Args:
            message: The message to format

        Returns:
            The formatted warning message
        """
        return self.format_message(message, MessageType.WARNING)

    def display_warning(self, message: str) -> None:
        """Display a formatted warning message.

        Args:
            message: The message to display
        """
        self.display_message(message, MessageType.WARNING)

    def format_info(self, message: str) -> Any:
        """Format an info message.

        Args:
            message: The message to format

        Returns:
            The formatted info message
        """
        return self.format_message(message, MessageType.INFO)

    def display_info(self, message: str) -> None:
        """Display a formatted info message.

        Args:
            message: The message to display
        """
        self.display_message(message, MessageType.INFO)

    def format_heading(self, message: str, level: int = 1) -> Any:
        """Format a heading message.

        Args:
            message: The message to format
            level: The heading level (1-6)

        Returns:
            The formatted heading message
        """
        # Create a markdown-style heading
        heading = "#" * min(level, 6) + " " + message
        return self.format_message(heading, MessageType.HEADING)

    def display_heading(self, message: str, level: int = 1) -> None:
        """Display a formatted heading message.

        Args:
            message: The message to display
            level: The heading level (1-6)
        """
        formatted = self.format_heading(message, level)

        if self.console:
            self.console.print(formatted)
        else:
            print(str(formatted))

    def format_table(self, data: dict[str, Any], title: str | None = None) -> Any:
        """Format a dictionary as a table.

        Args:
            data: The dictionary to format
            title: Optional title for the table

        Returns:
            The formatted table
        """
        return self.formatter.format_structured(data, OutputFormat.TABLE, title)

    def display_table(self, data: dict[str, Any], title: str | None = None) -> None:
        """Display a formatted table.

        Args:
            data: The dictionary to display as a table
            title: Optional title for the table
        """
        formatted = self.format_table(data, title)

        if self.console:
            self.console.print(formatted)
        else:
            print(str(formatted))

    def format_list(self, items: list[Any], title: str | None = None) -> Any:
        """Format a list of items.

        Args:
            items: The list of items to format
            title: Optional title for the list

        Returns:
            The formatted list
        """
        return self.formatter._list_to_rich(items, title)

    def display_list(self, items: list[Any], title: str | None = None) -> None:
        """Display a formatted list.

        Args:
            items: The list of items to display
            title: Optional title for the list
        """
        formatted = self.format_list(items, title)

        if self.console:
            self.console.print(formatted)
        else:
            print(str(formatted))

    def format_json(self, data: Any, title: str | None = None) -> Any:
        """Format data as JSON.

        Args:
            data: The data to format
            title: Optional title for the output

        Returns:
            The formatted JSON
        """
        return self.formatter.format_structured(data, OutputFormat.JSON, title)

    def display_json(self, data: Any, title: str | None = None) -> None:
        """Display formatted JSON.

        Args:
            data: The data to display as JSON
            title: Optional title for the output
        """
        formatted = self.format_json(data, title)

        if self.console:
            self.console.print(formatted)
        else:
            print(str(formatted))

    def format_yaml(self, data: Any, title: str | None = None) -> Any:
        """Format data as YAML.

        Args:
            data: The data to format
            title: Optional title for the output

        Returns:
            The formatted YAML
        """
        return self.formatter.format_structured(data, OutputFormat.YAML, title)

    def display_yaml(self, data: Any, title: str | None = None) -> None:
        """Display formatted YAML.

        Args:
            data: The data to display as YAML
            title: Optional title for the output
        """
        formatted = self.format_yaml(data, title)

        if self.console:
            self.console.print(formatted)
        else:
            print(str(formatted))

    def format_command_result(
        self,
        result: dict[str, Any],
        format_name: str | None = None,
        title: str | None = None,
    ) -> Any:
        """Format a command result in the specified format.

        This is a convenience method for CLI commands to format their output
        in a consistent way based on the user's preferred format.

        Args:
            result: The command result to format
            format_name: The name of the format to use (json, yaml, table, etc.)
            title: Optional title for the output

        Returns:
            The formatted command result
        """
        return self.formatter.format_command_output(result, format_name, title)

    def display_command_result(
        self,
        result: dict[str, Any],
        format_name: str | None = None,
        title: str | None = None,
    ) -> None:
        """Display a formatted command result.

        Args:
            result: The command result to display
            format_name: The name of the format to use (json, yaml, table, etc.)
            title: Optional title for the output
        """
        formatted = self.format_command_result(result, format_name, title)

        if self.console:
            self.console.print(formatted)
        else:
            print(str(formatted))


# Create a singleton instance for easy access
command_output = CommandOutput()
