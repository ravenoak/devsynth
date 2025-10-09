from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from devsynth.exceptions import DevSynthError
from devsynth.interface.state_access import (
    SessionStateMapping,
)
from devsynth.interface.state_access import get_session_value as _get_session_value
from devsynth.interface.state_access import set_session_value as _set_session_value
from devsynth.logging_setup import DevSynthLogger

from .shared_bridge import SharedBridgeMixin
from .ux_bridge import ProgressIndicator, UXBridge, sanitize_output

# Streamlit is an optional dependency; do not import at module scope.
st = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from devsynth.interface.webui_state import WizardState
    from devsynth.interface.wizard_state_manager import WizardStateManager

# Module level logger
logger = DevSynthLogger(__name__)


@dataclass(slots=True)
class SubtaskState:
    """Track the state of Streamlit subtasks displayed in the progress widget."""

    description: str
    total: int
    current: float = 0.0
    status: str = "Starting..."
    completed: bool = False
    nested_subtasks: dict[str, "SubtaskState"] = field(default_factory=dict)


def _safe_text(value: object, *, fallback: str) -> str:
    """Convert ``value`` to sanitized text, preserving a fallback on failure."""

    try:
        return sanitize_output(str(value))
    except Exception:  # pragma: no cover - defensive sanitization
        return fallback


def _default_status(current: float, total: int) -> str:
    """Return a human-friendly status message based on progress."""

    if total <= 0:
        total = 1

    if current >= total:
        return "Complete"

    ratio = current / total
    if ratio >= 0.99:
        return "Finalizing..."
    if ratio >= 0.75:
        return "Almost done..."
    if ratio >= 0.5:
        return "Halfway there..."
    if ratio >= 0.25:
        return "Processing..."
    return "Starting..."


def _require_streamlit() -> None:
    """Ensure the ``streamlit`` package is available (lazy import).

    Raises:
        DevSynthError: If ``streamlit`` is not installed.
    """
    global st
    if st is None:
        try:  # pragma: no cover - optional dependency
            import importlib

            st = importlib.import_module("streamlit")  # type: ignore[assignment]
        except Exception as exc:  # pragma: no cover - error path
            raise DevSynthError(
                "Streamlit is required for WebUI features. Install the optional "
                "extra:\n"
                "  poetry install --with dev --extras webui"
            ) from exc


class WebUIProgressIndicator(ProgressIndicator):
    """Enhanced progress indicator for WebUI with better visual feedback."""

    def __init__(self, description: str, total: int) -> None:
        self._description = description
        self._total = total
        self._current = 0.0
        self._status = "Starting..."
        self._subtasks: dict[str, SubtaskState] = {}
        self._update_times: list[tuple[float, float]] = []

    def update(
        self,
        *,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update the progress indicator.

        Args:
            advance: Amount to advance the progress
            description: New description for the progress indicator
            status: Status message to display (e.g., "Processing...", "Analyzing...")
        """
        if description is not None:
            self._description = _safe_text(description, fallback=self._description)

        if status is not None:
            self._status = _safe_text(status, fallback=self._status)
        else:
            self._status = _default_status(self._current, self._total)

        self._current += advance
        self._update_times.append((time.time(), self._current))

    def complete(self) -> None:
        """Mark the progress indicator as complete."""
        self._current = self._total

    def add_subtask(
        self,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str:
        """Add a subtask to the progress indicator.

        Args:
            description: Description of the subtask
            total: Total steps for the subtask

        Returns:
            task_id: ID of the created subtask
        """
        desc = _safe_text(description, fallback="<subtask>")
        task_id = f"subtask_{len(self._subtasks)}"
        initial_status = _safe_text(status, fallback=_default_status(0.0, total))
        self._subtasks[task_id] = SubtaskState(
            description=desc,
            total=total,
            status=initial_status,
        )
        return task_id

    def update_subtask(
        self,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update a subtask's progress.

        Args:
            task_id: ID of the subtask to update
            advance: Amount to advance the progress
            description: New description for the subtask
        """
        subtask = self._subtasks.get(task_id)
        if subtask is None:
            return

        if description is not None:
            subtask.description = _safe_text(description, fallback=subtask.description)

        subtask.current += advance
        if status is not None:
            subtask.status = _safe_text(status, fallback=subtask.status)
        else:
            subtask.status = _default_status(subtask.current, subtask.total)

    def complete_subtask(self, task_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            task_id: ID of the subtask to complete
        """
        subtask = self._subtasks.get(task_id)
        if subtask is None:
            return

        for nested_id in list(subtask.nested_subtasks.keys()):
            self.complete_nested_subtask(task_id, nested_id)

        subtask.current = float(subtask.total)
        subtask.completed = True
        subtask.status = "Complete"

    def add_nested_subtask(
        self,
        parent_id: str,
        description: str,
        total: int = 100,
        status: str = "Starting...",
    ) -> str:
        """Add a nested subtask to a subtask.

        Args:
            parent_id: ID of the parent subtask
            description: Description of the nested subtask
            total: Total steps for the nested subtask
            status: Initial status message for the nested subtask

        Returns:
            task_id: ID of the created nested subtask
        """
        parent = self._subtasks.get(parent_id)
        if parent is None:
            return ""

        desc = _safe_text(description, fallback="<nested subtask>")
        initial_status = (
            _safe_text(status, fallback=desc)
            if status is not None
            else _default_status(0.0, total)
        )

        task_id = f"nested_{parent_id}_{len(parent.nested_subtasks)}"
        parent.nested_subtasks[task_id] = SubtaskState(
            description=desc,
            total=total,
            status=initial_status,
        )
        return task_id

    def update_nested_subtask(
        self,
        parent_id: str,
        task_id: str,
        advance: float = 1,
        description: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update a nested subtask's progress.

        Args:
            parent_id: ID of the parent subtask
            task_id: ID of the nested subtask to update
            advance: Amount to advance the progress
            description: New description for the nested subtask
            status: Status message to display
        """
        parent = self._subtasks.get(parent_id)
        if parent is None:
            return

        nested = parent.nested_subtasks.get(task_id)
        if nested is None:
            return

        if description is not None:
            nested.description = _safe_text(description, fallback=nested.description)

        if status is not None:
            nested.status = _safe_text(status, fallback=nested.status)
        else:
            nested.status = _default_status(nested.current, nested.total)

        nested.current += advance

    def complete_nested_subtask(self, parent_id: str, task_id: str) -> None:
        """Mark a nested subtask as complete.

        Args:
            parent_id: ID of the parent subtask
            task_id: ID of the nested subtask to complete
        """
        parent = self._subtasks.get(parent_id)
        if parent is None:
            return

        nested = parent.nested_subtasks.get(task_id)
        if nested is None:
            return

        nested.current = float(nested.total)
        nested.completed = True
        nested.status = "Complete"


class WebUIBridge(SharedBridgeMixin, UXBridge):
    """Bridge for WebUI interactions implementing the :class:`UXBridge` API.

    This implementation provides a consistent interface with CLIUXBridge
    to ensure parity between CLI and WebUI interfaces.
    """

    def __init__(self) -> None:
        self.messages: list[str] = []
        super().__init__()

    # ------------------------------------------------------------------
    # Wizard utilities
    # ------------------------------------------------------------------
    @staticmethod
    def adjust_wizard_step(current: int, *, direction: str, total: int) -> int:
        """Return the next wizard step given a direction.

        Parameters
        ----------
        current:
            Current step index.
        direction:
            Either ``"next"`` or ``"back"``.
        total:
            Total number of steps.

        Returns
        -------
        int
            Clamped step index.
        """
        # Ensure total is a positive integer
        if not isinstance(total, int) or total <= 0:
            logger.warning(f"Invalid total steps: {total}, defaulting to 1")
            total = 1

        # Ensure current is a valid integer
        try:
            current = int(current)
        except (ValueError, TypeError):
            logger.warning(f"Invalid current step: {current}, defaulting to 0")
            current = 0

        # Calculate the next step based on direction
        if direction == "next":
            candidate = current + 1
        elif direction == "back":
            candidate = current - 1
        else:
            logger.warning(f"Invalid direction: {direction}, keeping current step")
            candidate = current

        # Ensure the step is within valid range
        return max(0, min(total - 1, candidate))

    @staticmethod
    def normalize_wizard_step(value: Any, *, total: int) -> int:
        """Coerce arbitrary values to a valid wizard step index.

        Parameters
        ----------
        value:
            The value to normalize, can be any type.
        total:
            Total number of steps.

        Returns
        -------
        int
            A valid step index between 0 and total-1.
        """
        # Ensure total is a positive integer
        if not isinstance(total, int) or total <= 0:
            logger.warning(f"Invalid total steps: {total}, defaulting to 1")
            total = 1

        # Handle different types of values
        if value is None:
            logger.debug("Normalizing None value to step 0")
            return 0

        try:
            # First try direct integer conversion
            if isinstance(value, int):
                step = value
            # Then try float conversion (for string representations of floats)
            elif isinstance(value, float):
                step = int(value)
            # Finally try string conversion with careful handling
            else:
                value_str = str(value).strip()
                if not value_str:
                    logger.debug("Empty string value, defaulting to step 0")
                    return 0

                # Convert to float first to accept integer or float strings
                step = int(float(value_str))

            logger.debug(f"Normalized value {value} to step {step}")
            return max(0, min(total - 1, step))

        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to normalize step value '{value}': {str(e)}, defaulting to 0"
            )
            return 0

    def ask_question(
        self,
        message: str,
        *,
        choices: Sequence[str] | None = None,
        default: str | None = None,
        show_default: bool = True,
    ) -> str:
        """Ask a question and return the response.

        In this lightweight implementation, it returns the default value.
        In a full implementation, it would display a form element.

        Args:
            message: The question to ask
            choices: Optional list of choices
            default: Default value
            show_default: Whether to show the default value

        Returns:
            The user's response (or default in this implementation)
        """
        logger.debug(f"WebUI asking question: {message}")
        answer = str(default or "")
        logger.debug(f"WebUI user answered: {answer}")
        return answer

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        """Request confirmation from the user.

        In this lightweight implementation, it returns the default value.
        In a full implementation, it would display a checkbox or buttons.

        Args:
            message: The confirmation message
            default: Default value

        Returns:
            The user's choice (or default in this implementation)
        """
        logger.debug(f"WebUI asking for confirmation: {message}")
        answer = default
        logger.debug(f"WebUI user confirmed: {answer}")
        return answer

    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str = None
    ) -> None:
        """Display a message to the user with Streamlit styling."""
        _require_streamlit()

        if message_type == "error":
            logger.error(f"WebUI displaying error: {message}")
        elif message_type == "warning":
            logger.warning(f"WebUI displaying warning: {message}")
        elif message_type == "success":
            logger.info(f"WebUI displaying success: {message}")
        else:
            logger.debug(f"WebUI displaying message: {message}")

        formatted = self._format_for_output(
            message, highlight=highlight, message_type=message_type
        )

        if message_type == "error":
            st.error(formatted)
        elif message_type == "warning":
            st.warning(formatted)
        elif message_type == "success":
            st.success(formatted)
        elif message_type == "info" or highlight:
            getattr(st, "info", st.write)(formatted)
        else:
            st.write(formatted)

        self.messages.append(formatted)

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator for long running tasks.

        Args:
            description: Description of the task
            total: Total steps for the task

        Returns:
            A progress indicator
        """
        return WebUIProgressIndicator(description, total)

    def get_wizard_manager(
        self,
        wizard_name: str,
        *,
        steps: int,
        initial_state: dict[str, Any] | None = None,
    ) -> WizardStateManager:
        """Return a :class:`WizardStateManager` bound to the current session."""

        _require_streamlit()
        session_state = getattr(st, "session_state", None)
        if session_state is None:
            raise DevSynthError(
                "Streamlit session_state is unavailable; cannot manage wizard state"
            )
        return self.create_wizard_manager(
            session_state,
            wizard_name,
            steps=steps,
            initial_state=initial_state,
        )

    @staticmethod
    def create_wizard_manager(
        session_state: SessionStateMapping | object,
        wizard_name: str,
        *,
        steps: int,
        initial_state: dict[str, Any] | None = None,
    ) -> WizardStateManager:
        """Instantiate a :class:`WizardStateManager` with defensive checks."""

        if session_state is None:
            raise DevSynthError(
                "Streamlit session_state is unavailable; cannot manage wizard state"
            )

        from devsynth.interface.wizard_state_manager import WizardStateManager

        return WizardStateManager(session_state, wizard_name, steps, initial_state)

    def get_wizard_state(
        self,
        wizard_name: str,
        *,
        steps: int,
        initial_state: dict[str, Any] | None = None,
    ) -> WizardState:
        """Return the :class:`WizardState` for the named wizard."""

        manager = self.get_wizard_manager(
            wizard_name, steps=steps, initial_state=initial_state
        )
        return manager.get_wizard_state()

    # ------------------------------------------------------------------
    # Session state management utilities
    # ------------------------------------------------------------------
    @staticmethod
    def get_session_value(
        session_state: SessionStateMapping | object | None,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a value from session state consistently.

        This function handles different implementations of session state
        and provides robust error handling.

        Args:
            session_state: The session state object
            key: The key to retrieve from session state
            default: The default value to return if the key is not found

        Returns:
            The value from session state or the default value
        """
        return _get_session_value(session_state, key, default)

    @staticmethod
    def set_session_value(
        session_state: SessionStateMapping | object | None,
        key: str,
        value: Any,
    ) -> bool:
        """Set a value in session state consistently.

        This function handles different implementations of session state
        and provides robust error handling.

        Args:
            session_state: The session state object
            key: The key to set in session state
            value: The value to set

        Returns:
            True if the value was set successfully, False otherwise
        """
        return _set_session_value(session_state, key, value)


__all__ = ["WebUIBridge", "WebUIProgressIndicator"]
