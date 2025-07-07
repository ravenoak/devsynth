from __future__ import annotations

from typing import List, Optional, Sequence, Dict, Any

from .ux_bridge import UXBridge, ProgressIndicator, sanitize_output
from .output_formatter import OutputFormatter


class WebUIProgressIndicator(ProgressIndicator):
    """Enhanced progress indicator for WebUI with better visual feedback."""

    def __init__(self, description: str, total: int) -> None:
        self._description = description
        self._total = total
        self._current = 0
        self._subtasks: Dict[str, Dict[str, Any]] = {}
        self._update_times = []

    def update(self, *, advance: float = 1, description: Optional[str] = None) -> None:
        """Update the progress indicator.

        Args:
            advance: Amount to advance the progress
            description: New description for the progress indicator
        """
        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                self._description = sanitize_output(desc_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                pass

        self._current += advance
        self._update_times.append((0, self._current))  # Use 0 as a placeholder for time

    def complete(self) -> None:
        """Mark the progress indicator as complete."""
        self._current = self._total

    def add_subtask(self, description: str, total: int = 100) -> str:
        """Add a subtask to the progress indicator.

        Args:
            description: Description of the subtask
            total: Total steps for the subtask

        Returns:
            task_id: ID of the created subtask
        """
        # Handle description safely, converting to string if needed
        try:
            desc_str = str(description)
            desc = sanitize_output(desc_str)
        except Exception:
            # Fallback for objects that can't be safely converted to string
            desc = "<subtask>"

        task_id = f"subtask_{len(self._subtasks)}"
        self._subtasks[task_id] = {
            "description": desc,
            "total": total,
            "current": 0,
            "completed": False
        }
        return task_id

    def update_subtask(self, task_id: str, advance: float = 1, description: Optional[str] = None) -> None:
        """Update a subtask's progress.

        Args:
            task_id: ID of the subtask to update
            advance: Amount to advance the progress
            description: New description for the subtask
        """
        if task_id not in self._subtasks:
            return

        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                self._subtasks[task_id]["description"] = sanitize_output(desc_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                pass

        self._subtasks[task_id]["current"] += advance

    def complete_subtask(self, task_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            task_id: ID of the subtask to complete
        """
        if task_id not in self._subtasks:
            return

        self._subtasks[task_id]["current"] = self._subtasks[task_id]["total"]
        self._subtasks[task_id]["completed"] = True


class WebUIBridge(UXBridge):
    """Bridge for WebUI interactions implementing the :class:`UXBridge` API.

    This implementation provides a consistent interface with CLIUXBridge
    to ensure parity between CLI and WebUI interfaces.
    """

    def __init__(self) -> None:
        self.messages: List[str] = []
        self.formatter = OutputFormatter()

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Ask a question and return the response.

        In this lightweight implementation, it returns the default value.
        In a full implementation, it would display a form element.

        Args:
            message: The question to ask
            choices: Optional list of choices
            default: Default value
            show_default: Whether to show the default value

        Returns:
            The user's response (or default in this implementation)
        """
        return str(default or "")

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        """Request confirmation from the user.

        In this lightweight implementation, it returns the default value.
        In a full implementation, it would display a checkbox or buttons.

        Args:
            message: The confirmation message
            default: Default value

        Returns:
            The user's choice (or default in this implementation)
        """
        return default

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        """Display a message to the user.

        This implementation formats the message using the OutputFormatter
        for consistency with CLIUXBridge.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
        """
        formatted = self.formatter.format_message(message, highlight=highlight)
        sanitized = sanitize_output(str(formatted))
        self.messages.append(sanitized)

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator for long running tasks.

        Args:
            description: Description of the task
            total: Total steps for the task

        Returns:
            A progress indicator
        """
        return WebUIProgressIndicator(description, total)


__all__ = ["WebUIBridge", "WebUIProgressIndicator"]
