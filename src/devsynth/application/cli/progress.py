"""Lightweight progress utilities for CLI commands.

This module provides a minimal ``ProgressManager`` that tracks active
progress indicators created via the :class:`~devsynth.interface.ux_bridge.UXBridge`.
It replaces the earlier enhanced progress system with a simpler
implementation focused on clarity rather than rich visuals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol

from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge


class SupportsProgress(Protocol):
    """Bridge protocol documenting the progress methods required."""

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create and return a :class:`~devsynth.interface.ux_bridge.ProgressIndicator`."""


@dataclass(slots=True)
class ManagedProgress:
    """Record keeping structure for progress tasks managed by :class:`ProgressManager`."""

    indicator: ProgressIndicator


class ProgressManager:
    """Create and manage progress indicators for CLI tasks."""

    def __init__(self, bridge: SupportsProgress | UXBridge) -> None:
        self.bridge: SupportsProgress = bridge
        self.indicators: dict[str, ManagedProgress] = {}

    def create_progress(
        self, task_id: str, description: str, total: int = 100
    ) -> ProgressIndicator:
        """Create and store a progress indicator for ``task_id``."""
        indicator = self.bridge.create_progress(description, total=total)
        self.indicators[task_id] = ManagedProgress(indicator=indicator)
        return indicator

    def get_progress(self, task_id: str) -> ProgressIndicator | None:
        """Return the indicator for ``task_id`` if it exists."""
        managed = self.indicators.get(task_id)
        return managed.indicator if managed else None

    def update_progress(
        self,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update the indicator associated with ``task_id``.

        Args:
            task_id: Identifier of the progress task to update.
            advance: Amount to advance the indicator.
            description: Optional new description for the task.
            status: Optional short status message.
        """
        managed = self.indicators.get(task_id)
        if managed is not None:
            managed.indicator.update(
                advance=advance, description=description, status=status
            )

    def complete_progress(self, task_id: str) -> None:
        """Complete and remove the indicator for ``task_id``."""
        managed = self.indicators.pop(task_id, None)
        if managed is not None:
            managed.indicator.complete()


__all__ = ["ProgressManager"]
