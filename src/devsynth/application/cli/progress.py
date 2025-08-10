"""Lightweight progress utilities for CLI commands.

This module provides a minimal ``ProgressManager`` that tracks active
progress indicators created via the :class:`~devsynth.interface.ux_bridge.UXBridge`.
It replaces the earlier enhanced progress system with a simpler
implementation focused on clarity rather than rich visuals.
"""

from __future__ import annotations

from typing import Dict, Optional

from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge


class ProgressManager:
    """Create and manage progress indicators for CLI tasks."""

    def __init__(self, bridge: UXBridge) -> None:
        self.bridge = bridge
        self.indicators: Dict[str, ProgressIndicator] = {}

    def create_progress(
        self, task_id: str, description: str, total: int = 100
    ) -> ProgressIndicator:
        """Create and store a progress indicator for ``task_id``."""
        indicator = self.bridge.create_progress(description, total=total)
        self.indicators[task_id] = indicator
        return indicator

    def get_progress(self, task_id: str) -> Optional[ProgressIndicator]:
        """Return the indicator for ``task_id`` if it exists."""
        return self.indicators.get(task_id)

    def update_progress(
        self, task_id: str, advance: float = 1, description: Optional[str] = None
    ) -> None:
        """Update the indicator associated with ``task_id``."""
        indicator = self.indicators.get(task_id)
        if indicator is not None:
            indicator.update(advance=advance, description=description)

    def complete_progress(self, task_id: str) -> None:
        """Complete and remove the indicator for ``task_id``."""
        indicator = self.indicators.pop(task_id, None)
        if indicator is not None:
            indicator.complete()


__all__ = ["ProgressManager"]
