"""Output formatting utilities for DevSynth interfaces.

This module provides utilities for formatting output in a consistent way
across different interfaces (CLI, WebUI, etc.).
"""

from typing import Optional, Dict, Any, Union
import re
import html

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.markdown import Markdown

from devsynth.security import sanitize_input


class OutputFormatter:
    """Formatter for standardizing output across different interfaces.

    This class provides methods for formatting different types of output
    (messages, errors, warnings, etc.) in a consistent way, with proper
    sanitization and styling.
    """

    # Regular expressions for detecting message types
    ERROR_PATTERN = re.compile(r"^(ERROR|FAILED|CRITICAL)[\s:]", re.IGNORECASE)
    WARNING_PATTERN = re.compile(r"^WARNING[\s:]", re.IGNORECASE)
    SUCCESS_PATTERN = re.compile(r"^(SUCCESS|COMPLETED)[\s:]|successfully", re.IGNORECASE)
    INFO_PATTERN = re.compile(r"^(INFO|NOTE)[\s:]", re.IGNORECASE)
    HEADING_PATTERN = re.compile(r"^(#+)\s+(.*)")

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize the output formatter.

        Args:
            console: Optional Rich console to use for output
        """
        self.console = console

    def sanitize_output(self, text: str) -> str:
        """Sanitize and escape user provided text for safe display.

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

        # First sanitize the input to remove any potentially harmful content
        sanitized = sanitize_input(text_str)

        # Then escape HTML entities to prevent XSS attacks
        escaped = html.escape(sanitized)

        return escaped

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

    def format_message(self, message: str, message_type: Optional[str] = None, highlight: bool = False) -> Union[str, Text, Panel, Markdown]:
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
            raise ValueError("Console not set. Use set_console() or provide a console in the constructor.")

        formatted = self.format_message(message, highlight=highlight)

        if isinstance(formatted, Panel):
            self.console.print(formatted, style="bold white on blue" if highlight else None)
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

    def format_list(self, items: list, title: Optional[str] = None, bullet: str = "•") -> str:
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


# Create a singleton instance for easy access
formatter = OutputFormatter()
