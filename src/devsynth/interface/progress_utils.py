"""Progress indicator utilities.

This module provides utilities for creating and managing progress indicators
for long-running operations in a consistent way across all DevSynth commands.
"""

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge

# Type variable for generic functions
T = TypeVar("T")


class ProgressManager:
    """Manager for progress indicators.

    This class provides a simplified interface for creating and managing
    progress indicators for long-running operations.
    """

    def __init__(self, bridge: UXBridge):
        """Initialize the progress manager.

        Args:
            bridge: The UXBridge instance to use for creating progress indicators
        """
        self.bridge = bridge
        self.active_indicators: Dict[str, ProgressIndicator] = {}

    def create(
        self, description: str, total: int = 100, key: Optional[str] = None
    ) -> ProgressIndicator:
        """Create a progress indicator.

        Args:
            description: Description of the operation
            total: Total steps for the operation
            key: Optional key to identify the progress indicator

        Returns:
            The created progress indicator
        """
        indicator = self.bridge.create_progress(description, total=total)

        # Store the indicator if a key is provided
        if key:
            self.active_indicators[key] = indicator

        return indicator

    def get(self, key: str) -> Optional[ProgressIndicator]:
        """Get a progress indicator by key.

        Args:
            key: The key of the progress indicator

        Returns:
            The progress indicator, or None if not found
        """
        return self.active_indicators.get(key)

    def complete(self, key: str) -> None:
        """Complete a progress indicator by key.

        Args:
            key: The key of the progress indicator
        """
        indicator = self.active_indicators.get(key)
        if indicator:
            indicator.complete()
            del self.active_indicators[key]

    def complete_all(self) -> None:
        """Complete all active progress indicators."""
        for key in list(self.active_indicators.keys()):
            self.complete(key)

    @contextmanager
    def progress(
        self, description: str, total: int = 100, key: Optional[str] = None
    ) -> ProgressIndicator:
        """Context manager for progress indicators.

        Args:
            description: Description of the operation
            total: Total steps for the operation
            key: Optional key to identify the progress indicator

        Yields:
            The progress indicator
        """
        indicator = self.create(description, total, key)
        try:
            yield indicator
        finally:
            indicator.complete()
            if key and key in self.active_indicators:
                del self.active_indicators[key]

    def track(
        self, items: List[Any], description: str, key: Optional[str] = None
    ) -> List[Any]:
        """Track progress through a list of items.

        Args:
            items: The list of items to process
            description: Description of the operation
            key: Optional key to identify the progress indicator

        Returns:
            The original list of items
        """
        total = len(items)
        if total == 0:
            return items

        with self.progress(description, total, key) as indicator:
            # Return the original list, but with a side effect of updating the progress
            # indicator each time an item is accessed
            class TrackedList(list):
                def __getitem__(self, index):
                    if isinstance(index, slice):
                        # For slices, update progress based on slice size
                        start, stop, step = index.indices(len(self))
                        count = len(range(start, stop, step))
                        indicator.update(advance=count)
                    else:
                        # For single items, update progress by 1
                        indicator.update(advance=1)
                    return super().__getitem__(index)

            return TrackedList(items)

    def with_progress(
        self, description: str, total: int = 100, key: Optional[str] = None
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator for functions that should show progress.

        Args:
            description: Description of the operation
            total: Total steps for the operation
            key: Optional key to identify the progress indicator

        Returns:
            Decorator function
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                with self.progress(description, total, key) as indicator:
                    # Add the progress indicator to kwargs
                    kwargs["progress"] = indicator
                    return func(*args, **kwargs)

            return wrapper

        return decorator


class ProgressTracker:
    """Utility for tracking progress of iterative operations.

    This class provides a simple way to track progress of operations that
    process items in batches or with unknown total steps.
    """

    def __init__(
        self,
        indicator: ProgressIndicator,
        total: Optional[int] = None,
        update_interval: float = 0.1,
        auto_complete: bool = True,
    ):
        """Initialize the progress tracker.

        Args:
            indicator: The progress indicator to update
            total: Optional total number of items to process
            update_interval: Minimum time between updates in seconds
            auto_complete: Whether to automatically complete the indicator when done
        """
        self.indicator = indicator
        self.total = total
        self.update_interval = update_interval
        self.auto_complete = auto_complete
        self.count = 0
        self.last_update_time = time.time()
        self.start_time = time.time()
        self.estimated_total = total or 100

    def update(self, advance: int = 1, force: bool = False) -> None:
        """Update the progress.

        Args:
            advance: Number of items processed
            force: Whether to force an update regardless of the update interval
        """
        self.count += advance

        # Update the estimated total if no total was provided
        if self.total is None:
            # Estimate based on current progress and elapsed time
            elapsed = time.time() - self.start_time
            if elapsed > 0 and self.count > 0:
                # Estimate total based on current rate and a time estimate
                rate = self.count / elapsed
                estimated_time = max(
                    10.0, elapsed * 2
                )  # At least 10 seconds, or double current time
                self.estimated_total = max(100, int(rate * estimated_time))

        # Only update the indicator if enough time has passed or if forced
        current_time = time.time()
        if force or (current_time - self.last_update_time) >= self.update_interval:
            # Calculate percentage based on actual total or estimated total
            total = self.total or self.estimated_total
            percentage = min(100, int(self.count / total * 100))

            # Update the indicator
            self.indicator.update(
                advance=0,  # Don't advance, we'll set the percentage directly
                description=f"Processed {self.count} items",
                status=f"{percentage}% complete",
            )

            # Update the last update time
            self.last_update_time = current_time

    def complete(self) -> None:
        """Complete the progress tracking."""
        if self.auto_complete:
            self.indicator.complete()

    def __enter__(self) -> "ProgressTracker":
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        self.complete()


class StepProgress:
    """Simple helper for sequential step-based progress.

    This utility wraps a :class:`~devsynth.interface.ux_bridge.ProgressIndicator`
    and provides a lightweight API for updating it as a series of named steps
    are executed. Each call to :meth:`advance` marks the previous step complete
    and updates the description for the next step.
    """

    def __init__(
        self, bridge: UXBridge, steps: List[str], *, description: Optional[str] = None
    ) -> None:
        self._steps = steps
        self._index = 0
        self._indicator = bridge.create_progress(
            description or steps[0], total=len(steps)
        )

    def advance(self, status: Optional[str] = None) -> None:
        """Advance to the next step.

        Args:
            status: Optional status text to display alongside the step
                description.
        """

        if self._index >= len(self._steps):
            return

        desc = self._steps[self._index]
        advance = 0 if self._index == 0 else 1
        self._indicator.update(description=desc, status=status or desc, advance=advance)
        self._index += 1

    def complete(self) -> None:
        """Complete the progress indicator."""

        remaining = len(self._steps) - self._index
        if remaining > 0:
            self._indicator.update(advance=remaining)
        self._indicator.complete()

    def __enter__(self) -> "StepProgress":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - defensive
        self.complete()


def step_progress(
    bridge: UXBridge, steps: List[str], *, description: Optional[str] = None
) -> StepProgress:
    """Create a :class:`StepProgress` helper.

    Args:
        bridge: The UXBridge used to create the underlying progress indicator.
        steps: Ordered list of step descriptions.
        description: Optional overall description for the progress indicator.

    Returns:
        A :class:`StepProgress` instance.
    """

    return StepProgress(bridge, steps, description=description)


def create_progress_manager(bridge: UXBridge) -> ProgressManager:
    """Create a progress manager for the given bridge.

    Args:
        bridge: The UXBridge instance to use

    Returns:
        A ProgressManager instance
    """
    return ProgressManager(bridge)


@contextmanager
def progress_indicator(
    bridge: UXBridge, description: str, total: int = 100
) -> ProgressIndicator:
    """Context manager for creating a progress indicator.

    Args:
        bridge: The UXBridge instance to use
        description: Description of the operation
        total: Total steps for the operation

    Yields:
        The progress indicator
    """
    indicator = bridge.create_progress(description, total=total)
    try:
        yield indicator
    finally:
        indicator.complete()


def track_progress(bridge: UXBridge, items: List[Any], description: str) -> List[Any]:
    """Track progress through a list of items.

    Args:
        bridge: The UXBridge instance to use
        items: The list of items to process
        description: Description of the operation

    Returns:
        The original list of items
    """
    manager = ProgressManager(bridge)
    return manager.track(items, description)


def with_progress(
    bridge: UXBridge, description: str, total: int = 100
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for functions that should show progress.

    Args:
        bridge: The UXBridge instance to use
        description: Description of the operation
        total: Total steps for the operation

    Returns:
        Decorator function
    """
    manager = ProgressManager(bridge)
    return manager.with_progress(description, total)


def run_with_progress(
    task_name: str,
    task_fn: Callable[[], T],
    bridge: UXBridge,
    total: int = 100,
    subtasks: Optional[List[Dict[str, Any]]] = None,
) -> T:
    """Run a task while displaying a progress indicator.

    Args:
        task_name: Description of the task to display.
        task_fn: Function executing the task.
        bridge: UXBridge used to create progress indicators.
        total: Total number of steps for the task.
        subtasks: Optional list of subtasks with ``name`` and ``total`` keys.

    Returns:
        Result of ``task_fn``.
    """

    progress = bridge.create_progress(task_name, total=total)
    try:
        if subtasks:
            for subtask in subtasks:
                progress.add_subtask(
                    subtask.get("name", "Subtask"),
                    total=subtask.get("total", 100),
                )

        return task_fn()
    finally:
        progress.complete()
