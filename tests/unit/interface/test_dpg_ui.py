from types import SimpleNamespace
from unittest.mock import MagicMock

import sys

import devsynth.interface.dpg_ui as dpg_ui


def test_run_buttons_call_commands(monkeypatch):
    """Buttons invoke corresponding workflow commands."""

    fake_dpg = MagicMock()
    fake_dpg.window.return_value.__enter__.return_value = None
    fake_dpg.is_dearpygui_running.side_effect = [False]
    monkeypatch.setattr(dpg_ui, "dpg", fake_dpg)
    monkeypatch.setattr(dpg_ui, "DearPyGUIBridge", MagicMock)

    init = MagicMock()
    gather = MagicMock()
    inspect = MagicMock()
    fake_cli = SimpleNamespace(init_cmd=init, gather_cmd=gather, inspect_cmd=inspect)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", fake_cli)

    dpg_ui.run()

    callbacks = [call.kwargs["callback"] for call in fake_dpg.add_button.call_args_list]
    for cb, func in zip(callbacks, [init, gather, inspect]):
        cb()
        func.assert_called_once()
