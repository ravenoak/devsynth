from types import ModuleType
from unittest.mock import MagicMock
import importlib
import sys

import pytest

from devsynth.interface.agentapi import APIBridge


class DummyForm:
    def __init__(self, submitted: bool = True) -> None:
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.fixture
def parity_env(monkeypatch):
    """Prepare a stub environment for CLI/WebUI parity tests."""

    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())

    # ------------------------------------------------------------------
    # CLI stubs
    # ------------------------------------------------------------------
    cli_stub = ModuleType("devsynth.application.cli")

    def init_cmd(path=".", project_root=None, language=None, goals=None, *, bridge):
        bridge.display_result(f"init:{path}")

    def spec_cmd(requirements_file="requirements.md", *, bridge):
        bridge.display_result(f"spec:{requirements_file}")

    def code_cmd(*, bridge):
        bridge.display_result("code")

    cli_stub.init_cmd = MagicMock(side_effect=init_cmd)
    cli_stub.spec_cmd = MagicMock(side_effect=spec_cmd)
    cli_stub.code_cmd = MagicMock(side_effect=code_cmd)

    # unused but required by imports
    for name in [
        "test_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())

    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    # ------------------------------------------------------------------
    # Doctor command stub uses a module level bridge
    # ------------------------------------------------------------------
    doctor_mod = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_mod.bridge = APIBridge()

    def doctor_cmd(config_dir: str = "config") -> None:
        doctor_mod.bridge.display_result(f"doctor:{config_dir}")

    doctor_mod.doctor_cmd = MagicMock(side_effect=doctor_cmd)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_mod
    )
    cli_stub.doctor_cmd = doctor_mod.doctor_cmd

    # Additional stub command modules required by the WebUI import
    analyze_mod = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_mod.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_code_cmd", analyze_mod
    )

    edrr_mod = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_mod.edrr_cycle_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_mod
    )

    align_mod = ModuleType("devsynth.application.cli.commands.align_cmd")
    align_mod.align_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.align_cmd", align_mod
    )

    # ------------------------------------------------------------------
    # Streamlit stub
    # ------------------------------------------------------------------
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Onboarding")
    st.sidebar.title = MagicMock()
    st.set_page_config = MagicMock()
    st.header = MagicMock()
    st.expander = lambda *_a, **_k: DummyForm(True)
    st.form = lambda *_a, **_k: DummyForm(True)
    st.form_submit_button = MagicMock(return_value=True)
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="desc")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.button = MagicMock(return_value=True)
    st.spinner = DummyForm
    st.divider = MagicMock()
    st.columns = MagicMock(
        return_value=(
            MagicMock(button=lambda *a, **k: False),
            MagicMock(button=lambda *a, **k: False),
        )
    )
    st.progress = MagicMock()
    st.write = MagicMock()
    st.markdown = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    # Import the WebUI after patching
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    monkeypatch.setattr(webui.WebUI, "_requirements_wizard", lambda self: None)
    monkeypatch.setattr(webui.WebUI, "_gather_wizard", lambda self: None)

    return {
        "cli": cli_stub,
        "doctor_mod": doctor_mod,
        "webui": webui,
        "st": st,
    }


# ----------------------------------------------------------------------
# Test cases
# ----------------------------------------------------------------------

def _capture_webui_messages(webui_cls, bridge, st):
    ui = webui_cls.WebUI()
    ui.display_result = lambda msg, highlight=False: bridge.display_result(msg, highlight=highlight)
    ui.create_progress = lambda desc, total=100: bridge.create_progress(desc, total=total)
    return ui


def test_init_parity(parity_env):
    cli = parity_env["cli"]
    webui = parity_env["webui"]
    st = parity_env["st"]

    # CLI invocation
    bridge_cli = APIBridge()
    cli.init_cmd(path="demo", bridge=bridge_cli)
    cli_messages = list(bridge_cli.messages)

    # WebUI invocation
    bridge_web = APIBridge()
    st.text_input.side_effect = ["demo", "demo", "python", ""]
    st.form_submit_button.return_value = True
    ui = _capture_webui_messages(webui, bridge_web, st)
    ui.onboarding_page()
    web_messages = list(bridge_web.messages)

    assert cli_messages == web_messages


def test_spec_parity(parity_env):
    cli = parity_env["cli"]
    webui = parity_env["webui"]
    st = parity_env["st"]

    bridge_cli = APIBridge()
    cli.spec_cmd(requirements_file="requirements.md", bridge=bridge_cli)
    cli_messages = list(bridge_cli.messages)

    bridge_web = APIBridge()
    st.text_input.side_effect = ["requirements.md", "requirements.md", "specs.md"]
    st.form_submit_button.side_effect = [True, False]
    st.button.side_effect = [False, False]
    st.sidebar.radio.return_value = "Requirements"
    ui = _capture_webui_messages(webui, bridge_web, st)
    ui.requirements_page()
    web_messages = list(bridge_web.messages)

    assert cli_messages == web_messages


def test_code_parity(parity_env):
    cli = parity_env["cli"]
    webui = parity_env["webui"]
    st = parity_env["st"]

    bridge_cli = APIBridge()
    cli.code_cmd(bridge=bridge_cli)
    cli_messages = list(bridge_cli.messages)

    bridge_web = APIBridge()
    st.text_input.side_effect = ["specs.md"]
    st.form_submit_button.return_value = False
    st.button.side_effect = [True, False]
    st.sidebar.radio.return_value = "Synthesis"
    ui = _capture_webui_messages(webui, bridge_web, st)
    ui.synthesis_page()
    web_messages = list(bridge_web.messages)

    assert cli_messages == web_messages


def test_doctor_parity(parity_env):
    cli = parity_env["cli"]
    webui = parity_env["webui"]
    doctor_mod = parity_env["doctor_mod"]
    st = parity_env["st"]

    bridge_cli = APIBridge()
    doctor_mod.bridge = bridge_cli
    doctor_mod.doctor_cmd("config")
    cli_messages = list(bridge_cli.messages)

    bridge_web = APIBridge()
    doctor_mod.bridge = bridge_web
    ui = _capture_webui_messages(webui, bridge_web, st)
    ui.doctor_page()
    web_messages = list(bridge_web.messages)

    assert cli_messages == web_messages
