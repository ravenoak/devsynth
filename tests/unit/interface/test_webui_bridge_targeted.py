"""Additional coverage for :mod:`devsynth.interface.webui_bridge`."""

from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.fast


@pytest.fixture
def bridge_under_test(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Reload bridge module with a feature-complete Streamlit double."""

    from tests.fixtures.streamlit_mocks import make_streamlit_mock

    fake_streamlit = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    import devsynth.interface.webui_bridge as bridge

    module = importlib.reload(bridge)
    return SimpleNamespace(module=module, streamlit=fake_streamlit)


def test_adjust_wizard_step_invalid_direction_keeps_bounds(
    bridge_under_test: SimpleNamespace, caplog: pytest.LogCaptureFixture
) -> None:
    """Unknown directions clamp to valid range and emit a warning.

    ReqID: coverage-webui-bridge
    """

    bridge = bridge_under_test.module

    with caplog.at_level("WARNING"):
        step = bridge.WebUIBridge.adjust_wizard_step(2, direction="sideways", total=3)

    assert step == 2
    assert any("Invalid direction" in message for message in caplog.messages)


def test_normalize_wizard_step_handles_strings(
    bridge_under_test: SimpleNamespace,
) -> None:
    """String inputs and floats are coerced to bounded indices.

    ReqID: coverage-webui-bridge
    """

    bridge = bridge_under_test.module
    normalize = bridge.WebUIBridge.normalize_wizard_step

    assert normalize("2", total=5) == 2
    assert normalize("7.9", total=6) == 5
    assert normalize("", total=4) == 0


def test_question_and_confirmation_defaults(bridge_under_test: SimpleNamespace) -> None:
    """Question helpers return default values without invoking Streamlit widgets.

    ReqID: coverage-webui-bridge
    """

    bridge = bridge_under_test.module
    ui = bridge.WebUIBridge()

    assert ui.ask_question("Prompt", default="fallback") == "fallback"
    assert ui.confirm_choice("Sure?", default=True) is True


def test_display_result_highlight_routes_to_info(
    bridge_under_test: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Highlight flag prefers ``st.info`` regardless of message type.

    ReqID: coverage-webui-bridge
    """

    bridge = bridge_under_test.module
    monkeypatch.setattr(bridge, "sanitize_output", lambda value: value)
    ui = bridge.WebUIBridge()

    bridge_under_test.streamlit.info.reset_mock()
    ui.display_result("Important", highlight=True)

    bridge_under_test.streamlit.info.assert_called_once()
    assert bridge_under_test.streamlit.info.call_args[0][0] is ui.messages[-1]


def test_create_progress_cycles_statuses(
    bridge_under_test: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Progress indicator transitions through documented status text.

    ReqID: coverage-webui-bridge
    """

    bridge = bridge_under_test.module
    monkeypatch.setattr(bridge, "sanitize_output", lambda value: value)
    indicator = bridge.WebUIBridge().create_progress("Task", total=100)

    checkpoints = [
        (0, "Starting..."),
        (24, "Starting..."),
        (25, "Processing..."),
        (50, "Halfway there..."),
        (75, "Almost done..."),
        (99, "Finalizing..."),
        (100, "Complete"),
    ]

    for current, expected in checkpoints:
        indicator._current = current
        indicator.update(advance=0)
        assert indicator._status == expected


def test_session_helpers_delegate_to_state_access(
    monkeypatch: pytest.MonkeyPatch, bridge_under_test: SimpleNamespace
) -> None:
    """Session wrappers call the state access module consistently.

    ReqID: coverage-webui-bridge
    """

    bridge = bridge_under_test.module
    captured = {}

    def fake_get(session, key, default=None):  # noqa: ANN001
        captured["get"] = (session, key, default)
        return "value"

    def fake_set(session, key, value):  # noqa: ANN001
        captured.setdefault("set", []).append((session, key, value))
        return True

    monkeypatch.setattr(bridge, "_get_session_value", fake_get)
    monkeypatch.setattr(bridge, "_set_session_value", fake_set)

    data = {}
    assert bridge.WebUIBridge.get_session_value(data, "key", default=1) == "value"
    assert captured["get"] == (data, "key", 1)

    assert bridge.WebUIBridge.set_session_value(data, "key", 2) is True
    assert captured["set"] == [(data, "key", 2)]


def test_get_wizard_manager_persists_state(
    bridge_under_test: SimpleNamespace,
) -> None:
    """Wizard managers reuse the same Streamlit-backed session state.

    ReqID: coverage-webui-bridge
    """

    bridge = bridge_under_test.module
    bridge_under_test.streamlit.session_state = {}
    ui = bridge.WebUIBridge()

    manager = ui.get_wizard_manager(
        "requirements", steps=3, initial_state={"title": "Draft"}
    )
    state = manager.get_wizard_state()
    assert state.get("title") == "Draft"

    state.set("title", "Final")

    refreshed = ui.get_wizard_state(
        "requirements", steps=3, initial_state={"title": "Placeholder"}
    )
    assert refreshed.get("title") == "Final"


def test_get_wizard_manager_requires_session_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Accessing wizard helpers without session_state raises ``DevSynthError``.

    ReqID: coverage-webui-bridge
    """

    from types import ModuleType

    stub = ModuleType("streamlit")
    stub.session_state = None  # type: ignore[assignment]
    monkeypatch.setitem(sys.modules, "streamlit", stub)

    import importlib

    import devsynth.interface.webui_bridge as bridge

    module = importlib.reload(bridge)
    ui = module.WebUIBridge()

    with pytest.raises(bridge.DevSynthError):
        ui.get_wizard_manager("req", steps=1)
