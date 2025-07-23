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
        message_type: Optional[str] = None,
    ) -> str:
        """Format and sanitize a message for output."""
        formatted = self.formatter.format_message(
            message, message_type=message_type, highlight=highlight
        )
        return sanitize_output(str(formatted))
