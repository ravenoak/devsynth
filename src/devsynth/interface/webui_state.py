"""
WebUI state management utilities.

This module provides common utilities for managing state in the WebUI components.
It ensures consistent state persistence and error handling across all WebUI pages.
"""

import importlib
import logging
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, Generic, TypeVar, assert_type

from devsynth.exceptions import DevSynthError
from devsynth.interface.state_access import get_session_value as _get_session_value
from devsynth.interface.state_access import set_session_value as _set_session_value
from devsynth.logging_setup import DevSynthLogger

# Module level logger
logger = DevSynthLogger(__name__)

# Type variable for generic functions
T = TypeVar("T")


def _require_streamlit() -> Any:
    try:
        return importlib.import_module("streamlit")
    except ModuleNotFoundError as e:
        raise DevSynthError(
            "Streamlit is required for WebUI state utilities but is not installed. "
            "Install the 'webui' extra, e.g.:\n"
            "  poetry install --with dev --extras webui\n"
            "Or run CLI/doctor commands without WebUI."
        ) from e


# Optional module-level reference used by tests to inject a dummy Streamlit
st: Any | None = None


def _get_st() -> Any:
    return st if st is not None else _require_streamlit()


def get_session_value(key: str, default: Any = None) -> Any:
    """
    Get a value from the session state with error handling.

    Args:
        key: The key to retrieve from the session state
        default: The default value to return if the key is not found

    Returns:
        The value from the session state or the default value
    """
    s = _get_st()
    return _get_session_value(s.session_state, key, default)


def set_session_value(key: str, value: Any) -> bool:
    """
    Set a value in the session state with error handling.

    Args:
        key: The key to set in the session state
        value: The value to set

    Returns:
        True if the value was set successfully, False otherwise
    """
    s = _get_st()
    success: bool = _set_session_value(s.session_state, key, value)
    if success:
        logger.debug(f"Set '{key}' in session state")
    return success


def with_state_management(
    prefix: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to add state management to a WebUI page or component.

    This decorator adds get_session_value and set_session_value methods to the
    decorated function, with an optional prefix for the keys.

    Args:
        prefix: Optional prefix for session state keys

    Returns:
        Decorated function with state management
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Add state management functions to kwargs
            def prefixed_get(key: str, default: Any = None) -> Any:
                full_key = f"{prefix}_{key}" if prefix else key
                return get_session_value(full_key, default)

            def prefixed_set(key: str, value: Any) -> None:
                full_key = f"{prefix}_{key}" if prefix else key
                set_session_value(full_key, value)

            kwargs["get_session_value"] = prefixed_get
            kwargs["set_session_value"] = prefixed_set

            return func(*args, **kwargs)

        return wrapper

    return decorator


class PageState(Generic[T]):
    """
    Class for managing state for a specific WebUI page.

    This class provides a consistent interface for managing state across
    different pages, with proper error handling and logging.
    """

    def __init__(self, page_name: str, initial_state: dict[str, Any] | None = None):
        """
        Initialize the page state.

        Args:
            page_name: Name of the page (used as prefix for session state keys)
            initial_state: Optional initial state dictionary
        """
        self.page_name = page_name
        self.initial_state = initial_state or {}
        self._initialize_state()

    def _initialize_state(self) -> None:
        """Initialize the state with default values if not already set."""
        for key, value in self.initial_state.items():
            if not self.has(key):
                self.set(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the page state.

        Args:
            key: The key to retrieve
            default: The default value to return if the key is not found

        Returns:
            The value from the state or the default value
        """
        full_key = f"{self.page_name}_{key}"
        return get_session_value(full_key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the page state.

        Args:
            key: The key to set
            value: The value to set

        Returns:
            True if the value was set successfully, False otherwise
        """
        full_key = f"{self.page_name}_{key}"
        success = set_session_value(full_key, value)
        if not success:
            logger.error(f"Failed to set '{key}' in page state")
        return success

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the page state.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        full_key = f"{self.page_name}_{key}"
        # Use get_session_value with a special sentinel value to check existence
        sentinel = object()
        value = get_session_value(full_key, sentinel)
        return value is not sentinel

    def clear(self) -> None:
        """Clear all state for this page."""
        try:
            s = _get_st()
            if not hasattr(s, "session_state"):
                logger.warning(
                    f"Session state not available, cannot clear {self.page_name} state"
                )
                return

            keys_to_remove = [
                k for k in s.session_state.keys() if k.startswith(f"{self.page_name}_")
            ]
            for key in keys_to_remove:
                try:
                    del s.session_state[key]
                except KeyError:
                    pass
                try:
                    delattr(s.session_state, key)
                except AttributeError:
                    pass

            logger.debug(f"Cleared {len(keys_to_remove)} keys for {self.page_name}")
        except Exception as e:
            logger.exception(f"Error clearing state for {self.page_name}: {str(e)}")
            raise

    def reset(self) -> None:
        """Reset the state to the initial values."""
        self.clear()
        self._initialize_state()


class WizardState(PageState[Any]):
    """
    Specialized state management for wizards with multiple steps.

    This class extends PageState with additional functionality for
    managing wizard steps and navigation.
    """

    def __init__(
        self,
        wizard_name: str,
        steps: int,
        initial_state: dict[str, Any] | None = None,
    ):
        """
        Initialize the wizard state.

        Args:
            wizard_name: Name of the wizard (used as prefix for session state keys)
            steps: Total number of steps in the wizard
            initial_state: Optional initial state dictionary
        """
        # Add step tracking to initial state
        full_initial_state = initial_state or {}
        full_initial_state.update(
            {"current_step": 1, "total_steps": steps, "completed": False}
        )

        super().__init__(wizard_name, full_initial_state)

    def get_current_step(self) -> int:
        """
        Get the current step number.

        Returns:
            The current step number (1-based)
        """
        step = self.get("current_step", 1)
        return step if isinstance(step, int) else 1

    def get_total_steps(self) -> int:
        """
        Get the total number of steps.

        Returns:
            The total number of steps
        """
        steps = self.get("total_steps", 1)
        return steps if isinstance(steps, int) else 1

    def is_completed(self) -> bool:
        """
        Check if the wizard is completed.

        Returns:
            True if the wizard is completed, False otherwise
        """
        completed = self.get("completed", False)
        return completed if isinstance(completed, bool) else False

    def set_completed(self, completed: bool = True) -> bool:
        """
        Set the wizard completion status.

        Args:
            completed: Whether the wizard is completed

        Returns:
            True if the completion status was set successfully, False otherwise
        """
        success = self.set("completed", completed)
        if success:
            logger.debug(f"Set {self.page_name} completion status to {completed}")
        else:
            logger.error(
                f"Failed to set {self.page_name} completion status to {completed}"
            )
        return success

    def next_step(self) -> bool:
        """
        Move to the next step if possible.

        Returns:
            True if the step was changed successfully, False otherwise
        """
        current = self.get_current_step()
        total = self.get_total_steps()

        if current < total:
            success = self.set("current_step", current + 1)
            if success:
                logger.debug(f"Advanced {self.page_name} to step {current + 1}/{total}")
            else:
                logger.error(
                    f"Failed to advance {self.page_name} to step {current + 1}/{total}"
                )
            return success
        else:
            logger.debug(
                f"Already at last step ({current}/{total}) for {self.page_name}"
            )
            return True  # No change needed is considered success

    def previous_step(self) -> bool:
        """
        Move to the previous step if possible.

        Returns:
            True if the step was changed successfully, False otherwise
        """
        current = self.get_current_step()

        if current > 1:
            success = self.set("current_step", current - 1)
            if success:
                logger.debug(f"Moved {self.page_name} back to step {current - 1}")
            else:
                logger.error(
                    f"Failed to move {self.page_name} back to step {current - 1}"
                )
            return success
        else:
            logger.debug(f"Already at first step for {self.page_name}")
            return True  # No change needed is considered success

    def go_to_step(self, step: int) -> bool:
        """
        Go to a specific step.

        Args:
            step: The step number to go to (1-based)

        Returns:
            True if the step was changed successfully, False otherwise
        """
        total = self.get_total_steps()

        # Normalize step number
        normalized_step = max(1, min(step, total))

        if normalized_step != step:
            logger.warning(
                f"Normalized step from {step} to {normalized_step} "
                f"(valid range: 1-{total})"
            )

        success = self.set("current_step", normalized_step)
        if success:
            logger.debug(f"Set {self.page_name} to step {normalized_step}/{total}")
        else:
            logger.error(
                f"Failed to set {self.page_name} to step {normalized_step}/{total}"
            )
        return success


if TYPE_CHECKING:
    _page_state: PageState[Any] = PageState("example", {"key": "value"})
    assert_type(_page_state.initial_state, dict[str, Any])
