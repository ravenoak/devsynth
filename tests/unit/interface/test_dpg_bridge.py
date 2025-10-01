import importlib
import os
import sys
import threading
import time
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# Gate Dear PyGui tests unless explicitly enabled

pytestmark = pytest.mark.skipif(
    os.getenv("DEVSYNTH_TEST_ALLOW_GUI", "").lower() not in {"1", "true", "yes"},
    reason="GUI tests are skipped unless DEVSYNTH_TEST_ALLOW_GUI is set",
)


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


@pytest.mark.parametrize("click_label, expected", [("Yes", True), ("No", False)])
@pytest.mark.medium
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


@pytest.mark.medium
def test_cancellable_progress_allows_cancel(monkeypatch):
    """Cancellable progress indicators expose cancellation state."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch, click_button="Cancel")
    bridge = bridge_module.DearPyGUIBridge()
    indicator = bridge.create_progress("desc", cancellable=True)
    assert indicator.is_cancelled()


@pytest.mark.medium
def test_run_cli_command_executes_and_polls(monkeypatch):
    """run_cli_command executes in background and polls the UI."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch)
    bridge = bridge_module.DearPyGUIBridge()

    def _cmd():
        import time

        time.sleep(0.01)
        return "done"

    result = bridge.run_cli_command(_cmd)
    assert result == "done"
    assert dpg_mod.render_dearpygui_frame.call_count >= 1


@pytest.mark.medium
def test_run_cli_command_handles_exception(monkeypatch):
    """Exceptions are reported via display_result."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch)
    bridge = bridge_module.DearPyGUIBridge()
    bridge.display_result = MagicMock()

    def _bad():
        raise ValueError("<boom>")

    bridge.run_cli_command(_bad)
    bridge.display_result.assert_called_once()
    (msg,) = bridge.display_result.call_args[0]
    kwargs = bridge.display_result.call_args[1]
    assert "<" not in msg and ">" not in msg
    assert kwargs["message_type"] == "error"


@pytest.mark.medium
def test_run_cli_command_cancellation(monkeypatch):
    """run_cli_command exits early when progress is cancelled."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch)

    cancel_event = threading.Event()
    release_event = threading.Event()

    class FakeProgress:
        def __init__(self) -> None:
            self.complete = MagicMock()

        def is_cancelled(self) -> bool:
            return cancel_event.is_set()

    progress = FakeProgress()
    monkeypatch.setattr(
        bridge_module.DearPyGUIBridge,
        "create_progress",
        lambda self, desc, cancellable=False: progress,
    )

    bridge = bridge_module.DearPyGUIBridge()

    def _cmd():
        release_event.wait()
        return "done"

    def _trigger_cancel():
        time.sleep(0.01)
        cancel_event.set()
        release_event.set()

    threading.Thread(target=_trigger_cancel).start()
    result = bridge.run_cli_command(_cmd, cancellable=True)
    assert result is None
    assert progress.complete.called
    assert dpg_mod.render_dearpygui_frame.call_count >= 1


@pytest.mark.medium
def test_run_cli_command_propagates_async_error(monkeypatch):
    """Errors raised in background threads are surfaced."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch)
    progress = MagicMock()
    progress.is_cancelled.return_value = False
    progress.complete = MagicMock()
    monkeypatch.setattr(
        bridge_module.DearPyGUIBridge,
        "create_progress",
        lambda self, desc, cancellable=False: progress,
    )
    bridge = bridge_module.DearPyGUIBridge()
    bridge.display_result = MagicMock()

    def _bad():
        time.sleep(0.01)
        raise RuntimeError("boom")

    result = bridge.run_cli_command(_bad)
    assert result is None
    bridge.display_result.assert_called_once()
    (msg,), kwargs = bridge.display_result.call_args
    assert "boom" in msg
    assert kwargs["message_type"] == "error"
    assert progress.complete.called


@pytest.mark.medium
def test_run_cli_command_progress_and_error_hooks(monkeypatch):
    """progress_hook and error_hook are utilised when provided."""
    bridge_module, dpg_mod = _setup_dpg(monkeypatch)
    bridge = bridge_module.DearPyGUIBridge()

    prog_calls: list[int] = []
    err: list[BaseException] = []

    def _hook(progress):
        prog_calls.append(1)

    def _err(exc):
        err.append(exc)

    def _bad():
        time.sleep(0.01)
        raise ValueError("boom")

    bridge.run_cli_command(
        _bad, progress_hook=_hook, error_hook=_err, message_type="custom"
    )
    assert prog_calls  # progress_hook called at least once
    assert err and isinstance(err[0], ValueError)
