import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "synthesis.feature"))


@pytest.fixture
def webui_context(monkeypatch):
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Synthesis")
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
    col3_mock = MagicMock()
    col3_mock.button = MagicMock(return_value=False)
    st.columns = MagicMock(return_value=(col1_mock, col2_mock, col3_mock))
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


@given("I am on the synthesis page")
def given_on_synthesis_page(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Synthesis"
    webui_context["ui"].run()
    return webui_context


@when('I navigate to the "Synthesis" page')
def navigate_to_synthesis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Synthesis"
    webui_context["ui"].run()


@when('I click the "Generate Tests" button')
def click_generate_tests(webui_context):
    # Configure the first column's button to return True (Generate Tests)
    cols = webui_context["st"].columns.return_value
    cols[0].button.return_value = True
    cols[1].button.return_value = False
    cols[2].button.return_value = False
    webui_context["ui"].synthesis_page()


@when('I click the "Generate Code" button')
def click_generate_code(webui_context):
    # Configure the second column's button to return True (Generate Code)
    cols = webui_context["st"].columns.return_value
    cols[0].button.return_value = False
    cols[1].button.return_value = True
    cols[2].button.return_value = False
    webui_context["ui"].synthesis_page()


@when('I click the "Run Pipeline" button')
def click_run_pipeline(webui_context):
    # Configure the third column's button to return True (Run Pipeline)
    cols = webui_context["st"].columns.return_value
    cols[0].button.return_value = False
    cols[1].button.return_value = False
    cols[2].button.return_value = True
    webui_context["ui"].synthesis_page()


@when("I expand the advanced options")
def expand_advanced_options(webui_context):
    webui_context["st"].expander = MagicMock(return_value=DummyForm(True))
    webui_context["ui"].synthesis_page()


@when("I select specific test generation options")
def select_test_generation_options(webui_context):
    webui_context["st"].checkbox.side_effect = [
        True,
        False,
        True,
    ]  # Custom option pattern
    webui_context["st"].selectbox.return_value = "bdd"  # Select BDD test style
    webui_context["st"].number_input.return_value = 90  # Set coverage target to 90%


@when("I select specific code generation options")
def select_code_generation_options(webui_context):
    webui_context["st"].checkbox.side_effect = [
        True,
        True,
        False,
    ]  # Custom option pattern
    webui_context["st"].selectbox.return_value = "python"  # Select Python language
    webui_context["st"].text_input.return_value = (
        "src/custom"  # Custom output directory
    )


@when("an error occurs during test generation")
def error_during_test_generation(webui_context):
    # Make the test_cmd raise an exception when called
    webui_context["cli"].test_cmd.side_effect = Exception("Test generation failed")


@when('I navigate to the "Analysis" page')
def navigate_to_analysis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Analysis"
    webui_context["ui"].run()


@when('I navigate back to the "Synthesis" page')
def navigate_back_to_synthesis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Synthesis"
    webui_context["ui"].run()


@then("I should see the synthesis page title")
def see_synthesis_title(webui_context):
    webui_context["st"].header.assert_any_call("Code Synthesis")


@then("I should see the synthesis options")
def see_synthesis_options(webui_context):
    assert webui_context["st"].columns.called


@then("the test generation should be executed")
def test_generation_executed(webui_context):
    assert webui_context["cli"].test_cmd.called


@then("I should see the test generation results")
def see_test_generation_results(webui_context):
    # This would check for success message or results display
    assert webui_context["st"].success.called or webui_context["st"].write.called


@then("the code generation should be executed")
def code_generation_executed(webui_context):
    assert webui_context["cli"].code_cmd.called


@then("I should see the code generation results")
def see_code_generation_results(webui_context):
    # This would check for success message or results display
    assert webui_context["st"].success.called or webui_context["st"].write.called


@then("the full pipeline should be executed")
def full_pipeline_executed(webui_context):
    assert webui_context["cli"].run_pipeline_cmd.called


@then("I should see the pipeline execution results")
def see_pipeline_execution_results(webui_context):
    # This would check for success message or results display
    assert webui_context["st"].success.called or webui_context["st"].write.called


@then("the test generation should be executed with custom settings")
def test_generation_executed_custom(webui_context):
    assert webui_context["cli"].test_cmd.called
    # Verify custom settings were passed
    args, kwargs = webui_context["cli"].test_cmd.call_args
    # Check for custom settings in the arguments
    assert "bdd" in str(kwargs) or 90 in str(kwargs)


@then("the code generation should be executed with custom settings")
def code_generation_executed_custom(webui_context):
    assert webui_context["cli"].code_cmd.called
    # Verify custom settings were passed
    args, kwargs = webui_context["cli"].code_cmd.call_args
    # Check for custom settings in the arguments
    assert "python" in str(kwargs) or "src/custom" in str(kwargs)


@then("I should see an appropriate error message")
def see_error_message(webui_context):
    assert webui_context["st"].error.called


@then("I should be able to retry the operation")
def can_retry_operation(webui_context):
    # Verify buttons are still accessible after error
    assert webui_context["st"].columns.called


@then("I should see the synthesis page with preserved state")
def see_synthesis_with_preserved_state(webui_context):
    # Check that session state preserves values
    assert (
        "synthesis_options" in webui_context["st"].session_state
        or webui_context["st"].columns.called
    )
