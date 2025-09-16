from __future__ import annotations

from unittest.mock import MagicMock, mock_open, patch

import pytest

from devsynth.interface.webui.rendering import ProjectSetupPages

pytestmark = [pytest.mark.requires_resource("webui"), pytest.mark.fast]


class DummyProjectPages(ProjectSetupPages):
    """Lightweight harness for exercising rendering helpers."""

    def __init__(self, st):
        self.streamlit = st
        self.messages: list[str] = []

    def display_result(self, message: str, **_kwargs: object) -> None:
        self.messages.append(message)


def test_validate_requirements_step_requires_fields() -> None:
    """ReqID: FR-217 enforce required inputs for each wizard step."""

    ui = DummyProjectPages(MagicMock())
    state: dict[str, str] = {}

    assert not ui._validate_requirements_step(state, 1)
    state["title"] = "T"
    assert ui._validate_requirements_step(state, 1)

    assert not ui._validate_requirements_step(state, 2)
    state["description"] = "D"
    assert ui._validate_requirements_step(state, 2)

    assert not ui._validate_requirements_step(state, 3)
    state["type"] = "functional"
    assert ui._validate_requirements_step(state, 3)

    assert not ui._validate_requirements_step(state, 4)
    state["priority"] = "medium"
    assert ui._validate_requirements_step(state, 4)


def test_handle_requirements_navigation_cancel_clears_state() -> None:
    """ReqID: FR-218 canceling the wizard resets stored progress."""

    st = MagicMock()
    cancel_column = MagicMock()
    cancel_column.button.return_value = True
    st.columns.return_value = (
        MagicMock(button=MagicMock(return_value=False)),
        MagicMock(button=MagicMock(return_value=False)),
        cancel_column,
    )
    ui = DummyProjectPages(st)
    manager = MagicMock()
    manager.reset_wizard_state.return_value = True
    wizard_state = MagicMock()
    wizard_state.get_current_step.return_value = 3
    wizard_state.get_total_steps.return_value = 5

    result = ui._handle_requirements_navigation(
        manager, wizard_state, temp_keys=["title", "description"]
    )

    assert result is None
    manager.reset_wizard_state.assert_called_once()
    manager.clear_temporary_state.assert_called_once_with(["title", "description"])
    assert ui.messages == ["Requirements wizard cancelled"]


def test_save_requirements_clears_temporary_keys() -> None:
    """ReqID: FR-219 saving requirements persists and resets wizard state."""

    st = MagicMock()
    ui = DummyProjectPages(st)
    manager = MagicMock()
    manager.get_value.side_effect = lambda key, default=None: {
        "title": "Req",
        "description": "Desc",
        "type": "functional",
        "priority": "medium",
        "constraints": "a, b",
    }[key]
    manager.set_completed.return_value = True
    manager.reset_wizard_state.return_value = True
    temp_keys = ["k1", "k2"]

    with patch("builtins.open", mock_open()) as mock_file:
        result = ui._save_requirements(manager, temp_keys)

    mock_file.assert_called_once_with("requirements_wizard.json", "w", encoding="utf-8")
    assert result == {
        "title": "Req",
        "description": "Desc",
        "type": "functional",
        "priority": "medium",
        "constraints": ["a", "b"],
    }
    manager.clear_temporary_state.assert_called_once_with(temp_keys)
    assert any("Requirements saved" in message for message in ui.messages)
