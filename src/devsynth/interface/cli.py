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
from devsynth.logging_setup import DevSynthLogger
from devsynth.security import validate_safe_input

# Module level logger
logger = DevSynthLogger(__name__)


# Define a custom theme for consistent styling
DEVSYNTH_THEME = Theme({
    # Basic message types
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",

    # Headings and structure
    "heading": "bold blue",
    "subheading": "bold cyan",
    "section": "bold magenta",
    "subsection": "magenta",

    # Interactive elements
    "prompt": "bold yellow",
    "input": "bold white",
    "command": "bold green",
    "option": "italic green",
    "flag": "cyan",

    # Data and code
    "key": "bold cyan",
    "value": "white",
    "path": "italic yellow",
    "file": "italic cyan",
    "directory": "italic blue",
    "code": "bold cyan on black",
    "code_comment": "dim italic white",
    "code_keyword": "bold magenta",
    "code_string": "green",

    # Status indicators
    "progress": "bold blue",
    "complete": "bold green",
    "pending": "bold yellow",
    "failed": "bold red",

    # Documentation
    "doc_link": "underline cyan",
    "doc_section": "bold blue",
    "doc_example": "dim white",

    # Highlights and emphasis
    "highlight": "bold white on blue",
    "important": "bold red",
    "note": "italic cyan",
    "tip": "italic green",

    # Specific command outputs
    "metric_good": "green",
    "metric_warning": "yellow",
    "metric_bad": "red",
    "diff_added": "green",
    "diff_removed": "red",
    "diff_changed": "yellow",
})

# Define a colorblind-friendly theme
COLORBLIND_THEME = Theme({
    # Basic message types - using blue/orange/black contrast which works for most color vision deficiencies
    "info": "bright_blue",
    "success": "bright_blue",
    "warning": "#FF9900",  # Orange
    "error": "bold white on #FF9900",  # Bold white on orange

    # Headings and structure
    "heading": "bold bright_blue",
    "subheading": "bright_blue",
    "section": "bold white",
    "subsection": "white",

    # Interactive elements
    "prompt": "bold #FF9900",  # Bold orange
    "input": "bold white",
    "command": "bold bright_blue",
    "option": "italic bright_blue",
    "flag": "bright_blue",

    # Data and code
    "key": "bold bright_blue",
    "value": "white",
    "path": "italic #FF9900",  # Italic orange
    "file": "italic bright_blue",
    "directory": "italic white",
    "code": "bold bright_blue on black",
    "code_comment": "dim italic white",
    "code_keyword": "bold white",
    "code_string": "bright_blue",

    # Status indicators
    "progress": "bold bright_blue",
    "complete": "bold bright_blue",
    "pending": "bold #FF9900",  # Bold orange
    "failed": "bold white on #FF9900",  # Bold white on orange

    # Documentation
    "doc_link": "underline bright_blue",
    "doc_section": "bold bright_blue",
    "doc_example": "dim white",

    # Highlights and emphasis
    "highlight": "bold black on bright_blue",
    "important": "bold white on #FF9900",  # Bold white on orange
    "note": "italic bright_blue",
    "tip": "italic bright_blue",

    # Specific command outputs
    "metric_good": "bright_blue",
    "metric_warning": "#FF9900",  # Orange
    "metric_bad": "white on #FF9900",  # White on orange
    "diff_added": "bright_blue",
    "diff_removed": "#FF9900",  # Orange
    "diff_changed": "white",
})


class CLIProgressIndicator(ProgressIndicator):
    """Enhanced Rich progress indicator with better visual feedback."""

    def __init__(self, console: Console, description: str, total: int) -> None:
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[cyan]{task.fields[status]}[/cyan]"),
            TimeRemainingColumn(),
            console=console,
            expand=True,
        )
        self._progress.start()

        # Handle description safely, converting to string if needed
        try:
            desc_str = str(description)
            desc = sanitize_output(desc_str)
        except Exception:
            # Fallback for objects that can't be safely converted to string
            desc = "<main task>"

        self._task = self._progress.add_task(desc, total=total, status="Starting...")
        self._subtasks: Dict[str, Any] = {}
        self._nested_subtasks: Dict[str, Dict[str, Any]] = {}
        self._last_update_time = {}
        self._start_time = {}

    def update(self, *, advance: float = 1, description: Optional[str] = None, status: Optional[str] = None) -> None:
        """Update the progress indicator.

        Args:
            advance: Amount to advance the progress
            description: New description for the task
            status: Status message to display (e.g., "Processing...", "Analyzing...")
        """
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

        # Handle status safely
        if status is not None:
            try:
                status_str = str(status)
                status_msg = sanitize_output(status_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                status_msg = "In progress..."
        else:
            # If no status is provided, use a default based on progress
            task = self._progress.tasks[self._task]
            if task.completed:
                status_msg = "Complete"
            elif task.percentage >= 99:
                status_msg = "Finalizing..."
            elif task.percentage >= 75:
                status_msg = "Almost done..."
            elif task.percentage >= 50:
                status_msg = "Halfway there..."
            elif task.percentage >= 25:
                status_msg = "Processing..."
            else:
                status_msg = "Starting..."

        self._progress.update(self._task, advance=advance, description=desc, status=status_msg)

    def complete(self) -> None:
        """Mark the task as complete and stop the progress indicator."""
        # Complete all subtasks first
        for task_id in list(self._subtasks.keys()):
            self.complete_subtask(task_id)

        # Complete all nested subtasks
        for parent_id in list(self._nested_subtasks.keys()):
            for task_id in list(self._nested_subtasks[parent_id].keys()):
                self.complete_nested_subtask(parent_id, task_id)

        # Complete the main task
        self._progress.update(self._task, completed=True, status="Complete")
        self._progress.stop()

    def add_subtask(self, description: str, total: int = 100, status: str = "Starting...") -> str:
        """Add a subtask to the progress indicator.

        Args:
            description: Description of the subtask
            total: Total steps for the subtask
            status: Initial status message for the subtask

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

        task_id = self._progress.add_task(formatted_desc, total=total, status=status)
        self._subtasks[task_id] = description
        self._start_time[task_id] = self._progress.get_time()
        return task_id

    def update_subtask(self, task_id: str, advance: float = 1, description: Optional[str] = None, status: Optional[str] = None) -> None:
        """Update a subtask's progress.

        Args:
            task_id: ID of the subtask to update
            advance: Amount to advance the progress
            description: New description for the subtask
            status: Status message to display
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

        # Handle status safely
        if status is not None:
            try:
                status_str = str(status)
                status_msg = sanitize_output(status_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                status_msg = "In progress..."
        else:
            # If no status is provided, use a default based on progress
            if task_id in self._progress.task_ids:
                task = self._progress.tasks[task_id]
                if task.completed:
                    status_msg = "Complete"
                elif task.percentage >= 99:
                    status_msg = "Finalizing..."
                elif task.percentage >= 75:
                    status_msg = "Almost done..."
                elif task.percentage >= 50:
                    status_msg = "Halfway there..."
                elif task.percentage >= 25:
                    status_msg = "Processing..."
                else:
                    status_msg = "Starting..."
            else:
                status_msg = "In progress..."

        self._progress.update(task_id, advance=advance, description=formatted_desc, status=status_msg)
        self._last_update_time[task_id] = self._progress.get_time()

    def complete_subtask(self, task_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            task_id: ID of the subtask to complete
        """
        # Complete all nested subtasks first if any
        if task_id in self._nested_subtasks:
            for nested_id in list(self._nested_subtasks[task_id].keys()):
                self.complete_nested_subtask(task_id, nested_id)

        # Complete the subtask
        self._progress.update(task_id, completed=True, status="Complete")

        # Remove from tracking dictionaries
        if task_id in self._subtasks:
            del self._subtasks[task_id]
        if task_id in self._last_update_time:
            del self._last_update_time[task_id]
        if task_id in self._start_time:
            del self._start_time[task_id]
        if task_id in self._nested_subtasks:
            del self._nested_subtasks[task_id]

    def add_nested_subtask(self, parent_id: str, description: str, total: int = 100, status: str = "Starting...") -> str:
        """Add a nested subtask to a subtask.

        Args:
            parent_id: ID of the parent subtask
            description: Description of the nested subtask
            total: Total steps for the nested subtask
            status: Initial status message for the nested subtask

        Returns:
            task_id: ID of the created nested subtask
        """
        # Handle description safely, converting to string if needed
        try:
            desc_str = str(description)
            desc = sanitize_output(desc_str)
            formatted_desc = f"    ↳ {desc}"
        except Exception:
            # Fallback for objects that can't be safely converted to string
            formatted_desc = "    ↳ <nested subtask>"

        task_id = self._progress.add_task(formatted_desc, total=total, status=status)

        # Initialize nested subtasks dictionary for parent if it doesn't exist
        if parent_id not in self._nested_subtasks:
            self._nested_subtasks[parent_id] = {}

        self._nested_subtasks[parent_id][task_id] = description
        self._start_time[task_id] = self._progress.get_time()
        return task_id

    def update_nested_subtask(self, parent_id: str, task_id: str, advance: float = 1, description: Optional[str] = None, status: Optional[str] = None) -> None:
        """Update a nested subtask's progress.

        Args:
            parent_id: ID of the parent subtask
            task_id: ID of the nested subtask to update
            advance: Amount to advance the progress
            description: New description for the nested subtask
            status: Status message to display
        """
        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                desc = sanitize_output(desc_str)
                formatted_desc = f"    ↳ {desc}"
            except Exception:
                # Fallback for objects that can't be safely converted to string
                formatted_desc = "    ↳ <description>"
        else:
            formatted_desc = None

        # Handle status safely
        if status is not None:
            try:
                status_str = str(status)
                status_msg = sanitize_output(status_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                status_msg = "In progress..."
        else:
            # If no status is provided, use a default based on progress
            if task_id in self._progress.task_ids:
                task = self._progress.tasks[task_id]
                if task.completed:
                    status_msg = "Complete"
                elif task.percentage >= 99:
                    status_msg = "Finalizing..."
                elif task.percentage >= 75:
                    status_msg = "Almost done..."
                elif task.percentage >= 50:
                    status_msg = "Halfway there..."
                elif task.percentage >= 25:
                    status_msg = "Processing..."
                else:
                    status_msg = "Starting..."
            else:
                status_msg = "In progress..."

        self._progress.update(task_id, advance=advance, description=formatted_desc, status=status_msg)
        self._last_update_time[task_id] = self._progress.get_time()

    def complete_nested_subtask(self, parent_id: str, task_id: str) -> None:
        """Mark a nested subtask as complete.

        Args:
            parent_id: ID of the parent subtask
            task_id: ID of the nested subtask to complete
        """
        self._progress.update(task_id, completed=True, status="Complete")

        # Remove from tracking dictionaries
        if parent_id in self._nested_subtasks and task_id in self._nested_subtasks[parent_id]:
            del self._nested_subtasks[parent_id][task_id]
        if task_id in self._last_update_time:
            del self._last_update_time[task_id]
        if task_id in self._start_time:
            del self._start_time[task_id]


class CLIUXBridge(UXBridge):
    """Bridge for command line interactions.

    This implementation uses Rich for formatted output and Typer-compatible
    prompts so that the same workflow logic can be reused by different
    frontends.
    """

    def __init__(self, colorblind_mode: bool = False) -> None:
        """Initialize the CLI UX bridge.

        Args:
            colorblind_mode: Whether to use the colorblind-friendly theme
        """
        # Use the appropriate theme based on colorblind_mode
        theme = COLORBLIND_THEME if colorblind_mode else DEVSYNTH_THEME
        self.console = Console(theme=theme)
        self.formatter = OutputFormatter(self.console)
        self.colorblind_mode = colorblind_mode

    def set_colorblind_mode(self, enabled: bool = True) -> None:
        """Enable or disable colorblind-friendly mode.

        Args:
            enabled: Whether to enable colorblind-friendly mode
        """
        if self.colorblind_mode != enabled:
            self.colorblind_mode = enabled
            # Create a new console with the appropriate theme
            theme = COLORBLIND_THEME if enabled else DEVSYNTH_THEME
            self.console = Console(theme=theme)
            # Update the formatter with the new console
            self.formatter.set_console(self.console)

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        logger.debug(f"Asking question: {message}")
        styled_message = Text(message, style="prompt")
        answer = Prompt.ask(
            styled_message,
            choices=list(choices) if choices else None,
            default=default,
            show_default=show_default,
        )
        validated_answer = validate_safe_input(str(answer))
        logger.debug(f"User answered: {validated_answer}")
        return validated_answer

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        logger.debug(f"Asking for confirmation: {message}")
        styled_message = Text(message, style="prompt")
        answer = Confirm.ask(styled_message, default=default)
        logger.debug(f"User confirmed: {answer}")
        return answer

    def display_result(self, message: str, *, highlight: bool = False, message_type: str = None) -> None:
        """Display a formatted message to the user.

        This method uses the OutputFormatter to format and display the message
        with appropriate styling based on the message content, message type, and highlight flag.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
            message_type: Optional type of message (info, success, warning, error, etc.)
                          If not provided, it will be detected from the message content
        """
        # Log the message with appropriate level based on message_type
        if message_type == "error":
            logger.error(f"Displaying error: {message}")
        elif message_type == "warning":
            logger.warning(f"Displaying warning: {message}")
        elif message_type == "success":
            logger.info(f"Displaying success: {message}")
        else:
            logger.debug(f"Displaying message: {message}")
        # Detect message type if not provided
        if message_type is None:
            # Check for common patterns in the message
            if message.startswith(("Error:", "ERROR:", "Failed:", "FAILED:")):
                message_type = "error"
            elif message.startswith(("Warning:", "WARNING:")):
                message_type = "warning"
            elif message.startswith(("Success:", "SUCCESS:", "Completed:", "COMPLETED:")) or "successfully" in message.lower():
                message_type = "success"
            elif message.startswith(("Info:", "INFO:", "Note:", "NOTE:")):
                message_type = "info"
            elif message.startswith(("Tip:", "TIP:")):
                message_type = "tip"
            elif message.startswith(("Important:", "IMPORTANT:")):
                message_type = "important"
            elif message.startswith("#"):
                # Markdown-style heading
                heading_level = len(message.split()[0])
                if heading_level == 1:
                    message_type = "heading"
                elif heading_level == 2:
                    message_type = "subheading"
                elif heading_level == 3:
                    message_type = "section"
                else:
                    message_type = "subsection"
            elif message.startswith(">"):
                # Markdown-style blockquote
                message_type = "note"
            elif message.startswith("- [ ]") or message.startswith("* [ ]"):
                # Markdown-style task list (incomplete)
                message_type = "pending"
            elif message.startswith("- [x]") or message.startswith("* [x]"):
                # Markdown-style task list (complete)
                message_type = "complete"
            elif message.startswith(("- ", "* ")):
                # Markdown-style list
                message_type = "value"
            elif ": " in message and not message.startswith(" "):
                # Key-value pair
                message_type = "key"
            elif message.startswith(("$ ", "> ")):
                # Command example
                message_type = "command"
            elif message.startswith(("http://", "https://", "www.")):
                # URL
                message_type = "doc_link"
            elif message.startswith(("./", "../", "/")):
                # File path
                message_type = "path"
            else:
                # Default to normal text
                message_type = "normal"

        # Format and display the message using the OutputFormatter
        if highlight:
            # If highlight is requested, use the highlight style regardless of message type
            style = "highlight"
        elif message_type in self.console.theme.styles:
            # Use the style from the theme if available
            style = message_type
        else:
            # Default to no specific style
            style = None

        # Check if the message already contains Rich markup
        if isinstance(message, str) and "[" in message and "]" in message:
            # Handle Rich markup
            self.console.print(message)
        else:
            # Format the message based on its type
            formatted = self.formatter.format_message(message, message_type=message_type, highlight=highlight)

            if isinstance(formatted, Panel):
                self.console.print(formatted, style=style)
            elif isinstance(formatted, Text):
                self.console.print(formatted)
            else:
                self.console.print(formatted, style=style)

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        return CLIProgressIndicator(self.console, description, total)


__all__ = ["CLIUXBridge", "CLIProgressIndicator"]
