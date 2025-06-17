"""User interaction protocol for DevSynth interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence


class UXBridge(ABC):
    """Protocol defining basic user interaction methods."""

    @abstractmethod
    def prompt(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Prompt the user and return their response."""

    @abstractmethod
    def confirm(self, message: str, *, default: bool = False) -> bool:
        """Request confirmation from the user."""

    @abstractmethod
    def print(self, message: str, *, highlight: bool = False) -> None:
        """Display a message to the user."""


__all__ = ["UXBridge"]
