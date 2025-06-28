from types import ModuleType
from unittest.mock import MagicMock
import importlib
import sys
import html
import re

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


def _setup_env(monkeypatch):
    cli_stub = ModuleType("devsynth.application.cli")

    def init_cmd(*, bridge):
        value = bridge.ask_question("val?")
        bridge.display_result(value)

    cli_stub.init_cmd = init_cmd
    for name in [
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
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.analyze_code_cmd",
        analyze_stub,
    )

    doctor_stub = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_stub.doctor_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.doctor_cmd",
        doctor_stub,
    )

    edrr_stub = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_stub.edrr_cycle_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.edrr_cycle_cmd",
        edrr_stub,
    )

    align_stub = ModuleType("devsynth.application.cli.commands.align_cmd")
    align_stub.align_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.align_cmd",
        align_stub,
    )

    st = ModuleType("streamlit")
    st.session_state = {}
    st.text_input = MagicMock(return_value="")
    st.selectbox = MagicMock(return_value="")
    st.checkbox = MagicMock(return_value=True)
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.progress = MagicMock()
    st.expander = lambda *_a, **_k: DummyForm()
    st.form = lambda *_a, **_k: DummyForm()
    st.form_submit_button = MagicMock(return_value=True)
    st.button = MagicMock(return_value=False)
    st.columns = MagicMock(
        return_value=(
            MagicMock(button=lambda *a, **k: False),
            MagicMock(button=lambda *a, **k: False),
        )
    )
    st.divider = MagicMock()
    st.spinner = DummyForm
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    return cli_stub.init_cmd, WebUI, st


def _sanitize(text: str) -> str:
    text = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    return html.escape(text.strip())


def test_bridge_consistency(monkeypatch):
    init_cmd, WebUI, st = _setup_env(monkeypatch)

    raw_input = "<script>alert(1)</script><b>demo</b>"
    expected = _sanitize(raw_input)

    out = MagicMock()
    monkeypatch.setattr("devsynth.interface.cli.Prompt.ask", lambda *a, **k: raw_input)
    monkeypatch.setattr("rich.console.Console.print", out)
    cli_bridge = CLIUXBridge()
    init_cmd(bridge=cli_bridge)
    cli_result = out.call_args.args[0]

    st.text_input.return_value = raw_input
    web_bridge = WebUI()
    init_cmd(bridge=web_bridge)
    web_result = st.write.call_args.args[0]

    api_bridge = APIBridge([raw_input])
    init_cmd(bridge=api_bridge)
    api_result = api_bridge.messages[0]

    assert cli_result == web_result == api_result == expected
