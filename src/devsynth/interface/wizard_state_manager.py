"""
Wizard state management coordination.

This module provides a centralized way to manage wizard state,
ensuring consistency between WebUIBridge and WizardState.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
from collections.abc import Sequence

from devsynth.config import get_project_config, save_config
from devsynth.interface.state_access import get_session_value, set_session_value
from devsynth.interface.webui_state import WizardState
from devsynth.logging_setup import DevSynthLogger

# Module level logger
logger = DevSynthLogger(__name__)


class WizardStateManager:
    """Manager for coordinating wizard state across components.

    This class provides a centralized way to manage wizard state,
    ensuring consistency between WebUIBridge and WizardState.
    """

    def __init__(
        self,
        session_state,
        wizard_name: str,
        steps: int,
        initial_state: dict[str, Any] | None = None,
    ):
        """
        Initialize the wizard state manager.

        Args:
            session_state: The session state object
            wizard_name: Name of the wizard
            steps: Total number of steps in the wizard
            initial_state: Optional initial state dictionary
        """
        self.session_state = session_state
        self.wizard_name = wizard_name
        self.steps = steps
        self.initial_state = initial_state or {}

    def get_wizard_state(self) -> WizardState:
        """Get the WizardState instance for this wizard.

        Returns:
            A WizardState instance
        """
        # Check if we already have a wizard state
        if not self.has_wizard_state():
            # Create a new WizardState instance
            logger.debug(f"Creating new WizardState for {self.wizard_name}")
            wizard_state = WizardState(self.wizard_name, self.steps, self.initial_state)
        else:
            # Use the existing WizardState instance
            logger.debug(f"Using existing WizardState for {self.wizard_name}")
            wizard_state = WizardState(self.wizard_name, self.steps, self.initial_state)

            # Validate the state to ensure it's not corrupted
            if not self.validate_wizard_state(wizard_state):
                # State is corrupted, reset it
                logger.warning(
                    f"Corrupted wizard state detected for {self.wizard_name}, resetting"
                )
                wizard_state.reset()
                # Re-initialize with default values
                for key, value in self.initial_state.items():
                    wizard_state.set(key, value)

        return wizard_state

    def has_wizard_state(self) -> bool:
        """Check if wizard state exists for this wizard.

        Returns:
            True if wizard state exists, False otherwise
        """
        key = f"{self.wizard_name}_current_step"
        return get_session_value(self.session_state, key) is not None

    def validate_wizard_state(self, wizard_state: WizardState) -> bool:
        """Validate the wizard state to ensure it's not corrupted.

        Args:
            wizard_state: The WizardState instance to validate

        Returns:
            True if the state is valid, False otherwise
        """
        # Get the expected keys for this wizard
        expected_keys = list(self.initial_state.keys()) + [
            "current_step",
            "total_steps",
            "completed",
        ]

        # Check if all expected keys are present with valid values
        for key in expected_keys:
            # Use a sentinel value to check if the key exists
            sentinel = object()
            value = wizard_state.get(key, sentinel)

            if value is sentinel:
                logger.warning(
                    f"Missing expected key '{key}' in wizard state for {self.wizard_name}"
                )
                return False

        # Check if current_step is within valid range
        current_step = wizard_state.get_current_step()
        total_steps = wizard_state.get_total_steps()

        if current_step < 1 or current_step > total_steps:
            logger.warning(
                f"Invalid current_step value {current_step} for {self.wizard_name} "
                f"(valid range: 1-{total_steps})"
            )
            return False

        # Check if total_steps matches expected value
        if total_steps != self.steps:
            logger.warning(
                f"Mismatched total_steps value {total_steps} for {self.wizard_name} "
                f"(expected: {self.steps})"
            )
            return False

        return True

    def reset_wizard_state(self) -> bool:
        """Reset the wizard state to initial values.

        Returns:
            True if the state was reset successfully, False otherwise
        """
        try:
            wizard_state = self.get_wizard_state()
            wizard_state.reset()
            logger.debug(f"Reset wizard state for {self.wizard_name}")
            return True
        except Exception as e:
            logger.error(
                f"Error resetting wizard state for {self.wizard_name}: {str(e)}"
            )
            return False

    def get_current_step(self) -> int:
        """Get the current step of the wizard.

        Returns:
            The current step number (1-based)
        """
        wizard_state = self.get_wizard_state()
        return wizard_state.get_current_step()

    def go_to_step(self, step: int) -> bool:
        """Go to a specific step in the wizard.

        Args:
            step: The step number to go to (1-based)

        Returns:
            True if the step was changed successfully, False otherwise
        """
        wizard_state = self.get_wizard_state()
        return wizard_state.go_to_step(step)

    def next_step(self) -> bool:
        """Move to the next step in the wizard.

        Returns:
            True if the step was changed successfully, False otherwise
        """
        wizard_state = self.get_wizard_state()
        return wizard_state.next_step()

    def previous_step(self) -> bool:
        """Move to the previous step in the wizard.

        Returns:
            True if the step was changed successfully, False otherwise
        """
        wizard_state = self.get_wizard_state()
        return wizard_state.previous_step()

    def set_completed(self, completed: bool = True) -> bool:
        """Set the completion status of the wizard.

        Args:
            completed: Whether the wizard is completed

        Returns:
            True if the status was set successfully, False otherwise
        """
        wizard_state = self.get_wizard_state()
        return wizard_state.set_completed(completed)

    def is_completed(self) -> bool:
        """Check if the wizard is completed.

        Returns:
            True if the wizard is completed, False otherwise
        """
        wizard_state = self.get_wizard_state()
        return wizard_state.is_completed()

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the wizard state.

        Args:
            key: The key to retrieve
            default: The default value to return if the key is not found

        Returns:
            The value from the wizard state or the default value
        """
        wizard_state = self.get_wizard_state()
        value = wizard_state.get(key, default)
        if key == "priority":
            try:
                cfg = get_project_config(Path("."))
                cfg.priority = value
                save_config(cfg, use_pyproject=False)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(
                    "Error persisting priority for %s: %s", self.wizard_name, str(exc)
                )
        return value

    def set_value(self, key: str, value: Any) -> bool:
        """Set a value in the wizard state.

        Args:
            key: The key to set
            value: The value to set

        Returns:
            True if the value was set successfully, False otherwise
        """
        wizard_state = self.get_wizard_state()
        return wizard_state.set(key, value)

    def clear_temporary_state(self, keys: Sequence[str] | None = None) -> None:
        """Clear temporary session state values used by the wizard.

        Streamlit widgets store their values in ``st.session_state`` using
        widget keys. These values are not managed by :class:`WizardState`
        directly and can leak between runs if left behind. This helper removes
        such keys after the wizard completes or is cancelled.

        Args:
            keys: Optional iterable of session state keys to remove. If ``None``
                or empty, the method performs no action.
        """
        if not keys:
            return

        for key in keys:
            try:
                if key in self.session_state:
                    del self.session_state[key]
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(
                    "Error clearing temporary state '%s' for %s: %s",
                    key,
                    self.wizard_name,
                    str(exc),
                )
            try:
                delattr(self.session_state, key)
            except Exception:
                # session_state may be a dict that doesn't support attribute access
                pass
