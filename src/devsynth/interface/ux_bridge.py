"""User interaction protocol for DevSynth interfaces.

The bridge decouples workflow logic from any particular UI framework. All
front‑ends (CLI, WebUI, Agent API) implement this interface so that workflows
can reuse the same interaction patterns.
"""

from __future__ import annotations

import html
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence, Union

from devsynth.security.validation import parse_bool_env

try:  # pragma: no cover - import guarded for optional deps
    # Import directly from the sanitization module to avoid initializing the
    # entire security package, which may have optional dependencies.
    from devsynth.security.sanitization import sanitize_input
except ImportError:  # pragma: no cover - graceful degradation

    def sanitize_input(text: str) -> str:  # type: ignore[override]
        """Fallback sanitizer used when security helpers are unavailable."""
        return text


def sanitize_output(text: str) -> str:
    """Sanitize and escape user provided text for safe display.

    Respects the ``DEVSYNTH_SANITIZATION_ENABLED`` environment variable so that
    projects can disable all sanitization/escaping in trusted contexts.
    """

    sanitized = sanitize_input(text)
    if not parse_bool_env("DEVSYNTH_SANITIZATION_ENABLED", True):
        return sanitized
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
    def update(
        self,
        *,
        advance: float = 1,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Advance the progress indicator.

        Args:
            advance: Amount to advance the progress.
            description: Optional new description for the task.
            status: Optional short status message.
        """

    @abstractmethod
    def complete(self) -> None:
        """Mark the progress indicator as complete."""


class UXBridge(ABC):
    """Protocol defining basic user interaction methods.

    The original interface exposed the terse ``prompt``, ``confirm`` and
    ``print`` helpers.  The modern API uses the more explicit
    ``ask_question``, ``confirm_choice`` and ``display_result`` methods.  The
    old method names remain available as thin wrappers around the new API so
    existing front‑ends continue to work during the transition.
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
    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str = None
    ) -> None:
        """Display a message to the user.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
            message_type: Optional type of message (info, success, warning, error, etc.)
        """

    def handle_error(self, error: Union[Exception, Dict[str, Any], str]) -> None:
        """Handle an error with enhanced error messages.

        This method formats the error with actionable suggestions and documentation links,
        and displays it to the user.

        Args:
            error: The error to handle
        """
        # Default implementation just displays the error message
        self.display_result(str(error), highlight=True)

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
                self,
                *,
                advance: float = 1,
                description: Optional[str] = None,
                status: Optional[str] = None,
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
        """Backward compatible alias for :meth:`ask_question`.

        Parameters mirror those of :meth:`ask_question` so callers using the
        legacy name automatically benefit from the new behaviour.
        """
        return self.ask_question(
            message,
            choices=choices,
            default=default,
            show_default=show_default,
        )

    def confirm(self, message: str, *, default: bool = False) -> bool:
        """Backward compatible alias for :meth:`confirm_choice`."""
        return self.confirm_choice(message, default=default)

    def print(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        """Backward compatible alias for :meth:`display_result`.

        Args:
            message: Message to display to the user.
            highlight: Whether to emphasise the message.
            message_type: Optional semantic type forwarded to
                :meth:`display_result`.
        """
        self.display_result(message, highlight=highlight, message_type=message_type)


__all__ = ["UXBridge", "ProgressIndicator", "sanitize_output"]
