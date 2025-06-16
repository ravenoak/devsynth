from abc import ABC, abstractmethod
from typing import Optional, Sequence


class UXBridge(ABC):
    """Abstract interface for user interaction."""

    @abstractmethod
    def prompt(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Prompt the user for input."""

    @abstractmethod
    def confirm(self, message: str, *, default: bool = False) -> bool:
        """Ask the user to confirm an action."""

    @abstractmethod
    def print(self, message: str, *, highlight: bool = False) -> None:
        """Display a message to the user."""
