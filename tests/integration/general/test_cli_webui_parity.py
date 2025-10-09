import importlib
import sys
import time
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import ProgressIndicator


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
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())
    from devsynth.application import cli as cli_module

    monkeypatch.setattr(cli_module, "init_cmd", MagicMock())
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
    st.text_input = MagicMock(side_effect=["demo", "demo", "python", ""])
    st.text_area = MagicMock(return_value="demo goals")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.button = MagicMock(return_value=False)
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
    st.empty = MagicMock(return_value=MagicMock())
    monkeypatch.setitem(sys.modules, "streamlit", st)
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    return cli_module, webui.WebUI()


@pytest.mark.slow
def test_init_invocations_match_succeeds(parity_env):
    """Test that init invocations match succeeds.

    ReqID: N/A"""
    cli_module, webui_bridge = parity_env
    cli_bridge = CLIUXBridge()
    cli_module.init_cmd(
        path="demo",
        project_root="demo",
        language="python",
        goals=None,
        bridge=cli_bridge,
    )
    args_cli = cli_module.init_cmd.call_args_list[-1].kwargs
    cli_module.init_cmd.reset_mock()
    webui_bridge.onboarding_page()
    args_web = cli_module.init_cmd.call_args_list[-1].kwargs
    args_cli.pop("bridge", None)
    args_web.pop("bridge", None)
    assert args_cli == args_web


@pytest.mark.slow
def test_display_result_sanitization_succeeds(parity_env, monkeypatch):
    """Ensure CLI and WebUI bridges sanitize output consistently.

    ReqID: N/A"""
    _, webui_bridge = parity_env
    cli_bridge = CLIUXBridge()
    out_cli: list[str] = []
    monkeypatch.setattr(
        "rich.console.Console.print",
        lambda self, msg, *, highlight=False: out_cli.append(
            str(msg) if hasattr(msg, "__str__") else msg
        ),
    )
    st = sys.modules["streamlit"]
    out_web: list[str] = []
    st.write = MagicMock(
        side_effect=lambda msg: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    st.markdown = MagicMock(
        side_effect=lambda msg, **kwargs: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    st.info = MagicMock(
        side_effect=lambda msg: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    st.error = MagicMock(
        side_effect=lambda msg: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    st.warning = MagicMock(
        side_effect=lambda msg: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    st.success = MagicMock(
        side_effect=lambda msg: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    st.header = MagicMock(
        side_effect=lambda msg: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    st.subheader = MagicMock(
        side_effect=lambda msg: out_web.append(
            str(msg) if hasattr(msg, "__str__") else msg
        )
    )
    sample = "<script>bad</script>Hello"
    cli_bridge.display_result(sample)
    webui_bridge.display_result(sample)
    out_cli_str = [str(item) for item in out_cli]
    out_web_str = [str(item) for item in out_web]
    assert out_cli_str == out_web_str


@pytest.mark.slow
def test_progress_indicator_parity_succeeds(parity_env, monkeypatch):
    """Ensure CLI and WebUI bridges can create progress indicators with the same interface.

    ReqID: N/A"""
    _, webui_bridge = parity_env
    cli_bridge = CLIUXBridge()
    cli_progress = cli_bridge.create_progress("Test Progress", total=100)
    web_progress = webui_bridge.create_progress("Test Progress", total=100)
    assert isinstance(cli_progress, ProgressIndicator)
    assert isinstance(web_progress, ProgressIndicator)
    assert hasattr(cli_progress, "update")
    assert hasattr(web_progress, "update")
    assert hasattr(cli_progress, "complete")
    assert hasattr(web_progress, "complete")
