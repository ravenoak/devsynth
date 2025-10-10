"""Enhanced error handling for DevSynth interfaces.

This module provides enhanced error handling with actionable suggestions
and documentation links for DevSynth interfaces.
"""

from __future__ import annotations

import inspect
import re
import traceback
from typing import TYPE_CHECKING, Any, assert_type

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ErrorSuggestion:
    """A suggestion for resolving an error."""

    def __init__(
        self,
        suggestion: str,
        documentation_link: str | None = None,
        command_example: str | None = None,
    ):
        """Initialize an error suggestion.

        Args:
            suggestion: The suggestion text
            documentation_link: Optional link to documentation
            command_example: Optional example command
        """
        self.suggestion = suggestion
        self.documentation_link = documentation_link
        self.command_example = command_example

    def __str__(self) -> str:
        """Return a string representation of the suggestion."""
        parts = [self.suggestion]
        if self.documentation_link:
            parts.append(f"Documentation: {self.documentation_link}")
        if self.command_example:
            parts.append(f"Example: {self.command_example}")
        return "\n".join(parts)


class EnhancedErrorHandler:
    """Enhanced error handler with actionable suggestions and documentation links."""

    # Common error patterns and their suggestions
    ERROR_PATTERNS = [
        # Configuration errors
        (
            r"(?i)config(?:uration)?\s+(?:file|not found|invalid|error)",
            ErrorSuggestion(
                "Your configuration file may be missing or invalid.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/configuration.html",
                "devsynth config --help",
            ),
        ),
        # Permission errors
        (
            r"(?i)permission(?:s)?\s+(?:denied|error)",
            ErrorSuggestion(
                "You may not have the necessary permissions.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/troubleshooting.html#permission-issues",
                "sudo devsynth doctor",
            ),
        ),
        # Network errors
        (
            r"(?i)(?:network|connection|timeout|unreachable)\s+(?:error|issue|problem)",
            ErrorSuggestion(
                "There may be network connectivity issues.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/troubleshooting.html#network-issues",
                "devsynth doctor --check-connectivity",
            ),
        ),
        # Provider errors
        (
            r"(?i)provider\s+(?:error|issue|problem)",
            ErrorSuggestion(
                "There may be issues with the provider configuration.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/providers.html",
                "devsynth config --key provider --value openai",
            ),
        ),
        # Invalid parameters
        (
            r"(?i)invalid\s+(?:parameter|argument|option)",
            ErrorSuggestion(
                "The command parameters may be incorrect.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/cli_reference.html",
                "devsynth [COMMAND] --help",
            ),
        ),
        # Missing files
        (
            r"(?i)(?:file|directory)\s+not\s+found",
            ErrorSuggestion(
                "The specified file or directory may not exist.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/troubleshooting.html#file-not-found",
                "ls -la [PATH]",
            ),
        ),
        # Memory errors
        (
            r"(?i)memory\s+(?:error|issue|problem)",
            ErrorSuggestion(
                "There may be issues with the memory system.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/memory.html",
                "devsynth doctor --check-memory",
            ),
        ),
        # WSDE errors
        (
            r"(?i)wsde\s+(?:error|issue|problem)",
            ErrorSuggestion(
                "There may be issues with the WSDE system.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/wsde.html",
                "devsynth doctor --check-wsde",
            ),
        ),
        # EDRR errors
        (
            r"(?i)edrr\s+(?:error|issue|problem)",
            ErrorSuggestion(
                "There may be issues with the EDRR system.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/edrr.html",
                "devsynth doctor --check-edrr",
            ),
        ),
    ]

    def __init__(self, console: Console | None = None):
        """Initialize the enhanced error handler.

        Args:
            console: Optional Rich console for output
        """
        self.console = console

    def format_error(
        self, error: Exception | dict[str, Any] | str
    ) -> str | Text | Panel:
        """Format an error with actionable suggestions and documentation links.

        Args:
            error: The error to format

        Returns:
            The formatted error message
        """
        # Extract error message
        if isinstance(error, Exception):
            error_message = str(error)
            error_type = type(error).__name__
            error_traceback = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
        elif isinstance(error, dict):
            error_message = error.get("message", str(error))
            error_type = error.get("type", "Error")
            error_traceback = error.get("traceback", "")
        else:
            error_message = str(error)
            error_type = "Error"
            error_traceback = ""

        # Find matching suggestions
        suggestions = self._find_suggestions(error_message)

        # Format the error message
        if self.console:
            return self._format_rich_error(
                error_message, error_type, error_traceback, suggestions
            )
        else:
            return self._format_text_error(
                error_message, error_type, error_traceback, suggestions
            )

    def _find_suggestions(self, error_message: str) -> list[ErrorSuggestion]:
        """Find suggestions for an error message.

        Args:
            error_message: The error message

        Returns:
            A list of suggestions
        """
        suggestions: list[ErrorSuggestion] = []
        for pattern, suggestion in self.ERROR_PATTERNS:
            if re.search(pattern, error_message):
                suggestions.append(suggestion)

        # If no specific suggestions were found, add a generic one
        if not suggestions:
            suggestions.append(
                ErrorSuggestion(
                    "For more information, run the doctor command to diagnose issues.",
                    "https://devsynth.readthedocs.io/en/latest/user_guides/troubleshooting.html",
                    "devsynth doctor",
                )
            )

        return suggestions

    def _format_rich_error(
        self,
        error_message: str,
        error_type: str,
        error_traceback: str,
        suggestions: list[ErrorSuggestion],
    ) -> Panel:
        """Format an error with Rich formatting.

        Args:
            error_message: The error message
            error_type: The error type
            error_traceback: The error traceback
            suggestions: The suggestions

        Returns:
            A Rich panel with the formatted error
        """
        # Create a text object for the error message
        text = Text()
        text.append(f"{error_type}: ", style="bold red")
        text.append(error_message, style="red")

        # Add suggestions
        if suggestions:
            text.append("\n\n", style="red")
            text.append("Suggestions:", style="bold yellow")
            for i, suggestion in enumerate(suggestions, 1):
                text.append(f"\n{i}. ", style="yellow")
                text.append(suggestion.suggestion, style="yellow")
                if suggestion.documentation_link:
                    text.append("\n   Documentation: ", style="dim yellow")
                    text.append(suggestion.documentation_link, style="blue underline")
                if suggestion.command_example:
                    text.append("\n   Example: ", style="dim yellow")
                    text.append(suggestion.command_example, style="green")

        # Create a panel with the text
        return Panel(
            text,
            title="Error",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )

    def _format_text_error(
        self,
        error_message: str,
        error_type: str,
        error_traceback: str,
        suggestions: list[ErrorSuggestion],
    ) -> str:
        """Format an error as plain text.

        Args:
            error_message: The error message
            error_type: The error type
            error_traceback: The error traceback
            suggestions: The suggestions

        Returns:
            The formatted error message
        """
        parts = [f"{error_type}: {error_message}"]

        # Add suggestions
        if suggestions:
            parts.append("\nSuggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                parts.append(f"{i}. {suggestion.suggestion}")
                if suggestion.documentation_link:
                    parts.append(f"   Documentation: {suggestion.documentation_link}")
                if suggestion.command_example:
                    parts.append(f"   Example: {suggestion.command_example}")

        return "\n".join(parts)


__all__ = ["EnhancedErrorHandler", "ErrorSuggestion"]


if TYPE_CHECKING:
    _handler = EnhancedErrorHandler()
    assert_type(_handler._find_suggestions("sample"), list[ErrorSuggestion])
