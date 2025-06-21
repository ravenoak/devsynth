import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.agentapi import APIBridge


class DummyForm:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return True


class DummyProgress:
    def __init__(self, *args, **kwargs):
        self.updated = False
        self.completed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.complete()
        return False

    def update(self, *args, **kwargs):
        self.updated = True

    def complete(self):
        self.completed = True


# ---------------------------------------------------------------------------
# Bridge factory helpers
# ---------------------------------------------------------------------------

def _cli_bridge(monkeypatch):
    ask = MagicMock(return_value="foo")
    confirm = MagicMock(return_value=True)
    out = MagicMock()
    monkeypatch.setattr("devsynth.interface.cli.Prompt.ask", ask)
    monkeypatch.setattr("devsynth.interface.cli.Confirm.ask", confirm)
    monkeypatch.setattr("rich.console.Console.print", out)
    monkeypatch.setattr("devsynth.interface.cli.CLIProgressIndicator", DummyProgress)
    return CLIUXBridge(), {"ask": ask, "confirm": confirm, "out": out}


def _web_bridge(monkeypatch):
    st = ModuleType("streamlit")
    st.session_state = {}
    st.text_input = MagicMock(return_value="foo")
    st.selectbox = MagicMock(return_value="foo")
    st.checkbox = MagicMock(return_value=True)
    st.write = MagicMock()
    st.markdown = MagicMock()
    prog = MagicMock()
    st.progress = MagicMock(return_value=prog)
    st.expander = lambda *_a, **_k: DummyForm()
    st.form = lambda *_a, **_k: DummyForm()
    st.form_submit_button = MagicMock(return_value=True)
    st.button = MagicMock(return_value=False)
    st.columns = MagicMock(return_value=(MagicMock(button=lambda *a, **k: False), MagicMock(button=lambda *a, **k: False)))
    st.divider = MagicMock()
    st.spinner = DummyForm
    monkeypatch.setitem(sys.modules, "streamlit", st)

    cli_stub = ModuleType("devsynth.application.cli")
    for name in [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    analyze_stub = ModuleType("devsynth.application.cli.commands.analyze_code_cmd")
    analyze_stub.analyze_code_cmd = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.commands.analyze_code_cmd", analyze_stub)

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    return WebUI(), {"write": st.write, "markdown": st.markdown, "progress": prog}


def _api_bridge(monkeypatch):
    return APIBridge(["foo", True]), {}


# ---------------------------------------------------------------------------
# Shared contract tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("factory", [_cli_bridge, _web_bridge, _api_bridge])
def test_bridge_contract(factory, monkeypatch):
    bridge, trackers = factory(monkeypatch)

    assert bridge.ask_question("q", choices=["x"], default="x") == "foo"
    assert bridge.confirm_choice("ok?", default=True) is True

    bridge.display_result("done", highlight=True)
    if "out" in trackers:
        trackers["out"].assert_called_once_with("done", highlight=True)
    if "markdown" in trackers:
        trackers["markdown"].assert_called_once_with("**done**")

    prog = bridge.create_progress("step", total=2)
    prog.update()
    prog.complete()
    with bridge.create_progress("ctx") as ctx_prog:
        ctx_prog.update()
        ctx_prog.complete()

    if isinstance(bridge, APIBridge):
        assert trackers == {}
        assert "step complete" in bridge.messages
        assert "ctx complete" in bridge.messages
