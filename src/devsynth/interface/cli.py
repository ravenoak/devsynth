"""CLI implementation of the UXBridge using Typer and Rich."""

from typing import Optional, Sequence, Dict, Any, Union

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.prompt import Confirm, Prompt
from rich.style import Style
from rich.theme import Theme
from rich.text import Text
from rich.markdown import Markdown

from devsynth.interface.ux_bridge import (
    UXBridge,
    ProgressIndicator,
    sanitize_output,
)
from devsynth.interface.output_formatter import OutputFormatter
from devsynth.security import validate_safe_input


# Define a custom theme for consistent styling
DEVSYNTH_THEME = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "heading": "bold blue",
    "subheading": "bold cyan",
    "prompt": "bold yellow",
    "command": "bold green",
    "path": "italic yellow",
    "code": "bold cyan on black",
    "highlight": "bold white on blue",
})


class CLIProgressIndicator(ProgressIndicator):
    """Enhanced Rich progress indicator with better visual feedback."""

    def __init__(self, console: Console, description: str, total: int) -> None:
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        )
        self._progress.start()

        # Handle description safely, converting to string if needed
        try:
            desc_str = str(description)
            desc = sanitize_output(desc_str)
        except Exception:
            # Fallback for objects that can't be safely converted to string
            desc = "<main task>"

        self._task = self._progress.add_task(desc, total=total)
        self._subtasks: Dict[str, Any] = {}

    def update(self, *, advance: float = 1, description: Optional[str] = None) -> None:
        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                desc = sanitize_output(desc_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                desc = "<description>"
        else:
            desc = None

        self._progress.update(self._task, advance=advance, description=desc)

    def complete(self) -> None:
        self._progress.update(self._task, completed=True)
        self._progress.stop()

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
            formatted_desc = f"  ↳ {desc}"
        except Exception:
            # Fallback for objects that can't be safely converted to string
            formatted_desc = "  ↳ <subtask>"

        task_id = self._progress.add_task(formatted_desc, total=total)
        self._subtasks[task_id] = description
        return task_id

    def update_subtask(self, task_id: str, advance: float = 1, description: Optional[str] = None) -> None:
        """Update a subtask's progress.

        Args:
            task_id: ID of the subtask to update
            advance: Amount to advance the progress
            description: New description for the subtask
        """
        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                desc = sanitize_output(desc_str)
                formatted_desc = f"  ↳ {desc}"
            except Exception:
                # Fallback for objects that can't be safely converted to string
                formatted_desc = "  ↳ <description>"
        else:
            formatted_desc = None

        self._progress.update(task_id, advance=advance, description=formatted_desc)

    def complete_subtask(self, task_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            task_id: ID of the subtask to complete
        """
        self._progress.update(task_id, completed=True)


class CLIUXBridge(UXBridge):
    """Bridge for command line interactions.

    This implementation uses Rich for formatted output and Typer-compatible
    prompts so that the same workflow logic can be reused by different
    frontends.
    """

    def __init__(self) -> None:
        self.console = Console(theme=DEVSYNTH_THEME)
        self.formatter = OutputFormatter(self.console)

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        styled_message = Text(message, style="prompt")
        answer = Prompt.ask(
            styled_message,
            choices=list(choices) if choices else None,
            default=default,
            show_default=show_default,
        )
        return validate_safe_input(str(answer))

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        styled_message = Text(message, style="prompt")
        return Confirm.ask(styled_message, default=default)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        """Display a formatted message to the user.

        This method uses the OutputFormatter to format and display the message
        with appropriate styling based on the message content and highlight flag.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
        """
        # Format and display the message using the OutputFormatter
        formatted = self.formatter.format_message(message, highlight=highlight)

        if isinstance(formatted, Panel):
            self.console.print(formatted, style="highlight" if highlight else None)
        elif isinstance(formatted, Text):
            self.console.print(formatted)
        elif isinstance(formatted, str) and "[" in formatted and "]" in formatted:
            # Handle Rich markup
            self.console.print(formatted, highlight=highlight)
        else:
            self.console.print(formatted)

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return CLIProgressIndicator(self.console, description, total)


__all__ = ["CLIUXBridge", "CLIProgressIndicator"]
