"""Enhanced progress indicators for the DevSynth CLI.

This module provides enhanced progress indicators for long-running operations
in the DevSynth CLI. It extends the basic progress indicator functionality
provided by the UXBridge abstraction with more detailed and visually appealing
progress indicators.
"""

from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from devsynth.interface.cli import CLIProgressIndicator
from devsynth.interface.progress_utils import run_with_progress
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge


class EnhancedProgressIndicator(CLIProgressIndicator):
    """Enhanced progress indicator with more detailed feedback.

    This class extends the basic CLIProgressIndicator with more detailed
    feedback, including estimated time remaining, task description, and
    subtasks.
    """

    def __init__(self, console: Console, description: str, total: int) -> None:
        """Initialize the enhanced progress indicator.

        Args:
            console: The Rich console to use for output
            description: The description of the task
            total: The total number of steps in the task
        """
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        self._progress.start()

        # Sanitize the description
        try:
            desc_str = str(description)
            desc = desc_str
        except Exception:
            # Fallback for objects that can't be safely converted to string
            desc = "<main task>"

        self._task = self._progress.add_task(desc, total=total)
        self._subtasks: Dict[str, str] = {}  # Maps subtask_id (description) to task_id

    def add_subtask(self, description: str, total: int = 100) -> str:
        """Add a subtask to the progress indicator.

        Args:
            description: The description of the subtask
            total: The total number of steps in the subtask

        Returns:
            The ID of the subtask (the description)
        """
        # Sanitize the description
        try:
            desc_str = str(description)
            desc = desc_str
        except Exception:
            # Fallback for objects that can't be safely converted to string
            desc = "<subtask>"

        formatted_desc = f"  ↳ {desc}"
        task_id = self._progress.add_task(formatted_desc, total=total)
        self._subtasks[desc] = task_id
        return desc

    def update_subtask(
        self, subtask_id: str, advance: float = 1, description: Optional[str] = None
    ) -> None:
        """Update a subtask's progress.

        Args:
            subtask_id: The ID of the subtask (the description)
            advance: The amount to advance the progress
            description: The new description of the subtask
        """
        if subtask_id in self._subtasks:
            task_id = self._subtasks[subtask_id]

            # If a new description is provided, update the subtask's description
            if description is not None:
                # Sanitize the description
                try:
                    desc_str = str(description)
                    desc = desc_str
                except Exception:
                    # Fallback for objects that can't be safely converted to string
                    desc = "<description>"

                formatted_desc = f"  ↳ {desc}"
                self._progress.update(
                    task_id, advance=advance, description=formatted_desc
                )

                # Update the subtask ID in the dictionary if the description has changed
                if desc != subtask_id:
                    self._subtasks[desc] = task_id
                    del self._subtasks[subtask_id]
            else:
                self._progress.update(task_id, advance=advance)

    def complete_subtask(self, subtask_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            subtask_id: The ID of the subtask (the description)
        """
        if subtask_id in self._subtasks:
            task_id = self._subtasks[subtask_id]
            self._progress.update(task_id, completed=True)

    def update(
        self,
        *,
        advance: float = 1,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update the progress indicator.

        Args:
            advance: The amount to advance the progress
            description: The new description of the task
            status: Status message to display
        """
        update_kwargs: Dict[str, Any] = {"advance": advance}

        if description is not None:
            try:
                desc_str = str(description)
                desc = desc_str
            except Exception:
                desc = "<description>"
            update_kwargs["description"] = desc

        if status is not None:
            update_kwargs["status"] = status

        self._progress.update(self._task, **update_kwargs)

    def complete(self) -> None:
        """Mark the task as complete."""
        # Complete all subtasks first
        for subtask_id, task_id in list(self._subtasks.items()):
            self._progress.update(task_id, completed=True)

        # Complete the main task
        self._progress.update(self._task, completed=True)
        self._progress.stop()


class ProgressManager:
    """Manager for creating and tracking progress indicators.

    This class provides a centralized way to create and track progress
    indicators for different tasks.
    """

    def __init__(self, bridge: UXBridge) -> None:
        """Initialize the progress manager.

        Args:
            bridge: The UXBridge to use for creating progress indicators
        """
        self.bridge = bridge
        self.indicators: Dict[str, ProgressIndicator] = {}

    def create_progress(
        self, task_id: str, description: str, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator for a task.

        Args:
            task_id: The ID of the task
            description: The description of the task
            total: The total number of steps in the task

        Returns:
            The progress indicator
        """
        indicator = self.bridge.create_progress(description, total=total)
        self.indicators[task_id] = indicator
        return indicator

    def get_progress(self, task_id: str) -> Optional[ProgressIndicator]:
        """Get the progress indicator for a task.

        Args:
            task_id: The ID of the task

        Returns:
            The progress indicator, or None if not found
        """
        return self.indicators.get(task_id)

    def update_progress(
        self, task_id: str, advance: float = 1, description: Optional[str] = None
    ) -> None:
        """Update the progress indicator for a task.

        Args:
            task_id: The ID of the task
            advance: The amount to advance the progress
            description: The new description of the task
        """
        indicator = self.get_progress(task_id)
        if indicator:
            indicator.update(advance=advance, description=description)

    def complete_progress(self, task_id: str) -> None:
        """Mark the progress indicator for a task as complete.

        Args:
            task_id: The ID of the task
        """
        indicator = self.get_progress(task_id)
        if indicator:
            indicator.complete()
            del self.indicators[task_id]


def create_enhanced_progress(
    console: Console, description: str, total: int = 100
) -> EnhancedProgressIndicator:
    """Create an enhanced progress indicator.

    Args:
        console: The Rich console to use for output
        description: The description of the task
        total: The total number of steps in the task

    Returns:
        The enhanced progress indicator
    """
    return EnhancedProgressIndicator(console, description, total)


def create_task_table(tasks: List[Dict[str, Any]], title: str = "Tasks") -> Table:
    """Create a table of tasks with their status.

    Args:
        tasks: The list of tasks
        title: The title of the table

    Returns:
        The table
    """
    table = Table(title=title)
    table.add_column("Task", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")

    for task in tasks:
        status = task.get("status", "Pending")
        status_style = (
            "green"
            if status == "Complete"
            else "yellow" if status == "In Progress" else "red"
        )
        table.add_row(
            task.get("name", ""),
            f"[{status_style}]{status}[/{status_style}]",
            task.get("description", ""),
        )

    return table
