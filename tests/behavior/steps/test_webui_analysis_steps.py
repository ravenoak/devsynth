import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "analysis.feature"))


@pytest.fixture
def webui_context(monkeypatch):
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Analysis")
    st.sidebar.title = MagicMock()
    st.sidebar.markdown = MagicMock()
    st.set_page_config = MagicMock()
    st.header = MagicMock()
    st.error = MagicMock()
    st.success = MagicMock()
    st.warning = MagicMock()
    st.info = MagicMock()
    st.expander = lambda *_a, **_k: DummyForm(True)
    st.form = lambda *_a, **_k: DummyForm(True)
    st.form_submit_button = MagicMock(return_value=True)
    st.text_input = MagicMock(return_value="text")
    st.text_area = MagicMock(return_value="desc")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.button = MagicMock(return_value=True)
    st.toggle = MagicMock(return_value=True)
    st.number_input = MagicMock(return_value=1)
    st.spinner = DummyForm
    st.divider = MagicMock()

    class _CompV1:
        @staticmethod
        def html(_html, **_kwargs):
            return None

    class _Components:
        v1 = _CompV1()

    st.components = _Components()
    # Create MagicMock objects for columns that can be configured during tests
    col1_mock = MagicMock()
    col1_mock.button = MagicMock(return_value=False)
    col2_mock = MagicMock()
    col2_mock.button = MagicMock(return_value=False)
    st.columns = MagicMock(return_value=(col1_mock, col2_mock))
    st.progress = MagicMock()
    st.write = MagicMock()
    st.markdown = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    # Stub optional dependencies used during WebUI import
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

    cli_stub = ModuleType("devsynth.application.cli")
    for name in [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
        "doctor_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    analyze_stub = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_stub.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_code_cmd", analyze_stub
    )
    cli_stub.inspect_code_cmd = analyze_stub.inspect_code_cmd

    from pathlib import Path

    from devsynth.config import ProjectUnifiedConfig
    from devsynth.config.loader import ConfigModel

    mock_config = ConfigModel(project_root="/mock/project/root", offline_mode=False)
    mock_project_config = ProjectUnifiedConfig(
        config=mock_config,
        path=Path("/mock/project/root/.devsynth/project.yaml"),
        use_pyproject=False,
    )

    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    import devsynth.interface.webui.rendering as rendering

    load_project_config_mock = MagicMock(return_value=mock_project_config)
    save_config_mock = MagicMock()

    monkeypatch.setattr(rendering, "load_project_config", load_project_config_mock)
    monkeypatch.setattr(rendering, "save_config", save_config_mock)
    webui.save_config = save_config_mock
    monkeypatch.setattr(webui.WebUI, "_requirements_wizard", lambda self: None)
    monkeypatch.setattr(webui.WebUI, "_gather_wizard", lambda self: None)
    monkeypatch.setattr(Path, "exists", lambda _self: True)
    ctx = {
        "st": st,
        "cli": cli_stub,
        "webui": webui,
        "ui": webui.WebUI(),
        "save_config_mock": save_config_mock,
        "load_project_config_mock": load_project_config_mock,
    }
    return ctx


class DummyForm:
    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@given("the WebUI is initialized")
def given_webui_initialized(webui_context):
    return webui_context


@given("I have a valid project directory")
def given_valid_project_directory(webui_context, monkeypatch):
    from pathlib import Path

    monkeypatch.setattr(Path, "exists", lambda _self: True)
    monkeypatch.setattr(Path, "is_dir", lambda _self: True)
    return webui_context


@given("I am on the analysis page")
def given_on_analysis_page(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Analysis"
    webui_context["ui"].run()
    return webui_context


@when('I navigate to the "Analysis" page')
def navigate_to_analysis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Analysis"
    webui_context["ui"].run()


@when("I submit the analysis form with default settings")
def submit_analysis_form_default(webui_context):
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].analysis_page()


@when("I enter a custom path for analysis")
def enter_custom_path(webui_context):
    webui_context["st"].text_input.return_value = "/custom/path/to/analyze"


@when("I select specific analysis options")
def select_analysis_options(webui_context):
    webui_context["st"].checkbox.side_effect = [
        True,
        False,
        True,
    ]  # Custom option pattern


@when("I submit the analysis form")
def submit_analysis_form(webui_context):
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].analysis_page()


@when("I enter an invalid path for analysis")
def enter_invalid_path(webui_context, monkeypatch):
    from pathlib import Path

    webui_context["st"].text_input.return_value = "/invalid/path"
    monkeypatch.setattr(Path, "exists", lambda _self: False)


@when('I navigate to the "Synthesis" page')
def navigate_to_synthesis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Synthesis"
    webui_context["ui"].run()


@when('I navigate back to the "Analysis" page')
def navigate_back_to_analysis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Analysis"
    webui_context["ui"].run()


@then("I should see the analysis page title")
def see_analysis_title(webui_context):
    webui_context["st"].header.assert_any_call("Code Analysis")


@then("I should see the code analysis form")
def see_analysis_form(webui_context):
    assert webui_context["st"].form.called


@then("the code analysis should be executed")
def code_analysis_executed(webui_context):
    assert webui_context["cli"].inspect_code_cmd.called


@then("I should see the analysis results")
def see_analysis_results(webui_context):
    # This would check for success message or results display
    assert webui_context["st"].success.called or webui_context["st"].write.called


@then("the code analysis should be executed with custom settings")
def code_analysis_executed_custom(webui_context):
    assert webui_context["cli"].inspect_code_cmd.called
    # Verify custom settings were passed
    args, kwargs = webui_context["cli"].inspect_code_cmd.call_args
    assert "/custom/path/to/analyze" in str(kwargs)


@then("I should see an appropriate error message")
def see_error_message(webui_context):
    assert webui_context["st"].error.called


@then("I should be able to correct the input and resubmit")
def can_correct_and_resubmit(webui_context):
    # Verify form is still accessible after error
    assert webui_context["st"].form.called


@then("I should see the analysis page with preserved state")
def see_analysis_with_preserved_state(webui_context):
    # Check that session state preserves values
    assert (
        "analysis_path" in webui_context["st"].session_state
        or webui_context["st"].text_input.called
    )
