"""Progress indicators for long-running operations.

This module provides enhanced progress indicators for long-running operations,
with features like time estimation, status updates, and subtask tracking.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from contextlib import ExitStack
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, TypeVar, cast

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from devsynth.application.cli.models import (
    ProgressCheckpoint,
    ProgressHistoryEntry,
    ProgressSnapshot,
    ProgressSubtaskLike,
    ProgressSubtaskSpec,
    ProgressUpdate,
    SubtaskState,
    coerce_subtask_spec,
)
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge
from devsynth.logging_setup import DevSynthLogger

# ``_ProgressIndicatorBase`` must be available before defining classes that inherit
# from it so ``from module import _ProgressIndicatorBase`` succeeds even when
# other modules import this file during runtime initialisation (e.g. deterministic
# progress tests that reload the module). Declare the protocol first so type
# checkers know the intended interface, then provide a `TypeAlias` for static
# analysis while the runtime alias continues to reference the concrete
# implementation.


class _ProgressIndicatorProtocol(Protocol):
    def update(
        self,
        *,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None: ...

    def complete(self) -> None: ...

    def add_subtask(
        self, description: str, total: int = 100, status: str = "Starting..."
    ) -> str: ...

    def update_subtask(
        self,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None: ...

    def complete_subtask(self, task_id: str) -> None: ...


# Define _ProgressIndicatorBase as a type alias that resolves to ProgressIndicator at runtime
# This ensures it's always available for imports and type checking
if TYPE_CHECKING:
    _ProgressIndicatorBase: TypeAlias = _ProgressIndicatorProtocol
else:
    _ProgressIndicatorBase = ProgressIndicator


__all__ = [
    "LongRunningProgressIndicator",
    "_ProgressIndicatorBase",
    "_ProgressIndicatorProtocol",
]


logger = DevSynthLogger(__name__)

T = TypeVar("T")


def _as_float(value: Any) -> float | None:
    """Safely coerce ``value`` to ``float`` when possible."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _console_for_bridge(bridge: UXBridge) -> Console:
    """Return a console from ``bridge`` when available."""

    console = getattr(bridge, "console", None)
    if isinstance(console, Console):
        return console
    if console is not None and hasattr(console, "print"):
        return cast(Console, console)
    return Console()


class LongRunningProgressIndicator(_ProgressIndicatorBase):
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

        self._history: list[ProgressHistoryEntry] = []
        self._checkpoints: list[ProgressCheckpoint] = []

        # Add the main task with additional fields
        self._task = self._progress.add_task(
            desc,
            total=total,
            status="Starting...",
            start_time=time.time(),
            checkpoints=tuple(self._checkpoints),
            history=tuple(self._history),
        )

        # Store subtasks with their IDs
        self._subtasks: dict[str, SubtaskState] = {}

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
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update the progress indicator.

        Args:
            advance: The amount to advance the progress
            description: The new description of the task
            status: The new status of the task
        """
        current_time = time.time()

        # Update the task fields
        update_kwargs: dict[str, object] = {}

        if description is not None:
            # Sanitize the description
            try:
                desc_str = str(description)
                update_kwargs["description"] = desc_str
            except Exception:
                # Fallback for objects that can't be safely converted to string
                update_kwargs["description"] = "<description>"

        task = self._progress.tasks[self._task]

        if status is not None:
            update_kwargs["status"] = status

            if task.fields.get("status") != status:
                entry = ProgressHistoryEntry(
                    time=current_time, status=status, completed=task.completed
                )
                self._history.append(entry)
                update_kwargs["history"] = tuple(self._history)

        # Calculate adaptive refresh rate based on progress
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
        if (
            current_time - self._last_update_time >= self._update_interval
            or description is not None
            or status is not None
            or advance >= 5
        ):

            # Update the progress
            self._progress.update(self._task, advance=advance, **update_kwargs)

            task = self._progress.tasks[self._task]
            if task.total > 0 and task.completed > 0:
                elapsed = current_time - self._start_time
                progress_fraction = task.completed / task.total
                if progress_fraction > 0.05:  # Only show ETA after 5% progress
                    estimated_total_time = elapsed / progress_fraction
                    eta = self._start_time + estimated_total_time
                    eta_datetime = datetime.fromtimestamp(eta)

                    if not self._checkpoints or (
                        progress_fraction - self._checkpoints[-1].progress >= 0.1
                    ):
                        checkpoint = ProgressCheckpoint(
                            time=current_time,
                            progress=progress_fraction,
                            eta=eta,
                        )
                        self._checkpoints.append(checkpoint)
                        self._progress.update(
                            self._task, checkpoints=tuple(self._checkpoints)
                        )

            self._last_update_time = current_time

    def add_subtask(
        self, description: str, total: int = 100, status: str = "Starting..."
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
            parent=self._task,
        )
        self._subtasks[desc] = SubtaskState(task_id=task_id, total=float(total))

        logger.debug(f"Added subtask '{desc}' to LongRunningProgressIndicator")
        return desc

    def update_subtask(
        self,
        subtask_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update a subtask's progress.

        Args:
            subtask_id: The ID of the subtask (the description)
            advance: The amount to advance the progress
            description: The new description of the subtask
            status: The new status of the subtask
        """
        if subtask_id in self._subtasks:
            state = self._subtasks[subtask_id]
            task_id = state.task_id

            # Prepare update kwargs
            update_kwargs: dict[str, object] = {}

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
                    self._subtasks[desc] = state
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
                main_advance = (
                    proportion * main_task.total / max(len(self._subtasks), 1)
                )

                # Update the main task
                self.update(advance=main_advance)

    def complete_subtask(self, subtask_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            subtask_id: The ID of the subtask (the description)
        """
        if subtask_id in self._subtasks:
            state = self._subtasks[subtask_id]
            task_id = state.task_id

            # Get the current progress
            subtask = self._progress.tasks[task_id]
            remaining = subtask.total - subtask.completed

            # Complete the subtask
            self._progress.update(task_id, completed=subtask.total, status="Complete")

            # Also advance the main task proportionally
            if remaining > 0:
                main_task = self._progress.tasks[self._task]

                # Calculate the equivalent advance for the main task
                main_advance = (
                    remaining
                    * main_task.total
                    / (max(len(self._subtasks), 1) * max(subtask.total, 1))
                )

                # Update the main task
                self.update(advance=main_advance)

    def complete(self) -> None:
        """Mark the task as complete."""
        # Complete all subtasks first
        for _, state in list(self._subtasks.items()):
            subtask = self._progress.tasks[state.task_id]
            self._progress.update(
                state.task_id, completed=subtask.total, status="Complete"
            )

        # Complete the main task
        main_task = self._progress.tasks[self._task]
        final_total = float(main_task.total)
        if final_total < 100.0:
            final_total = 100.0
        self._progress.update(
            self._task,
            completed=final_total,
            total=final_total,
            status="Complete",
        )
        try:
            main_task.total = final_total
        except AttributeError:
            pass

        # Calculate and display final statistics
        task = self._progress.tasks[self._task]
        elapsed = time.time() - self._start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        # Display completion message
        self._console.print(f"[bold green]Task completed in {elapsed_str}[/bold green]")

        # Stop the progress display
        self._progress.stop()

    def get_summary(self) -> ProgressSnapshot:
        """Get a summary of the progress."""

        task = self._progress.tasks[self._task]
        elapsed = time.time() - self._start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        progress = task.completed / task.total if task.total > 0 else 0.0

        eta: float | None = None
        eta_str: str | None = None
        remaining: float | None = None
        remaining_str: str | None = None

        if task.total > 0 and task.completed > 0:
            progress_fraction = task.completed / task.total
            if progress_fraction > 0.05:
                estimated_total_time = elapsed / progress_fraction
                eta = self._start_time + estimated_total_time
                eta_str = datetime.fromtimestamp(eta).strftime("%Y-%m-%d %H:%M:%S")
                remaining = estimated_total_time - elapsed
                remaining_str = str(timedelta(seconds=int(remaining)))

        return ProgressSnapshot(
            description=task.description,
            progress=progress,
            elapsed=elapsed,
            elapsed_str=elapsed_str,
            subtasks=len(self._subtasks),
            history=tuple(self._history),
            checkpoints=tuple(self._checkpoints),
            eta=eta,
            eta_str=eta_str,
            remaining=remaining,
            remaining_str=remaining_str,
        )


def simulate_progress_timeline(
    events: Sequence[Mapping[str, object]],
    *,
    description: str = "Deterministic progress run",
    total: int = 100,
    console: Console | None = None,
    clock: Callable[[], float] | None = None,
    progress_factory: Callable[..., Progress] | None = None,
) -> dict[str, object]:
    """Drive :class:`LongRunningProgressIndicator` with deterministic events.

    The simulation mirrors CLI behaviour without requiring a Rich console by
    allowing callers to inject a fake clock, console, or ``Progress`` factory.
    ``events`` is a sequence of dictionaries with an ``action`` key describing
    each operation:

    ``update``
        Advance the main task. Optional keys: ``advance`` (float), ``status``,
        ``description``.
    ``add_subtask``
        Create a subtask. Optional keys: ``total`` (int), ``status``; ``alias``
        stores a human-friendly name used by later events.
    ``update_subtask``
        Update a subtask referenced by ``alias`` or ``subtask``.
    ``complete_subtask``
        Mark a subtask as complete.
    ``tick``
        Consume additional clock ticks without updating progress. Useful for
        spacing ETA checkpoints.
    ``complete``
        Complete all tasks and stop the progress display.

    Returns a dictionary containing the emitted transcript, latest summary, and
    sanitized subtask snapshots for deterministic assertions.
    """

    transcript: list[tuple[str, Mapping[str, object]]] = []
    console_obj = console or Console()

    with ExitStack() as stack:
        if clock is not None:
            original_time = time.time

            def _restore_time() -> None:
                time.time = original_time

            stack.callback(_restore_time)
            time.time = clock

        if progress_factory is not None:
            original_progress = globals()["Progress"]

            def _restore_progress() -> None:
                globals()["Progress"] = original_progress

            stack.callback(_restore_progress)
            globals()["Progress"] = progress_factory

        indicator = LongRunningProgressIndicator(console_obj, description, total)
        progress: Progress = indicator._progress
        alias_to_subtask: dict[str, str] = {}

        for event in events:
            action = str(event.get("action", "")).lower()

            if action == "tick":
                ticks = int(_as_float(event.get("times", 1)) or 1)
                for _ in range(max(0, ticks)):
                    if clock is not None:
                        clock()
                    else:
                        time.time()
                transcript.append(("tick", {"times": ticks}))
                continue

            if action == "add_subtask":
                subtask_desc = event.get("description", "<subtask>")
                try:
                    description_text = str(subtask_desc)
                except Exception:
                    description_text = "<subtask>"
                alias_raw = event.get("alias", "")
                alias = str(alias_raw) or description_text
                subtask_total = int(_as_float(event.get("total", 100)) or 100)
                status_obj = event.get("status")
                status_text = (
                    status_obj if isinstance(status_obj, str) else "Starting..."
                )
                created = indicator.add_subtask(
                    description_text,
                    total=subtask_total,
                    status=status_text,
                )
                alias_to_subtask[alias] = created
                subtask_task = progress.tasks[indicator._subtasks[created].task_id]
                transcript.append(
                    (
                        "add_subtask",
                        {
                            "alias": alias,
                            "task_id": created,
                            "description": subtask_task.description,
                            "status": subtask_task.fields.get("status", ""),
                            "total": subtask_task.total,
                        },
                    )
                )
                continue

            if action == "update_subtask":
                key = event.get("alias") or event.get("subtask")
                if not isinstance(key, str):
                    continue
                lookup = alias_to_subtask.get(key, key)
                advance = _as_float(event.get("advance", 1)) or 1.0
                description_obj = event.get("description")
                status_obj = event.get("status")
                description_update_text = (
                    str(description_obj) if isinstance(description_obj, str) else None
                )
                status_update_text = (
                    str(status_obj) if isinstance(status_obj, str) else None
                )
                indicator.update_subtask(
                    lookup,
                    advance=advance,
                    description=description_update_text,
                    status=status_update_text,
                )
                state = indicator._subtasks.get(lookup)
                if state is None and description_update_text is not None:
                    state = indicator._subtasks.get(description_update_text)
                if (
                    description_update_text is not None
                    and description_update_text in indicator._subtasks
                ):
                    alias_to_subtask[key] = description_update_text
                if state is not None:
                    task = progress.tasks[state.task_id]
                    transcript.append(
                        (
                            "update_subtask",
                            {
                                "alias": key,
                                "description": task.description,
                                "completed": task.completed,
                                "status": task.fields.get("status", ""),
                            },
                        )
                    )
                continue

            if action == "complete_subtask":
                key = event.get("alias") or event.get("subtask")
                if not isinstance(key, str):
                    continue
                lookup = alias_to_subtask.get(key, key)
                indicator.complete_subtask(lookup)
                state = indicator._subtasks.get(lookup)
                if state is not None:
                    task = progress.tasks[state.task_id]
                    transcript.append(
                        (
                            "complete_subtask",
                            {
                                "alias": key,
                                "completed": task.completed,
                                "status": task.fields.get("status", ""),
                            },
                        )
                    )
                continue

            if action == "update":
                advance = _as_float(event.get("advance", 1)) or 1.0
                description_value = event.get("description")
                status_value = event.get("status")
                indicator.update(
                    advance=advance,
                    description=(
                        str(description_value)
                        if isinstance(description_value, str)
                        else None
                    ),
                    status=str(status_value) if isinstance(status_value, str) else None,
                )
                main_task = progress.tasks[indicator._task]
                transcript.append(
                    (
                        "update",
                        {
                            "completed": main_task.completed,
                            "status": main_task.fields.get("status", ""),
                            "description": main_task.description,
                        },
                    )
                )
                continue

            if action == "complete":
                indicator.complete()
                main_task = progress.tasks[indicator._task]
                transcript.append(
                    (
                        "complete",
                        {
                            "completed": main_task.completed,
                            "status": main_task.fields.get("status", ""),
                        },
                    )
                )

        summary = indicator.get_summary()
        subtasks_snapshot: dict[str, object] = {}
        for alias, state in indicator._subtasks.items():
            task = progress.tasks[state.task_id]
            subtasks_snapshot[alias] = {
                "description": task.description,
                "total": task.total,
                "completed": task.completed,
                "status": task.fields.get("status", ""),
            }

        console_messages = tuple(getattr(console_obj, "messages", ()))

    return {
        "transcript": tuple(transcript),
        "summary": summary,
        "history": tuple(indicator._history),
        "checkpoints": tuple(indicator._checkpoints),
        "subtasks": subtasks_snapshot,
        "console_messages": console_messages,
    }


def create_long_running_progress(
    console: Console, description: str, total: int = 100
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
    task_fn: Callable[..., T],
    bridge: UXBridge,
    total: int = 100,
    subtasks: Sequence[ProgressSubtaskLike] | None = None,
    **task_kwargs: object,
) -> T:
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
    progress = create_long_running_progress(
        _console_for_bridge(bridge), task_name, total
    )

    try:
        # Add subtasks if provided
        if subtasks:
            for subtask in subtasks:
                spec = coerce_subtask_spec(subtask)
                progress.add_subtask(
                    spec.name,
                    total=spec.total,
                    status=spec.status,
                )

        # Define a callback for the task to update progress
        def update_progress(
            advance: float = 1,
            description: str | None = None,
            status: str | None = None,
            subtask: str | None = None,
        ) -> None:
            if subtask:
                progress.update_subtask(subtask, advance, description, status)
            else:
                progress.update(advance=advance, description=description, status=status)

        # Add the callback to the task kwargs
        task_kwargs["progress_callback"] = cast(ProgressUpdate, update_progress)

        # Run the task function
        return task_fn(**task_kwargs)
    finally:
        # Mark the task as complete, even if an exception occurs
        progress.complete()
