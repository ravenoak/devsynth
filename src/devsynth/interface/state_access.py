"""Unified state access for DevSynth interfaces.

This module provides standardized functions for accessing session state
across different components of the system.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

# Module level logger
logger = logging.getLogger(__name__)


@runtime_checkable
class SessionStateMapping(Protocol):
    """Minimum mapping protocol needed for Streamlit ``session_state`` objects."""

    def get(self, key: str, default: Any = ...) -> Any:  # pragma: no cover - protocol
        ...

    def __contains__(self, key: object) -> bool:  # pragma: no cover - protocol
        ...

    def __getitem__(self, key: str) -> Any:  # pragma: no cover - protocol
        ...

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover - protocol
        ...


def _as_session_mapping(session_state: object | None) -> SessionStateMapping | None:
    """Return a typed mapping view when available."""

    if session_state is None:
        return None
    if isinstance(session_state, SessionStateMapping):
        return session_state
    return None


def is_session_state_available(session_state: object | None) -> bool:
    """Check if session state is available and usable.

    Args:
        session_state: The session state object to check

    Returns:
        True if session state is available and usable, False otherwise
    """
    return session_state is not None


def handle_state_error(operation: str, key: str, error: Exception) -> None:
    """Handle errors in state operations consistently.

    Args:
        operation: The operation being performed (get, set, etc.)
        key: The key being accessed
        error: The exception that occurred
    """
    logger.warning(f"Error {operation} session state key '{key}': {str(error)}")


def get_session_value(
    session_state: object | None, key: str, default: Any = None
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
    if not is_session_state_available(session_state):
        logger.warning(f"Session state not available, returning default for {key}")
        return default

    mapping = _as_session_mapping(session_state)

    try:
        # First try attribute access (common in production)
        value = getattr(session_state, key, None)

        # If not found and session_state is dict-like, try dict access (common in tests)
        if value is None and mapping is not None:
            value = mapping.get(key, default)

        # If still None but not explicitly set to None, return default
        if (
            value is None
            and key not in dir(session_state)
            and (mapping is None or key not in mapping)
        ):
            return default

        return value
    except (AttributeError, TypeError) as e:
        # Log the error for debugging
        handle_state_error("accessing", key, e)
        return default


def set_session_value(session_state: object | None, key: str, value: Any) -> bool:
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
    if not is_session_state_available(session_state):
        logger.warning(f"Session state not available, cannot set {key}")
        return False

    success = False
    mapping = _as_session_mapping(session_state)
    try:
        # Try attribute access first (common in production)
        setattr(session_state, key, value)
        success = True
    except (AttributeError, TypeError) as e:
        handle_state_error("setting", key, e)

    try:
        # Also try dict-like access (common in tests)
        if mapping is not None:
            mapping[key] = value
            success = True
    except (TypeError, KeyError) as e:
        handle_state_error("setting via item", key, e)

    return success


__all__ = [
    "SessionStateMapping",
    "is_session_state_available",
    "handle_state_error",
    "get_session_value",
    "set_session_value",
]
