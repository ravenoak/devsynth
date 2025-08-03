"""Progress indicators for long-running operations.

This module provides enhanced progress indicators for long-running operations,
with features like time estimation, status updates, and subtask tracking.
"""

from typing import Dict, List, Optional, Any, Callable, Union
import time
from datetime import datetime, timedelta

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live

from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge
from devsynth.interface.cli import CLIProgressIndicator
from devsynth.application.cli.progress import EnhancedProgressIndicator
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class LongRunningProgressIndicator(EnhancedProgressIndicator):
    """Progress indicator for long-running operations.

    This class extends the EnhancedProgressIndicator with additional features
    for long-running operations, such as:
    - Estimated completion time
    - Operation history tracking
    - Periodic status updates
    - Adaptive refresh rate
    - Detailed subtask tracking
    - Checkpoint saving
    """

    def __init__(self, console: Console, description: str, total: int) -> None:
        """Initialize the long-running progress indicator.

        Args:
            console: The Rich console to use for output
            description: The description of the task
            total: The total number of steps in the task
        """
        # Create a progress bar with additional columns for long-running operations
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            TextColumn("[dim]{task.fields[status]}[/dim]"),
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

        # Add the main task with additional fields
        self._task = self._progress.add_task(
            desc, 
            total=total, 
            status="Starting...",
            start_time=time.time(),
            checkpoints=[],
            history=[],
        )
        
        # Store subtasks with their IDs
        self._subtasks: Dict[str, str] = {}  # Maps subtask_id (description) to task_id
        
        # Store the console for direct output if needed
        self._console = console
        
        # Track the last update time for adaptive refresh
        self._last_update_time = time.time()
        self._update_interval = 1.0  # Start with 1 second updates
        
        # Store the start time for ETA calculation
        self._start_time = time.time()
        
        logger.debug(f"Created LongRunningProgressIndicator for '{desc}'")

    def update(
        self, 
        *, 
        advance: float = 1, 
        description: Optional[str] = None, 
        status: Optional[str] = None
    ) -> None:
        """Update the progress indicator.

        Args:
            advance: The amount to advance the progress
            description: The new description of the task
            status: The new status of the task
        """
        current_time = time.time()
        
        # Update the task fields
        update_kwargs = {}
        
        if description is not None:
            # Sanitize the description
            try:
                desc_str = str(description)
                update_kwargs["description"] = desc_str
            except Exception:
                # Fallback for objects that can't be safely converted to string
                update_kwargs["description"] = "<description>"
        
        if status is not None:
            update_kwargs["status"] = status
            
            # Add to history if status changed
            task = self._progress.tasks[self._task]
            if task.fields.get("status") != status:
                history = list(task.fields.get("history", []))
                history.append({
                    "time": current_time,
                    "status": status,
                    "completed": task.completed
                })
                update_kwargs["history"] = history
        
        # Calculate adaptive refresh rate based on progress
        task = self._progress.tasks[self._task]
        if task.total > 0:
            progress_fraction = task.completed / task.total
            if progress_fraction < 0.1:
                # Early stages: update more frequently
                self._update_interval = 0.5
            elif progress_fraction > 0.9:
                # Late stages: update more frequently
                self._update_interval = 0.5
            else:
                # Middle stages: update less frequently
                self._update_interval = 2.0
        
        # Only update if enough time has passed or if this is a significant update
        if (current_time - self._last_update_time >= self._update_interval or 
            description is not None or 
            status is not None or 
            advance >= 5):
            
            # Update the progress
            self._progress.update(self._task, advance=advance, **update_kwargs)
            
            # Calculate and display ETA if we have enough progress
            task = self._progress.tasks[self._task]
            if task.total > 0 and task.completed > 0:
                elapsed = current_time - self._start_time
                progress_fraction = task.completed / task.total
                if progress_fraction > 0.05:  # Only show ETA after 5% progress
                    estimated_total_time = elapsed / progress_fraction
                    eta = self._start_time + estimated_total_time
                    eta_datetime = datetime.fromtimestamp(eta)
                    
                    # Add checkpoint if significant progress has been made
                    checkpoints = list(task.fields.get("checkpoints", []))
                    if not checkpoints or (progress_fraction - checkpoints[-1]["progress"] >= 0.1):
                        checkpoints.append({
                            "time": current_time,
                            "progress": progress_fraction,
                            "eta": eta
                        })
                        self._progress.update(self._task, checkpoints=checkpoints)
            
            self._last_update_time = current_time

    def add_subtask(
        self, 
        description: str, 
        total: int = 100, 
        status: str = "Starting..."
    ) -> str:
        """Add a subtask to the progress indicator.

        Args:
            description: The description of the subtask
            total: The total number of steps in the subtask
            status: The initial status of the subtask

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
        task_id = self._progress.add_task(
            formatted_desc, 
            total=total, 
            status=status,
            start_time=time.time(),
            parent=self._task
        )
        self._subtasks[desc] = task_id
        
        logger.debug(f"Added subtask '{desc}' to LongRunningProgressIndicator")
        return desc

    def update_subtask(
        self, 
        subtask_id: str, 
        advance: float = 1, 
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> None:
        """Update a subtask's progress.

        Args:
            subtask_id: The ID of the subtask (the description)
            advance: The amount to advance the progress
            description: The new description of the subtask
            status: The new status of the subtask
        """
        if subtask_id in self._subtasks:
            task_id = self._subtasks[subtask_id]
            
            # Prepare update kwargs
            update_kwargs = {}
            
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
                update_kwargs["description"] = formatted_desc

                # Update the subtask ID in the dictionary if the description has changed
                if desc != subtask_id:
                    self._subtasks[desc] = task_id
                    del self._subtasks[subtask_id]
            
            # If a new status is provided, update the subtask's status
            if status is not None:
                update_kwargs["status"] = status
            
            # Update the subtask
            self._progress.update(task_id, advance=advance, **update_kwargs)
            
            # Also advance the main task proportionally
            main_task = self._progress.tasks[self._task]
            subtask = self._progress.tasks[task_id]
            
            if subtask.total > 0:
                # Calculate the proportion of the subtask that was completed
                proportion = advance / subtask.total
                
                # Calculate the equivalent advance for the main task
                main_advance = proportion * main_task.total / len(self._subtasks)
                
                # Update the main task
                self.update(advance=main_advance)

    def complete_subtask(self, subtask_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            subtask_id: The ID of the subtask (the description)
        """
        if subtask_id in self._subtasks:
            task_id = self._subtasks[subtask_id]
            
            # Get the current progress
            subtask = self._progress.tasks[task_id]
            remaining = subtask.total - subtask.completed
            
            # Complete the subtask
            self._progress.update(task_id, completed=subtask.total, status="Complete")
            
            # Also advance the main task proportionally
            if remaining > 0:
                main_task = self._progress.tasks[self._task]
                
                # Calculate the equivalent advance for the main task
                main_advance = remaining * main_task.total / (len(self._subtasks) * subtask.total)
                
                # Update the main task
                self.update(advance=main_advance)

    def complete(self) -> None:
        """Mark the task as complete."""
        # Complete all subtasks first
        for subtask_id, task_id in list(self._subtasks.items()):
            subtask = self._progress.tasks[task_id]
            self._progress.update(task_id, completed=subtask.total, status="Complete")

        # Complete the main task
        self._progress.update(self._task, completed=100, status="Complete")
        
        # Calculate and display final statistics
        task = self._progress.tasks[self._task]
        elapsed = time.time() - self._start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        
        # Display completion message
        self._console.print(f"[bold green]Task completed in {elapsed_str}[/bold green]")
        
        # Stop the progress display
        self._progress.stop()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the progress.

        Returns:
            A dictionary with summary information
        """
        task = self._progress.tasks[self._task]
        elapsed = time.time() - self._start_time
        
        summary = {
            "description": task.description,
            "progress": task.completed / task.total if task.total > 0 else 0,
            "elapsed": elapsed,
            "elapsed_str": str(timedelta(seconds=int(elapsed))),
            "subtasks": len(self._subtasks),
            "history": task.fields.get("history", []),
            "checkpoints": task.fields.get("checkpoints", []),
        }
        
        # Calculate ETA if we have enough progress
        if task.total > 0 and task.completed > 0:
            progress_fraction = task.completed / task.total
            if progress_fraction > 0.05:  # Only show ETA after 5% progress
                estimated_total_time = elapsed / progress_fraction
                eta = self._start_time + estimated_total_time
                eta_datetime = datetime.fromtimestamp(eta)
                
                summary["eta"] = eta
                summary["eta_str"] = eta_datetime.strftime("%Y-%m-%d %H:%M:%S")
                summary["remaining"] = estimated_total_time - elapsed
                summary["remaining_str"] = str(timedelta(seconds=int(estimated_total_time - elapsed)))
        
        return summary


def create_long_running_progress(
    console: Console, 
    description: str, 
    total: int = 100
) -> LongRunningProgressIndicator:
    """Create a long-running progress indicator.

    Args:
        console: The Rich console to use for output
        description: The description of the task
        total: The total number of steps in the task

    Returns:
        The long-running progress indicator
    """
    return LongRunningProgressIndicator(console, description, total)


def run_with_long_running_progress(
    task_name: str,
    task_fn: Callable[..., Any],
    bridge: UXBridge,
    total: int = 100,
    subtasks: Optional[List[Dict[str, Any]]] = None,
    **task_kwargs: Any
) -> Any:
    """Run a task with a long-running progress indicator.

    Args:
        task_name: The name of the task
        task_fn: The function to run
        bridge: The UXBridge to use for creating progress indicators
        total: The total number of steps in the task
        subtasks: Optional list of subtasks with their descriptions and totals
        **task_kwargs: Additional keyword arguments to pass to the task function

    Returns:
        The result of the task function
    """
    # Create a progress indicator for the task
    progress = create_long_running_progress(bridge.console, task_name, total)

    try:
        # Add subtasks if provided
        if subtasks:
            for subtask in subtasks:
                progress.add_subtask(
                    subtask.get("name", "Subtask"),
                    total=subtask.get("total", 100),
                    status=subtask.get("status", "Starting...")
                )

        # Define a callback for the task to update progress
        def update_progress(
            advance: float = 1, 
            description: Optional[str] = None, 
            status: Optional[str] = None,
            subtask: Optional[str] = None
        ) -> None:
            if subtask:
                progress.update_subtask(subtask, advance, description, status)
            else:
                progress.update(advance=advance, description=description, status=status)

        # Add the callback to the task kwargs
        task_kwargs["progress_callback"] = update_progress

        # Run the task function
        result = task_fn(**task_kwargs)

        return result
    finally:
        # Mark the task as complete, even if an exception occurs
        progress.complete()