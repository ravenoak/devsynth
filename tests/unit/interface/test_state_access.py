"""
Tests for the state_access module.

This module tests the functions in the state_access module, including
get_session_value, set_session_value, is_session_state_available, and handle_state_error.
"""

from unittest.mock import MagicMock, patch

import pytest

# Import the module to test
from devsynth.interface.state_access import (
    get_session_value,
    handle_state_error,
    is_session_state_available,
    set_session_value,
)


@pytest.mark.medium
@pytest.fixture
def clean_state():
    """Set up clean state for tests."""
    # Store any global state that might be modified during tests

    # Reset any module-level state before test
    # No specific global state to reset in this module

    yield

    # Clean up state after test
    # Reset any module-level state that might have been modified


def test_is_session_state_available(clean_state):
    """Test the is_session_state_available function."""
    # Test with None
    assert is_session_state_available(None) is False

    # Test with a valid session state
    assert is_session_state_available({}) is True
    assert is_session_state_available(MagicMock()) is True


@pytest.mark.medium
def test_handle_state_error(clean_state):
    """Test the handle_state_error function."""
    # Mock the logger
    with patch("devsynth.interface.state_access.logger") as mock_logger:
        # Call the function
        handle_state_error("testing", "test_key", ValueError("Test error"))

        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with(
            "Error testing session state key 'test_key': Test error"
        )


@pytest.mark.medium
def test_get_session_value_with_none_session_state(clean_state):
    """Test get_session_value with None session state."""
    # Mock the logger
    with patch("devsynth.interface.state_access.logger") as mock_logger:
        # Call the function with None session state
        result = get_session_value(None, "test_key", "default_value")

        # Check that the function returns the default value
        assert result == "default_value"

        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with(
            "Session state not available, returning default for test_key"
        )


@pytest.mark.medium
def test_get_session_value_with_attribute_access(mock_session_state, clean_state):
    """Test get_session_value with attribute access."""
    # Set a value in the session state
    mock_session_state.test_key = "test_value"

    # Call the function
    result = get_session_value(mock_session_state, "test_key", "default_value")

    # Check that the function returns the expected value
    assert result == "test_value"


@pytest.mark.medium
def test_get_session_value_with_dict_access(mock_session_state, clean_state):
    """Test get_session_value with dictionary access."""
    # Set a value in the session state
    mock_session_state["test_key"] = "test_value"

    # Call the function
    result = get_session_value(mock_session_state, "test_key", "default_value")

    # Check that the function returns the expected value
    assert result == "test_value"


@pytest.mark.medium
def test_get_session_value_with_missing_key(mock_session_state, clean_state):
    """Test get_session_value with a missing key."""
    # Call the function with a key that doesn't exist
    result = get_session_value(mock_session_state, "missing_key", "default_value")

    # Check that the function returns the default value
    assert result == "default_value"


@pytest.mark.medium
def test_get_session_value_with_exception(clean_state):
    """Test get_session_value with an exception."""

    # Create a custom mock class that raises an exception when attributes are accessed
    class ExceptionSessionState:
        def __getattr__(self, name):
            raise Exception("Test error")

        def __getitem__(self, key):
            raise Exception("Test error")

    session_state = ExceptionSessionState()

    # Mock the logger
    with patch("devsynth.interface.state_access.logger") as mock_logger:
        # Call the function
        result = get_session_value(session_state, "test_key", "default_value")

        # Check that the function returns the default value
        assert result == "default_value"

        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with(
            "Error accessing session state key 'test_key': Test error"
        )


@pytest.mark.medium
def test_set_session_value_with_none_session_state(clean_state):
    """Test set_session_value with None session state."""
    # Mock the logger
    with patch("devsynth.interface.state_access.logger") as mock_logger:
        # Call the function with None session state
        result = set_session_value(None, "test_key", "test_value")

        # Check that the function returns False
        assert result is False

        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with(
            "Session state not available, cannot set test_key"
        )


@pytest.mark.medium
def test_set_session_value_with_attribute_access(mock_session_state, clean_state):
    """Test set_session_value with attribute access."""
    # Call the function
    result = set_session_value(mock_session_state, "test_key", "test_value")

    # Check that the function returns True
    assert result is True

    # Check that the value was set in the session state
    assert mock_session_state.test_key == "test_value"


@pytest.mark.medium
def test_set_session_value_with_dict_access(mock_session_state, clean_state):
    """Test set_session_value with dictionary access."""
    # Call the function
    result = set_session_value(mock_session_state, "test_key", "test_value")

    # Check that the function returns True
    assert result is True

    # Check that the value was set in the session state
    assert mock_session_state["test_key"] == "test_value"


@pytest.mark.medium
def test_set_session_value_with_attribute_exception(clean_state):
    """Test set_session_value with an exception during attribute access."""

    # Create a custom mock class that raises an exception when attributes are set
    # but allows item access to succeed
    class AttributeExceptionSessionState:
        def __init__(self):
            self.items = {}

        def __setattr__(self, name, value):
            if name == "items":
                # Allow setting the items dictionary
                object.__setattr__(self, name, value)
            else:
                # Raise exception for other attributes
                raise Exception("Test error")

        def __setitem__(self, key, value):
            # Allow item access to succeed
            self.items[key] = value

    session_state = AttributeExceptionSessionState()

    # Mock the logger
    with patch("devsynth.interface.state_access.logger") as mock_logger:
        # Call the function
        result = set_session_value(session_state, "test_key", "test_value")

        # Check that the function returns True because item access succeeds
        # even though attribute access fails
        assert result is True

        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with(
            "Error setting session state key 'test_key': Test error"
        )


@pytest.mark.medium
def test_set_session_value_with_dict_exception(clean_state):
    """Test set_session_value with an exception during dictionary access."""

    # Create a custom mock class that allows attribute access but raises an exception for item access
    class DictExceptionSessionState:
        def __init__(self):
            self.attributes = {}

        def __setattr__(self, name, value):
            if name == "attributes":
                # Allow setting the attributes dictionary
                object.__setattr__(self, name, value)
            else:
                # Store other attributes in the dictionary
                self.attributes[name] = value

        def __getattr__(self, name):
            if name in self.attributes:
                return self.attributes[name]
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        def __setitem__(self, key, value):
            raise Exception("Test error")

    session_state = DictExceptionSessionState()

    # Mock the logger
    with patch("devsynth.interface.state_access.logger") as mock_logger:
        # Call the function
        result = set_session_value(session_state, "test_key", "test_value")

        # Check that the function returns True (attribute access succeeded)
        assert result is True

        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with(
            "Error setting via item session state key 'test_key': Test error"
        )


@pytest.mark.medium
def test_set_session_value_with_both_exceptions(clean_state):
    """Test set_session_value with exceptions during both attribute and dictionary access."""

    # Create a custom mock class that raises exceptions for both attribute and item access
    class BothExceptionsSessionState:
        def __setattr__(self, name, value):
            raise Exception("Attribute error")

        def __setitem__(self, key, value):
            raise Exception("Item error")

    session_state = BothExceptionsSessionState()

    # Mock the logger
    with patch("devsynth.interface.state_access.logger") as mock_logger:
        # Call the function
        result = set_session_value(session_state, "test_key", "test_value")

        # Check that the function returns False
        assert result is False

        # Check that the logger was called with the expected messages
        mock_logger.warning.assert_any_call(
            "Error setting session state key 'test_key': Attribute error"
        )
        mock_logger.warning.assert_any_call(
            "Error setting via item session state key 'test_key': Item error"
        )


@pytest.mark.medium
def test_integration_with_streamlit(mock_streamlit_for_state, clean_state):
    """Test integration with streamlit."""
    # Set a value using set_session_value
    result = set_session_value(
        mock_streamlit_for_state.session_state, "test_key", "test_value"
    )

    # Check that the function returns True
    assert result is True

    # Check that the value was set in the session state
    assert mock_streamlit_for_state.session_state.test_key == "test_value"

    # Get the value using get_session_value
    value = get_session_value(
        mock_streamlit_for_state.session_state, "test_key", "default_value"
    )

    # Check that the function returns the expected value
    assert value == "test_value"
