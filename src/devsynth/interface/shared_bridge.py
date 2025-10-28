from __future__ import annotations

"""Shared utilities for UXBridge implementations."""

from typing import Optional

from .output_formatter import OutputFormatter
from .ux_bridge import sanitize_output


class SharedBridgeMixin:
    """Mixin providing common display logic for bridges."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[misc]
        self.formatter = OutputFormatter(getattr(self, "console", None))

    def _format_for_output(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ):
        """Format and sanitize a message for output.

        Returns:
            A formatted message, which could be a string, Panel, Text, or other Rich object.
        """
        formatted = self.formatter.format_message(
            message, message_type=message_type, highlight=highlight
        )

        # If the formatted message is already a Rich object (Panel, Text, etc.),
        # return it as is to preserve its type for proper rendering
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.text import Text

        if isinstance(formatted, (Panel, Text, Markdown)):
            return formatted

        # Otherwise, sanitize the string representation
        return sanitize_output(str(formatted))
