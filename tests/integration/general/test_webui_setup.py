import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.requires_resource("webui")


def _setup_streamlit(monkeypatch, button_return=False, toggle_return=False):
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
    st.form_submit_button = MagicMock(return_value=False)
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="text")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=False)
    st.toggle = MagicMock(return_value=toggle_return)
    st.button = MagicMock(return_value=button_return)
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
    st.error = MagicMock()
    st.info = MagicMock()
    st.success = MagicMock()
    st.warning = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    modules = [
        "langgraph",
        "langgraph.checkpoint",
        "langgraph.checkpoint.base",
        "langgraph.graph",
        "langchain",
        "langchain_openai",
        "langchain_community",
        "tiktoken",
        "tinydb",
        "tinydb.storages",
        "tinydb.middlewares",
        "duckdb",
        "lmdb",
        "faiss",
        "httpx",
        "lmstudio",
        "openai",
        "openai.types",
        "openai.types.chat",
        "torch",
        "transformers",
        "astor",
    ]
    for name in modules:
        module = ModuleType(name)
        if name == "langgraph.checkpoint.base":
            module.BaseCheckpointSaver = object
            module.empty_checkpoint = object()
        if name == "langgraph.graph":
            module.END = None
            module.StateGraph = object
        if name == "tinydb":
            module.TinyDB = object
            module.Query = object
        if name == "tinydb.storages":
            module.JSONStorage = object
            module.MemoryStorage = object
        if name == "tinydb.middlewares":
            module.CachingMiddleware = object
        if name == "openai":
            module.OpenAI = object
            module.AsyncOpenAI = object
        if name == "openai.types.chat":
            module.ChatCompletion = object
            module.ChatCompletionChunk = object
        if name == "transformers":
            module.AutoModelForCausalLM = object
            module.AutoTokenizer = object
        if name == "httpx":
            module.RequestError = Exception
            module.HTTPStatusError = Exception
        monkeypatch.setitem(sys.modules, name, module)
    return st


class DummyForm:

    def __init__(self, submitted: bool = True) -> None:
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.mark.medium
def test_guided_setup_button_invokes_wizard_succeeds(monkeypatch):
    """Test that guided setup button invokes wizard succeeds.

    ReqID: N/A"""
    st = _setup_streamlit(monkeypatch, button_return=True)
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    mock_run = MagicMock()
    monkeypatch.setattr(
        webui, "SetupWizard", MagicMock(return_value=MagicMock(run=mock_run))
    )
    webui.WebUI().onboarding_page()
    assert mock_run.called


@pytest.mark.medium
def test_offline_toggle_saves_config_succeeds(monkeypatch, tmp_path):
    """Test that offline toggle saves config succeeds.

    ReqID: N/A"""
    st = _setup_streamlit(monkeypatch, button_return=True, toggle_return=True)
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.config import ConfigModel, ProjectUnifiedConfig

    cfg = ProjectUnifiedConfig(
        ConfigModel(project_root=str(tmp_path)), tmp_path / "project.yaml", False
    )
    monkeypatch.setattr(webui, "load_project_config", lambda: cfg)
    saved = {}
    monkeypatch.setattr(
        webui,
        "save_config",
        lambda conf, *, use_pyproject, path: saved.update(
            {"offline": conf.offline_mode}
        ),
    )
    webui.WebUI().config_page()
    assert saved.get("offline") is True


@pytest.mark.medium
def test_webui_bridge_error_display_succeeds(monkeypatch):
    """WebUIBridge displays errors via st.error."""
    st = _setup_streamlit(monkeypatch)
    from devsynth.interface import webui_bridge

    # Ensure WebUIBridge uses our stubbed streamlit module
    monkeypatch.setattr(webui_bridge, "st", st)
    bridge = webui_bridge.WebUIBridge()
    bridge.display_result("Failure", message_type="error")
    assert st.error.called
