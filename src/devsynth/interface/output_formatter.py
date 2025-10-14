"""Output formatting utilities for DevSynth interfaces.

This module provides utilities for formatting output in a consistent way
across different interfaces (CLI, WebUI, etc.).
"""

import html
import json
import re
import textwrap
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from rich.box import ROUNDED, Box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from devsynth.interface.ux_bridge import sanitize_output as global_sanitize_output


class OutputFormat(Enum):
    """Enum for output formats."""

    TEXT = auto()
    JSON = auto()
    YAML = auto()
    MARKDOWN = auto()
    TABLE = auto()
    RICH = auto()  # Rich formatted output


class OutputFormatter:
    """Formatter for standardizing output across different interfaces.

    This class provides methods for formatting different types of output
    (messages, errors, warnings, etc.) in a consistent way, with proper
    sanitization and styling.
    """

    # Regular expressions for detecting message types
    ERROR_PATTERN = re.compile(r"^(ERROR|FAILED|CRITICAL)[\s:]", re.IGNORECASE)
    WARNING_PATTERN = re.compile(r"^WARNING[\s:]", re.IGNORECASE)
    SUCCESS_PATTERN = re.compile(
        r"^(SUCCESS|COMPLETED)[\s:]|successfully", re.IGNORECASE
    )
    INFO_PATTERN = re.compile(r"^(INFO|NOTE)[\s:]", re.IGNORECASE)
    HEADING_PATTERN = re.compile(r"^(#+)\s+(.*)")

    # Default indentation and spacing settings
    DEFAULT_INDENT = 2
    DEFAULT_SPACING = 1
    DEFAULT_LINE_WIDTH = 100

    # Default table settings
    DEFAULT_TABLE_BOX = ROUNDED

    # Output format mappings
    FORMAT_EXTENSIONS = {
        "json": OutputFormat.JSON,
        "yaml": OutputFormat.YAML,
        "yml": OutputFormat.YAML,
        "md": OutputFormat.MARKDOWN,
        "markdown": OutputFormat.MARKDOWN,
        "txt": OutputFormat.TEXT,
        "text": OutputFormat.TEXT,
        "table": OutputFormat.TABLE,
        "rich": OutputFormat.RICH,
    }

    def __init__(
        self,
        console: Optional[Console] = None,
        default_format: OutputFormat = OutputFormat.RICH,
    ) -> None:
        """Initialize the output formatter.

        Args:
            console: Optional Rich console to use for output
            default_format: Default output format to use
        """
        self.console = console
        self.default_format = default_format
        self.indent = self.DEFAULT_INDENT
        self.spacing = self.DEFAULT_SPACING
        self.line_width = self.DEFAULT_LINE_WIDTH

    def sanitize_output(self, text: str) -> str:
        """Sanitize and escape user provided text for safe display.

        This delegates to the centralized sanitization policy in
        devsynth.interface.ux_bridge.sanitize_output so that all interfaces
        (CLI, WebUI, Agent API) respect the same environment toggles and
        behavior.

        Args:
            text: The text to sanitize

        Returns:
            The sanitized text

        Raises:
            AttributeError: If text is None
        """
        if text is None:
            raise AttributeError("Cannot sanitize None")

        if text == "":
            return ""

        # Convert to string if not already
        text_str = str(text)

        # Delegate to the global sanitizer (respects DEVSYNTH_SANITIZATION_ENABLED)
        sanitized: str = global_sanitize_output(text_str)
        return sanitized

    def detect_message_type(self, message: str) -> str:
        """Detect the type of message based on its content.

        Args:
            message: The message to analyze

        Returns:
            The message type: "error", "warning", "success", "info", "heading", or "normal"
        """
        if not message:
            return "normal"

        if self.ERROR_PATTERN.search(message):
            return "error"
        elif self.WARNING_PATTERN.search(message):
            return "warning"
        elif self.SUCCESS_PATTERN.search(message):
            return "success"
        elif self.INFO_PATTERN.search(message):
            return "info"

        # Check for markdown-style headings
        heading_match = self.HEADING_PATTERN.match(message)
        if heading_match:
            return "heading"

        return "normal"

    def format_message(
        self, message: str, message_type: Optional[str] = None, highlight: bool = False
    ) -> Union[str, Text, Panel, Markdown]:
        """Format a message based on its type and highlight flag.

        Args:
            message: The message to format
            message_type: Optional message type override
            highlight: Whether to highlight the message

        Returns:
            The formatted message
        """
        # Sanitize the message
        sanitized = self.sanitize_output(message)

        # Detect message type if not provided
        if message_type is None:
            message_type = self.detect_message_type(sanitized)

        # If the message contains Rich markup, return it as is
        if "[" in sanitized and "]" in sanitized:
            return sanitized

        # Format based on message type and highlight flag
        if highlight:
            return Panel(sanitized)
        elif message_type == "error":
            return Text(sanitized, style="bold red")
        elif message_type == "warning":
            return Text(sanitized, style="yellow")
        elif message_type == "success":
            return Text(sanitized, style="green")
        elif message_type == "info":
            return Text(sanitized, style="cyan")
        elif message_type == "heading":
            # Extract heading level and text
            heading_match = self.HEADING_PATTERN.match(sanitized)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                if level == 1:
                    return Text(text, style="bold blue")
                else:
                    return Text(text, style="bold cyan")
            return Text(sanitized)
        else:
            # For normal messages, create a Text object with no style
            return Text(sanitized, style=None)

    def display(self, message: str, highlight: bool = False) -> None:
        """Display a formatted message.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
        """
        if not self.console:
            raise ValueError(
                "Console not set. Use set_console() or provide a console in the constructor."
            )

        formatted = self.format_message(message, highlight=highlight)

        if isinstance(formatted, Panel):
            self.console.print(
                formatted, style="bold white on blue" if highlight else None
            )
        elif isinstance(formatted, Text):
            self.console.print(formatted)
        else:
            self.console.print(formatted)

    def set_console(self, console: Console) -> None:
        """Set the console to use for output.

        Args:
            console: The Rich console to use
        """
        self.console = console

    def format_table(self, data: Dict[str, Any], title: Optional[str] = None) -> str:
        """Format a dictionary as a table.

        Args:
            data: The dictionary to format
            title: Optional title for the table

        Returns:
            The formatted table as a string
        """
        result = []

        if title:
            result.append(f"# {title}")
            result.append("")

        max_key_length = max(len(str(k)) for k in data.keys()) if data else 0

        for key, value in data.items():
            sanitized_key = self.sanitize_output(str(key))
            sanitized_value = self.sanitize_output(str(value))
            result.append(f"{sanitized_key.ljust(max_key_length)} : {sanitized_value}")

        return "\n".join(result)

    def format_list(
        self, items: List[Any], title: Optional[str] = None, bullet: str = "•"
    ) -> str:
        """Format a list of items.

        Args:
            items: The list of items to format
            title: Optional title for the list
            bullet: The bullet character to use

        Returns:
            The formatted list as a string
        """
        result = []

        if title:
            result.append(f"# {title}")
            result.append("")

        for item in items:
            sanitized = self.sanitize_output(str(item))
            result.append(f"{bullet} {sanitized}")

        return "\n".join(result)

    def format_structured(
        self,
        data: Any,
        output_format: Optional[OutputFormat] = None,
        title: Optional[str] = None,
    ) -> Union[str, Panel, Table, Syntax]:
        """Format data in a structured format (JSON, YAML, etc.).

        Args:
            data: The data to format
            output_format: The output format to use (defaults to self.default_format)
            title: Optional title for the output

        Returns:
            The formatted data
        """
        if output_format is None:
            output_format = self.default_format

        # Handle different output formats
        if output_format == OutputFormat.JSON:
            json_str = json.dumps(data, indent=self.indent, sort_keys=True)
            if self.console:
                return Syntax(json_str, "json", theme="monokai", line_numbers=True)
            return json_str

        elif output_format == OutputFormat.YAML:
            yaml_str = yaml.safe_dump(
                data, indent=self.indent, sort_keys=True, default_flow_style=False
            )
            if self.console:
                return Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
            return yaml_str

        elif output_format == OutputFormat.MARKDOWN:
            # Convert data to markdown
            if isinstance(data, dict):
                return self._dict_to_markdown(data, title)
            elif isinstance(data, list):
                return self._list_to_markdown(data, title)
            else:
                return f"# {title if title else 'Data'}\n\n{str(data)}"

        elif output_format == OutputFormat.TABLE:
            # Convert data to a table
            if isinstance(data, dict):
                return self._dict_to_table(data, title)
            elif isinstance(data, list) and all(
                isinstance(item, dict) for item in data
            ):
                return self._list_of_dicts_to_table(data, title)
            else:
                # Fall back to text format for non-tabular data
                return self.format_structured(data, OutputFormat.TEXT, title)

        elif output_format == OutputFormat.RICH:
            # Use Rich formatting based on data type
            if isinstance(data, dict):
                return self._dict_to_rich(data, title)
            elif isinstance(data, list):
                return self._list_to_rich(data, title)
            else:
                return Text(str(data))

        else:  # OutputFormat.TEXT
            # Convert to plain text with consistent formatting
            if isinstance(data, dict):
                return self.format_table(data, title)
            elif isinstance(data, list):
                return self.format_list(data, title)
            else:
                result = []
                if title:
                    result.append(f"# {title}")
                    result.append("")
                result.append(str(data))
                return "\n".join(result)

    def _dict_to_markdown(
        self, data: Dict[str, Any], title: Optional[str] = None
    ) -> str:
        """Convert a dictionary to markdown format.

        Args:
            data: The dictionary to convert
            title: Optional title for the markdown

        Returns:
            The markdown string
        """
        result = []

        if title:
            result.append(f"# {title}")
            result.append("")

        for key, value in data.items():
            sanitized_key = self.sanitize_output(str(key))

            if isinstance(value, dict):
                result.append(f"## {sanitized_key}")
                result.append("")
                for sub_key, sub_value in value.items():
                    sanitized_sub_key = self.sanitize_output(str(sub_key))
                    sanitized_sub_value = self.sanitize_output(str(sub_value))
                    result.append(f"- **{sanitized_sub_key}**: {sanitized_sub_value}")
                result.append("")
            elif isinstance(value, list):
                result.append(f"## {sanitized_key}")
                result.append("")
                for item in value:
                    sanitized_item = self.sanitize_output(str(item))
                    result.append(f"- {sanitized_item}")
                result.append("")
            else:
                sanitized_value = self.sanitize_output(str(value))
                result.append(f"## {sanitized_key}")
                result.append("")
                result.append(sanitized_value)
                result.append("")

        return "\n".join(result)

    def _list_to_markdown(self, data: List[Any], title: Optional[str] = None) -> str:
        """Convert a list to markdown format.

        Args:
            data: The list to convert
            title: Optional title for the markdown

        Returns:
            The markdown string
        """
        result = []

        if title:
            result.append(f"# {title}")
            result.append("")

        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    sanitized_key = self.sanitize_output(str(key))
                    sanitized_value = self.sanitize_output(str(value))
                    result.append(f"- **{sanitized_key}**: {sanitized_value}")
            else:
                sanitized_item = self.sanitize_output(str(item))
                result.append(f"- {sanitized_item}")

        return "\n".join(result)

    def _dict_to_table(
        self, data: Dict[str, Any], title: Optional[str] = None
    ) -> Table:
        """Convert a dictionary to a Rich table.

        Args:
            data: The dictionary to convert
            title: Optional title for the table

        Returns:
            The Rich table
        """
        table = Table(box=self.DEFAULT_TABLE_BOX, title=title)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        for key, value in data.items():
            sanitized_key = self.sanitize_output(str(key))

            if isinstance(value, (dict, list)):
                # For complex values, use JSON representation
                sanitized_value = json.dumps(value, indent=self.indent)
            else:
                sanitized_value = self.sanitize_output(str(value))

            table.add_row(sanitized_key, sanitized_value)

        return table

    def _list_of_dicts_to_table(
        self, data: List[Dict[str, Any]], title: Optional[str] = None
    ) -> Table:
        """Convert a list of dictionaries to a Rich table.

        Args:
            data: The list of dictionaries to convert
            title: Optional title for the table

        Returns:
            The Rich table
        """
        if not data:
            return Table(title=title or "Empty List")

        # Get all unique keys from all dictionaries
        all_keys: set[str] = set()
        for item in data:
            all_keys.update(item.keys())

        # Create the table with columns for each key
        table = Table(box=self.DEFAULT_TABLE_BOX, title=title)
        for key in sorted(all_keys):
            table.add_column(str(key), style="cyan")

        # Add rows for each dictionary
        for item in data:
            row = []
            for key in sorted(all_keys):
                value = item.get(key, "")
                if isinstance(value, (dict, list)):
                    # For complex values, use JSON representation
                    value_str = json.dumps(value, indent=self.indent)
                else:
                    value_str = self.sanitize_output(str(value))
                row.append(value_str)
            table.add_row(*row)

        return table

    def _dict_to_rich(self, data: Dict[str, Any], title: Optional[str] = None) -> Panel:
        """Convert a dictionary to a Rich panel.

        Args:
            data: The dictionary to convert
            title: Optional title for the panel

        Returns:
            The Rich panel
        """
        # Format the dictionary as a table
        table = self._dict_to_table(data)

        # Wrap the table in a panel with the title
        return Panel(table, title=title, border_style="blue")

    def _list_to_rich(
        self, data: List[Any], title: Optional[str] = None
    ) -> Union[Panel, Table]:
        """Convert a list to a Rich panel or table.

        Args:
            data: The list to convert
            title: Optional title for the panel or table

        Returns:
            The Rich panel or table
        """
        # Check if this is a list of dictionaries
        if all(isinstance(item, dict) for item in data):
            # Format as a table
            return self._list_of_dicts_to_table(data, title)
        else:
            # Format as a bulleted list
            text = Text()
            if data:
                for item in data:
                    text.append("• ", style="yellow")
                    text.append(f"{self.sanitize_output(str(item))}\n")
            else:
                text.append("(empty list)")

            # Wrap the text in a panel with the title
            return Panel(text, title=title, border_style="blue")

    def set_format_options(
        self,
        indent: Optional[int] = None,
        spacing: Optional[int] = None,
        line_width: Optional[int] = None,
    ) -> None:
        """Set formatting options.

        Args:
            indent: Number of spaces to use for indentation
            spacing: Number of blank lines between sections
            line_width: Maximum line width for wrapped text
        """
        if indent is not None:
            self.indent = indent
        if spacing is not None:
            self.spacing = spacing
        if line_width is not None:
            self.line_width = line_width

    def format_command_output(
        self, data: Any, format_name: Optional[str] = None, title: Optional[str] = None
    ) -> Union[str, Panel, Table, Syntax]:
        """Format command output in the specified format.

        This is a convenience method for CLI commands to format their output
        in a consistent way based on the user's preferred format.

        Args:
            data: The data to format
            format_name: The name of the format to use (json, yaml, table, etc.)
            title: Optional title for the output

        Returns:
            The formatted output
        """
        # Determine the output format
        output_format = self.default_format
        if format_name:
            output_format = self.FORMAT_EXTENSIONS.get(
                format_name.lower(), self.default_format
            )

        # Format the data
        return self.format_structured(data, output_format, title)


# Create a singleton instance for easy access
formatter = OutputFormatter()
