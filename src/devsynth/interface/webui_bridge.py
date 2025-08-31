from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Sequence

# Streamlit is an optional dependency; do not import at module scope.
st = None  # type: ignore[assignment]

from devsynth.exceptions import DevSynthError
from devsynth.interface.state_access import get_session_value as _get_session_value
from devsynth.interface.state_access import set_session_value as _set_session_value
from devsynth.logging_setup import DevSynthLogger

from .output_formatter import OutputFormatter
from .shared_bridge import SharedBridgeMixin
from .ux_bridge import ProgressIndicator, UXBridge, sanitize_output

# Module level logger
logger = DevSynthLogger(__name__)


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
                "Streamlit is required for WebUI features. Install the optional extra:\n"
                "  poetry install --with dev --extras webui"
            ) from exc


class WebUIProgressIndicator(ProgressIndicator):
    """Enhanced progress indicator for WebUI with better visual feedback."""

    def __init__(self, description: str, total: int) -> None:
        self._description = description
        self._total = total
        self._current = 0
        self._status = "Starting..."
        self._subtasks: Dict[str, Dict[str, Any]] = {}
        self._update_times = []

    def update(
        self,
        *,
        advance: float = 1,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update the progress indicator.

        Args:
            advance: Amount to advance the progress
            description: New description for the progress indicator
            status: Status message to display (e.g., "Processing...", "Analyzing...")
        """
        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                self._description = sanitize_output(desc_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                pass

        # Store status if provided
        if status is not None:
            try:
                status_str = str(status)
                self._status = sanitize_output(status_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                self._status = "In progress..."
        else:
            # If no status is provided, use a default based on progress
            if self._current >= self._total:
                self._status = "Complete"
            elif self._current >= 0.99 * self._total:
                self._status = "Finalizing..."
            elif self._current >= 0.75 * self._total:
                self._status = "Almost done..."
            elif self._current >= 0.5 * self._total:
                self._status = "Halfway there..."
            elif self._current >= 0.25 * self._total:
                self._status = "Processing..."
            else:
                self._status = "Starting..."

        self._current += advance
        self._update_times.append((time.time(), self._current))

    def complete(self) -> None:
        """Mark the progress indicator as complete."""
        self._current = self._total

    def add_subtask(self, description: str, total: int = 100) -> str:
        """Add a subtask to the progress indicator.

        Args:
            description: Description of the subtask
            total: Total steps for the subtask

        Returns:
            task_id: ID of the created subtask
        """
        # Handle description safely, converting to string if needed
        try:
            desc_str = str(description)
            desc = sanitize_output(desc_str)
        except Exception:
            # Fallback for objects that can't be safely converted to string
            desc = "<subtask>"

        task_id = f"subtask_{len(self._subtasks)}"
        self._subtasks[task_id] = {
            "description": desc,
            "total": total,
            "current": 0,
            "completed": False,
        }
        return task_id

    def update_subtask(
        self, task_id: str, advance: float = 1, description: Optional[str] = None
    ) -> None:
        """Update a subtask's progress.

        Args:
            task_id: ID of the subtask to update
            advance: Amount to advance the progress
            description: New description for the subtask
        """
        if task_id not in self._subtasks:
            return

        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                self._subtasks[task_id]["description"] = sanitize_output(desc_str)
            except Exception:
                # Fallback for objects that can't be safely converted to string
                pass

        self._subtasks[task_id]["current"] += advance

    def complete_subtask(self, task_id: str) -> None:
        """Mark a subtask as complete.

        Args:
            task_id: ID of the subtask to complete
        """
        if task_id not in self._subtasks:
            return

        # Complete all nested subtasks first if any
        if "nested_subtasks" in self._subtasks[task_id]:
            for nested_id in list(self._subtasks[task_id]["nested_subtasks"].keys()):
                self.complete_nested_subtask(task_id, nested_id)

        self._subtasks[task_id]["current"] = self._subtasks[task_id]["total"]
        self._subtasks[task_id]["completed"] = True

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
        if parent_id not in self._subtasks:
            return ""

        # Handle description safely, converting to string if needed
        try:
            desc_str = str(description)
            desc = sanitize_output(desc_str)
        except Exception:
            # Fallback for objects that can't be safely converted to string
            desc = "<nested subtask>"

        # Initialize nested subtasks dictionary for parent if it doesn't exist
        if "nested_subtasks" not in self._subtasks[parent_id]:
            self._subtasks[parent_id]["nested_subtasks"] = {}

        task_id = (
            f"nested_{parent_id}_{len(self._subtasks[parent_id]['nested_subtasks'])}"
        )
        self._subtasks[parent_id]["nested_subtasks"][task_id] = {
            "description": desc,
            "total": total,
            "current": 0,
            "status": status,
            "completed": False,
        }
        return task_id

    def update_nested_subtask(
        self,
        parent_id: str,
        task_id: str,
        advance: float = 1,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update a nested subtask's progress.

        Args:
            parent_id: ID of the parent subtask
            task_id: ID of the nested subtask to update
            advance: Amount to advance the progress
            description: New description for the nested subtask
            status: Status message to display
        """
        if (
            parent_id not in self._subtasks
            or "nested_subtasks" not in self._subtasks[parent_id]
            or task_id not in self._subtasks[parent_id]["nested_subtasks"]
        ):
            return

        # Handle description safely, converting to string if needed
        if description is not None:
            try:
                desc_str = str(description)
                self._subtasks[parent_id]["nested_subtasks"][task_id]["description"] = (
                    sanitize_output(desc_str)
                )
            except Exception:
                # Fallback for objects that can't be safely converted to string
                pass

        # Handle status safely
        if status is not None:
            try:
                status_str = str(status)
                self._subtasks[parent_id]["nested_subtasks"][task_id]["status"] = (
                    sanitize_output(status_str)
                )
            except Exception:
                # Fallback for objects that can't be safely converted to string
                self._subtasks[parent_id]["nested_subtasks"][task_id][
                    "status"
                ] = "In progress..."
        else:
            # If no status is provided, use a default based on progress
            current = self._subtasks[parent_id]["nested_subtasks"][task_id]["current"]
            total = self._subtasks[parent_id]["nested_subtasks"][task_id]["total"]
            if current >= total:
                self._subtasks[parent_id]["nested_subtasks"][task_id][
                    "status"
                ] = "Complete"
            elif current >= 0.99 * total:
                self._subtasks[parent_id]["nested_subtasks"][task_id][
                    "status"
                ] = "Finalizing..."
            elif current >= 0.75 * total:
                self._subtasks[parent_id]["nested_subtasks"][task_id][
                    "status"
                ] = "Almost done..."
            elif current >= 0.5 * total:
                self._subtasks[parent_id]["nested_subtasks"][task_id][
                    "status"
                ] = "Halfway there..."
            elif current >= 0.25 * total:
                self._subtasks[parent_id]["nested_subtasks"][task_id][
                    "status"
                ] = "Processing..."
            else:
                self._subtasks[parent_id]["nested_subtasks"][task_id][
                    "status"
                ] = "Starting..."

        self._subtasks[parent_id]["nested_subtasks"][task_id]["current"] += advance

    def complete_nested_subtask(self, parent_id: str, task_id: str) -> None:
        """Mark a nested subtask as complete.

        Args:
            parent_id: ID of the parent subtask
            task_id: ID of the nested subtask to complete
        """
        if (
            parent_id not in self._subtasks
            or "nested_subtasks" not in self._subtasks[parent_id]
            or task_id not in self._subtasks[parent_id]["nested_subtasks"]
        ):
            return

        self._subtasks[parent_id]["nested_subtasks"][task_id]["current"] = (
            self._subtasks[parent_id]["nested_subtasks"][task_id]["total"]
        )
        self._subtasks[parent_id]["nested_subtasks"][task_id]["completed"] = True
        self._subtasks[parent_id]["nested_subtasks"][task_id]["status"] = "Complete"


class WebUIBridge(SharedBridgeMixin, UXBridge):
    """Bridge for WebUI interactions implementing the :class:`UXBridge` API.

    This implementation provides a consistent interface with CLIUXBridge
    to ensure parity between CLI and WebUI interfaces.
    """

    def __init__(self) -> None:
        self.messages: List[str] = []
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

                # Try to convert to float first (handles both integers and floats in string form)
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
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
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

    # ------------------------------------------------------------------
    # Session state management utilities
    # ------------------------------------------------------------------
    @staticmethod
    def get_session_value(session_state, key, default=None):
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
    def set_session_value(session_state, key, value):
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
