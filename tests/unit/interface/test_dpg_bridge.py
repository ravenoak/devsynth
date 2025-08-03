import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


def _setup_dpg(monkeypatch, *, input_text="", click_button=None):
    """Set up a stubbed dearpygui module."""
    dpg_pkg = ModuleType("dearpygui")
    dpg_mod = ModuleType("dearpygui.dearpygui")

    dpg_mod.is_viewport_created = MagicMock(return_value=True)

    class _Window:
        def __enter__(self):
            return "win"

        def __exit__(self, exc_type, exc, tb):
            return False

    dpg_mod.window = MagicMock(return_value=_Window())

    stored = {"value": input_text}

    def add_input_text(**_kwargs):
        return "input"

    dpg_mod.add_input_text = add_input_text

    def get_value(_id):
        return stored["value"]

    dpg_mod.get_value = get_value

    def add_button(label, callback, **_kwargs):
        if click_button == label:
            callback()
        return MagicMock()

    dpg_mod.add_button = add_button
    dpg_mod.add_text = MagicMock()
    dpg_mod.add_progress_bar = MagicMock(return_value="bar")
    dpg_mod.set_item_label = MagicMock()
    dpg_mod.set_value = MagicMock()
    dpg_mod.render_dearpygui_frame = MagicMock()
    dpg_mod.delete_item = MagicMock()

    dpg_pkg.dearpygui = dpg_mod
    monkeypatch.setitem(sys.modules, "dearpygui", dpg_pkg)
    monkeypatch.setitem(sys.modules, "dearpygui.dearpygui", dpg_mod)

    # Reload bridge to use stub
    import devsynth.interface.dpg_bridge as bridge_module

    importlib.reload(bridge_module)
    return bridge_module, dpg_mod


@pytest.mark.medium
def test_ask_question_returns_string(monkeypatch):
    """ask_question returns string responses."""
    bridge_module, dpg_mod = _setup_dpg(
        monkeypatch, input_text="hello", click_button="Submit"
    )
    monkeypatch.setattr(
        bridge_module.DearPyGUIBridge,
        "_event_loop",
        staticmethod(lambda condition: None),
    )
    bridge = bridge_module.DearPyGUIBridge()
    assert bridge.ask_question("msg") == "hello"


@pytest.mark.medium
@pytest.mark.parametrize("click_label, expected", [("Yes", True), ("No", False)])
def test_confirm_choice_returns_boolean(monkeypatch, click_label, expected):
    """confirm_choice yields booleans."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch, click_button=click_label)
    monkeypatch.setattr(
        bridge_module.DearPyGUIBridge,
        "_event_loop",
        staticmethod(lambda condition: None),
    )
    bridge = bridge_module.DearPyGUIBridge()
    assert bridge.confirm_choice("msg") is expected


@pytest.mark.medium
def test_display_result_sanitizes_output(monkeypatch):
    """display_result sanitizes output before showing."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch, click_button="OK")
    monkeypatch.setattr(
        bridge_module.DearPyGUIBridge,
        "_event_loop",
        staticmethod(lambda condition: None),
    )
    bridge = bridge_module.DearPyGUIBridge()
    bridge.display_result("<script>")
    called_arg = dpg_mod.add_text.call_args[0][0]
    assert "<" not in called_arg and ">" not in called_arg


@pytest.mark.medium
def test_create_progress_returns_indicator(monkeypatch):
    """create_progress returns a ProgressIndicator."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch)
    bridge = bridge_module.DearPyGUIBridge()
    indicator = bridge.create_progress("desc")
    from devsynth.interface.ux_bridge import ProgressIndicator

    assert isinstance(indicator, ProgressIndicator)
