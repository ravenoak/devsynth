"""User interaction protocol for DevSynth interfaces.

The bridge decouples workflow logic from any particular UI framework. All
front‑ends (CLI, WebUI, Agent API) implement this interface so that workflows
can reuse the same interaction patterns.
"""

from __future__ import annotations

import html
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any, Literal, Protocol, TypeAlias, TypedDict, runtime_checkable

from devsynth.security.validation import parse_bool_env

try:  # pragma: no cover - import guarded for optional deps
    # Import directly from the sanitization module to avoid initializing the
    # entire security package, which may have optional dependencies.
    from devsynth.security.sanitization import sanitize_input
except ImportError:  # pragma: no cover - graceful degradation

    def sanitize_input(text: str) -> str:
        """Fallback sanitizer used when security helpers are unavailable."""
        return text


def sanitize_output(text: str) -> str:
    """Sanitize and escape user provided text for safe display.

    Respects the ``DEVSYNTH_SANITIZATION_ENABLED`` environment variable so that
    projects can disable all sanitization/escaping in trusted contexts.
    """

    sanitized: str = sanitize_input(text)
    if not parse_bool_env("DEVSYNTH_SANITIZATION_ENABLED", True):
        return sanitized
    return html.escape(sanitized)


PROGRESS_STATUS_VALUES: tuple[str, ...] = (
    "Starting...",
    "Processing...",
    "Halfway there...",
    "Almost done...",
    "Finalizing...",
    "In progress...",
    "Complete",
)

ProgressStatusText: TypeAlias = Literal[
    "Starting...",
    "Processing...",
    "Halfway there...",
    "Almost done...",
    "Finalizing...",
    "In progress...",
    "Complete",
]


class SubtaskProgressSnapshot(TypedDict, total=False):
    """Structure describing a subtask or nested subtask."""

    description: str
    total: float
    current: float
    status: ProgressStatusText
    nested_subtasks: dict[str, SubtaskProgressSnapshot]


@runtime_checkable
class SupportsSubtasks(Protocol):
    """Protocol capturing operations available on subtask-aware indicators."""

    def add_subtask(
        self,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str: ...

    def update_subtask(
        self,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None: ...

    def complete_subtask(self, task_id: str) -> None: ...


@runtime_checkable
class SupportsNestedSubtasks(SupportsSubtasks, Protocol):
    """Protocol documenting nested subtask helpers when available."""

    def add_nested_subtask(
        self,
        parent_id: str,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str: ...

    def update_nested_subtask(
        self,
        parent_id: str,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None: ...

    def complete_nested_subtask(self, parent_id: str, task_id: str) -> None: ...


class ProgressIndicator(ABC):
    """Handle to update progress for long running operations."""

    def __enter__(self) -> ProgressIndicator:  # pragma: no cover - simple passthrough
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any
    ) -> None:  # pragma: no cover - simple passthrough
        self.complete()

    @abstractmethod
    def update(
        self,
        *,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
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

    # ------------------------------------------------------------------
    # Optional subtask helpers
    # ------------------------------------------------------------------
    def add_subtask(
        self,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str:
        """Register a subtask with the progress indicator."""

        raise NotImplementedError("Subtasks are not supported by this indicator")

    def update_subtask(
        self,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update a previously registered subtask."""

        raise NotImplementedError("Subtasks are not supported by this indicator")

    def complete_subtask(self, task_id: str) -> None:
        """Complete a registered subtask."""

        raise NotImplementedError("Subtasks are not supported by this indicator")

    def add_nested_subtask(
        self,
        parent_id: str,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str:
        """Register a nested subtask under a parent subtask."""

        raise NotImplementedError("Nested subtasks are not supported by this indicator")

    def update_nested_subtask(
        self,
        parent_id: str,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update a nested subtask."""

        raise NotImplementedError("Nested subtasks are not supported by this indicator")

    def complete_nested_subtask(self, parent_id: str, task_id: str) -> None:
        """Complete a nested subtask."""

        raise NotImplementedError("Nested subtasks are not supported by this indicator")


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

    @property
    def capabilities(self) -> Mapping[str, bool]:
        """Advertise optional UX features supported by the bridge."""

        return MappingProxyType({})

    @abstractmethod
    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        """Prompt the user with a question and return their response."""

    @abstractmethod
    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        """Request confirmation from the user."""

    @abstractmethod
    def display_result(
        self,
        message: str,
        *,
        highlight: bool = False,
        message_type: str | None = None,
    ) -> None:
        """Display a message to the user.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
            message_type: Optional type of message (info, success, warning, error, etc.)
        """

    def handle_error(self, error: Exception | Mapping[str, Any] | str) -> None:
        """Handle an error with enhanced error messages.

        This method formats the error with actionable suggestions and documentation links,
        and displays it to the user.

        Args:
            error: The error to handle
        """
        # Default implementation just displays the error message
        self.display_result(str(error), highlight=True, message_type="error")

    def display_error(
        self,
        error: Exception | Mapping[str, Any] | str,
        *,
        include_suggestions: bool = True,
    ) -> None:
        """Display an error message using the bridge's error handling pipeline.

        Implementations can override this method to surface richer diagnostics
        (for example, actionable suggestions). The default implementation
        delegates to :meth:`handle_error` so existing subclasses automatically
        benefit from the enhanced error display logic.

        Args:
            error: The error object or message to display.
            include_suggestions: Whether to include actionable suggestions when
                available. The base implementation ignores this flag but accepts
                it for API compatibility with CLI helpers.
        """

        # ``include_suggestions`` is accepted for compatibility with CLI
        # helpers. Implementations that support suggestion toggles can honour
        # the flag. The default behaviour simply routes through ``handle_error``.
        _ = include_suggestions
        self.handle_error(error)

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator for long running tasks.

        Subclasses can override this to provide rich progress reporting.  The
        base implementation simply returns a no-op progress indicator so that
        lightweight test bridges do not need to implement the method.
        """

        class _DummyProgress(ProgressIndicator, SupportsNestedSubtasks):
            """Minimal indicator used during tests when no UI is attached."""

            def __init__(self) -> None:
                self._counter = 0

            def _next_id(self, prefix: str) -> str:
                self._counter += 1
                return f"{prefix}_{self._counter}"

            def update(
                self,
                *,
                advance: float = 1,
                description: str | None = None,
                status: str | None = None,
            ) -> None:  # pragma: no cover - simple no-op
                pass

            def complete(self) -> None:  # pragma: no cover - simple no-op
                pass

            def add_subtask(
                self,
                description: str,
                total: int = 100,
                status: str = "Starting...",
            ) -> str:  # pragma: no cover - simple no-op
                return self._next_id("subtask")

            def update_subtask(
                self,
                task_id: str,
                advance: float = 1,
                description: str | None = None,
                status: str | None = None,
            ) -> None:  # pragma: no cover - simple no-op
                pass

            def complete_subtask(
                self, task_id: str
            ) -> None:  # pragma: no cover - simple no-op
                pass

            def add_nested_subtask(
                self,
                parent_id: str,
                description: str,
                total: int = 100,
                status: str = "Starting...",
            ) -> str:  # pragma: no cover - simple no-op
                return self._next_id("nested")

            def update_nested_subtask(
                self,
                parent_id: str,
                task_id: str,
                advance: float = 1,
                description: str | None = None,
                status: str | None = None,
            ) -> None:  # pragma: no cover - simple no-op
                pass

            def complete_nested_subtask(
                self, parent_id: str, task_id: str
            ) -> None:  # pragma: no cover - simple no-op
                pass

        return _DummyProgress()

    # ------------------------------------------------------------------
    # Backwards compatible API
    # ------------------------------------------------------------------

    def prompt(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
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


__all__ = [
    "UXBridge",
    "ProgressIndicator",
    "sanitize_output",
    "PROGRESS_STATUS_VALUES",
    "ProgressStatusText",
    "SubtaskProgressSnapshot",
    "SupportsSubtasks",
    "SupportsNestedSubtasks",
]
