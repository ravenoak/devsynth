"""Fast tests for WebUI bridge wizard navigation and progress behavior."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from devsynth.interface import webui_bridge

pytestmark = pytest.mark.fast


class _StreamlitBridgeStub:
    def __init__(self) -> None:
        self.write_messages: list[str] = []
        self.success_messages: list[str] = []
        self.warning_messages: list[str] = []
        self.error_messages: list[str] = []
        self.info_messages: list[str] = []
        self.session_state: object | None = SimpleNamespace()

    def write(self, message: str) -> None:
        self.write_messages.append(message)

    def success(self, message: str) -> None:
        self.success_messages.append(message)

    def warning(self, message: str) -> None:  # pragma: no cover - defensive logging
        self.warning_messages.append(message)

    def error(self, message: str) -> None:  # pragma: no cover - defensive logging
        self.error_messages.append(message)

    def info(self, message: str) -> None:
        self.info_messages.append(message)


@pytest.fixture()
def bridge_streamlit_stub(monkeypatch: pytest.MonkeyPatch) -> _StreamlitBridgeStub:
    stub = _StreamlitBridgeStub()
    monkeypatch.setattr(webui_bridge, "st", stub, raising=False)
    monkeypatch.setattr(webui_bridge, "_require_streamlit", lambda: None)
    return stub


def test_progress_indicator_nested_completion_and_sanitization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_sanitize(text: str) -> str:
        if "danger" in text:
            raise ValueError("boom")
        return text.replace("<", "&lt;").replace(">", "&gt;")

    monkeypatch.setattr(webui_bridge, "sanitize_output", fake_sanitize)

    indicator = webui_bridge.WebUIProgressIndicator("Main", total=4)
    subtask_id = indicator.add_subtask("<subtask>", total=2)

    subtask = indicator._subtasks[subtask_id]
    assert subtask.description == "&lt;subtask&gt;"
    assert subtask.status == "Starting..."

    nested_id = indicator.add_nested_subtask(subtask_id, "<nested>")
    nested = subtask.nested_subtasks[nested_id]
    assert nested.description == "&lt;nested&gt;"

    indicator.update_nested_subtask(
        subtask_id,
        nested_id,
        advance=0.5,
        description="<danger>",
        status="<danger>",
    )

    assert nested.description == "&lt;nested&gt;"
    assert nested.status == "Starting..."
    assert pytest.approx(nested.current, rel=1e-3) == 0.5

    indicator.complete_subtask(subtask_id)

    assert subtask.completed is True
    assert nested.completed is True
    assert nested.status == "Complete"


def test_wizard_navigation_and_display_fallback(
    bridge_streamlit_stub: _StreamlitBridgeStub, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = webui_bridge.WebUIBridge()
    monkeypatch.setattr(
        webui_bridge.WebUIBridge,
        "_format_for_output",
        lambda self, message, **_: webui_bridge.sanitize_output(message),
    )

    assert (
        webui_bridge.WebUIBridge.adjust_wizard_step(0, direction="next", total=3) == 1
    )
    assert (
        webui_bridge.WebUIBridge.adjust_wizard_step(2, direction="next", total=3) == 2
    )
    assert (
        webui_bridge.WebUIBridge.adjust_wizard_step("1", direction="back", total=0) == 0
    )
    assert (
        webui_bridge.WebUIBridge.adjust_wizard_step(5, direction="sideways", total=2)
        == 1
    )

    assert webui_bridge.WebUIBridge.normalize_wizard_step("2", total=3) == 2
    assert webui_bridge.WebUIBridge.normalize_wizard_step(None, total=2) == 0
    assert webui_bridge.WebUIBridge.normalize_wizard_step(5, total=2) == 1
    assert webui_bridge.WebUIBridge.normalize_wizard_step(-1, total=2) == 0

    bridge.display_result("<highlight>", highlight=True)
    assert bridge_streamlit_stub.info_messages == ["&lt;highlight&gt;"]
    assert bridge.messages == ["&lt;highlight&gt;"]
    assert bridge_streamlit_stub.write_messages == []


def test_default_status_thresholds() -> None:
    assert webui_bridge._default_status(0, 10) == "Starting..."
    assert webui_bridge._default_status(3, 10) == "Processing..."
    assert webui_bridge._default_status(5, 10) == "Halfway there..."
    assert webui_bridge._default_status(8, 10) == "Almost done..."
    assert webui_bridge._default_status(10, 10) == "Complete"
    assert webui_bridge._default_status(9.9, 10) == "Finalizing..."
    assert webui_bridge._default_status(1, 0) == "Complete"


def test_progress_indicator_updates_and_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        webui_bridge,
        "sanitize_output",
        lambda value: value.replace("<", "&lt;").replace(">", "&gt;"),
    )

    indicator = webui_bridge.WebUIProgressIndicator("Task", total=4)
    indicator.update(description="<phase>")
    assert indicator._description == "&lt;phase&gt;"
    assert indicator._status == "Starting..."

    indicator.update(status="<custom>", advance=0)
    assert indicator._status == "&lt;custom&gt;"

    subtask_id = indicator.add_subtask("<sub>", total=2)
    indicator.update_subtask(subtask_id, advance=1, description="<detail>")
    subtask = indicator._subtasks[subtask_id]
    assert subtask.description == "&lt;detail&gt;"
    assert subtask.status == "Halfway there..."

    indicator.complete_subtask(subtask_id)
    assert subtask.completed is True
    assert subtask.status == "Complete"

    indicator.complete()
    assert indicator._current == indicator._total


def test_nested_subtask_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(webui_bridge, "sanitize_output", lambda value: value)

    indicator = webui_bridge.WebUIProgressIndicator("Task", total=3)
    parent_id = indicator.add_subtask("parent", total=2)
    missing_nested = indicator.add_nested_subtask("missing", "child")
    assert missing_nested == ""

    nested_id = indicator.add_nested_subtask(parent_id, "child", total=2)
    indicator.update_nested_subtask(parent_id, nested_id, advance=1)
    nested = indicator._subtasks[parent_id].nested_subtasks[nested_id]
    assert nested.status == "Starting..."

    indicator.complete_nested_subtask(parent_id, nested_id)
    assert nested.completed is True
    assert nested.status == "Complete"

    indicator.complete_subtask(parent_id)
    assert indicator._subtasks[parent_id].completed is True

    indicator.update_nested_subtask("missing", nested_id)
    indicator.complete_nested_subtask("missing", nested_id)


def test_display_result_routes_by_type(
    bridge_streamlit_stub: _StreamlitBridgeStub, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = webui_bridge.WebUIBridge()
    monkeypatch.setattr(
        webui_bridge.WebUIBridge,
        "_format_for_output",
        lambda self, message, **_: webui_bridge.sanitize_output(message),
    )

    bridge.display_result("<err>", message_type="error")
    assert bridge_streamlit_stub.error_messages[-1] == "&lt;err&gt;"

    bridge.display_result("<warn>", message_type="warning")
    assert bridge_streamlit_stub.warning_messages[-1] == "&lt;warn&gt;"

    bridge.display_result("<ok>", message_type="success")
    assert bridge_streamlit_stub.success_messages[-1] == "&lt;ok&gt;"

    bridge.display_result("<info>", message_type="info")
    assert bridge_streamlit_stub.info_messages[-1] == "&lt;info&gt;"

    bridge.display_result("<highlight>", highlight=True)
    assert bridge_streamlit_stub.info_messages[-1] == "&lt;highlight&gt;"

    bridge.display_result("<plain>")
    assert bridge_streamlit_stub.write_messages[-1] == "&lt;plain&gt;"
    assert bridge.messages[-1] == "&lt;plain&gt;"


def test_get_wizard_manager_and_create(monkeypatch: pytest.MonkeyPatch) -> None:
    bridge = webui_bridge.WebUIBridge()

    stub = _StreamlitBridgeStub()
    monkeypatch.setattr(webui_bridge, "st", stub, raising=False)
    monkeypatch.setattr(webui_bridge, "_require_streamlit", lambda: None)

    captured: dict[str, object] = {}
    original_create = webui_bridge.WebUIBridge.create_wizard_manager

    def fake_create(session_state, wizard_name, *, steps, initial_state=None):
        captured.update(
            {
                "session_state": session_state,
                "wizard_name": wizard_name,
                "steps": steps,
                "initial_state": initial_state,
            }
        )
        return "manager"

    monkeypatch.setattr(
        webui_bridge.WebUIBridge,
        "create_wizard_manager",
        staticmethod(fake_create),
    )

    manager = bridge.get_wizard_manager("wizard", steps=3, initial_state={"x": 1})
    assert manager == "manager"
    assert captured["session_state"] is stub.session_state
    assert captured["wizard_name"] == "wizard"

    stub.session_state = None
    with pytest.raises(webui_bridge.DevSynthError):
        bridge.get_wizard_manager("wizard", steps=1)

    monkeypatch.setattr(
        webui_bridge.WebUIBridge,
        "create_wizard_manager",
        staticmethod(original_create),
    )

    dummy_module = SimpleNamespace(
        WizardStateManager=lambda session_state, name, steps, initial_state: {
            "session_state": session_state,
            "name": name,
            "steps": steps,
            "initial_state": initial_state,
        }
    )
    monkeypatch.setitem(
        sys.modules,
        "devsynth.interface.wizard_state_manager",
        dummy_module,
    )

    result = webui_bridge.WebUIBridge.create_wizard_manager(
        SimpleNamespace(), "wiz", steps=2, initial_state={"a": 2}
    )
    assert result["name"] == "wiz"

    with pytest.raises(webui_bridge.DevSynthError):
        webui_bridge.WebUIBridge.create_wizard_manager(None, "wiz", steps=1)
