"""User interaction protocol for DevSynth interfaces.

The bridge decouples workflow logic from any particular UI framework. All
front‑ends (CLI, WebUI, Agent API) implement this interface so that workflows
can reuse the same interaction patterns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence
import html

from devsynth.security import sanitize_input


def sanitize_output(text: str) -> str:
    """Sanitize and escape user provided text for safe display."""
    sanitized = sanitize_input(text)
    return html.escape(sanitized)


class ProgressIndicator(ABC):
    """Handle to update progress for long running operations."""

    def __enter__(self) -> "ProgressIndicator":  # pragma: no cover - simple passthrough
        return self

    def __exit__(
        self, exc_type, exc, tb
    ) -> None:  # pragma: no cover - simple passthrough
        self.complete()

    @abstractmethod
    def update(self, *, advance: float = 1, description: Optional[str] = None) -> None:
        """Advance the progress indicator."""

    @abstractmethod
    def complete(self) -> None:
        """Mark the progress indicator as complete."""


class UXBridge(ABC):
    """Protocol defining basic user interaction methods.

    The original interface exposed ``prompt``, ``confirm`` and ``print``.  This
    version adds the more descriptive ``ask_question``, ``confirm_choice`` and
    ``display_result`` methods.  The legacy method names remain for backward
    compatibility and simply delegate to the new ones.
    """

    # ------------------------------------------------------------------
    # New descriptive methods
    # ------------------------------------------------------------------

    @abstractmethod
    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Prompt the user with a question and return their response."""

    @abstractmethod
    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        """Request confirmation from the user."""

    @abstractmethod
    def display_result(self, message: str, *, highlight: bool = False) -> None:
        """Display a message to the user."""

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator for long running tasks.

        Subclasses can override this to provide rich progress reporting.  The
        base implementation simply returns a no-op progress indicator so that
        lightweight test bridges do not need to implement the method.
        """

        class _DummyProgress(ProgressIndicator):
            def update(
                self, *, advance: float = 1, description: Optional[str] = None
            ) -> None:  # pragma: no cover - simple no-op
                pass

            def complete(self) -> None:  # pragma: no cover - simple no-op
                pass

        return _DummyProgress()

    # ------------------------------------------------------------------
    # Backwards compatible API
    # ------------------------------------------------------------------

    def prompt(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Alias for :meth:`ask_question`."""
        return self.ask_question(
            message,
            choices=choices,
            default=default,
            show_default=show_default,
        )

    def confirm(self, message: str, *, default: bool = False) -> bool:
        """Alias for :meth:`confirm_choice`."""
        return self.confirm_choice(message, default=default)

    def print(self, message: str, *, highlight: bool = False) -> None:
        """Alias for :meth:`display_result`."""
        self.display_result(message, highlight=highlight)


__all__ = ["UXBridge", "ProgressIndicator", "sanitize_output"]
