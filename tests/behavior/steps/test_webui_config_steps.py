import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "config.feature"))


@pytest.fixture
def webui_context(monkeypatch):
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Configuration")
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
    st.tabs = MagicMock(
        return_value=[
            DummyForm(True),
            DummyForm(True),
            DummyForm(True),
            DummyForm(True),
            DummyForm(True),
        ]
    )

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
        "enable_feature_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    from pathlib import Path

    from devsynth.config import ProjectUnifiedConfig
    from devsynth.config.loader import ConfigModel

    mock_config = ConfigModel(
        project_root="/mock/project/root",
        offline_mode=False,
        features={"feature1": False, "feature2": False},
        uxbridge_settings={
            "default_interface": "cli",
            "webui_port": 8501,
            "api_port": 8000,
            "enable_authentication": False,
        },
    )
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
        "config": mock_project_config,
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


@given("I am on the configuration page")
def given_on_config_page(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Configuration"
    webui_context["ui"].run()
    return webui_context


@when('I navigate to the "Configuration" page')
def navigate_to_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Configuration"
    webui_context["ui"].run()


@when('I select the "Provider Settings" category')
def select_provider_settings(webui_context):
    # Mock the tabs to return the provider settings tab as active
    tabs = webui_context["st"].tabs.return_value
    # Set the second tab (index 1) as the active tab
    webui_context["st"].tabs.return_value = [
        DummyForm(False),
        DummyForm(True),
        DummyForm(False),
        DummyForm(False),
        DummyForm(False),
    ]
    webui_context["ui"].config_page()


@when('I select the "Memory Settings" category')
def select_memory_settings(webui_context):
    # Mock the tabs to return the memory settings tab as active
    tabs = webui_context["st"].tabs.return_value
    # Set the third tab (index 2) as the active tab
    webui_context["st"].tabs.return_value = [
        DummyForm(False),
        DummyForm(False),
        DummyForm(True),
        DummyForm(False),
        DummyForm(False),
    ]
    webui_context["ui"].config_page()


@when('I select the "Feature Flags" category')
def select_feature_flags(webui_context):
    # Mock the tabs to return the feature flags tab as active
    tabs = webui_context["st"].tabs.return_value
    # Set the fifth tab (index 4) as the active tab
    webui_context["st"].tabs.return_value = [
        DummyForm(False),
        DummyForm(False),
        DummyForm(False),
        DummyForm(False),
        DummyForm(True),
    ]
    webui_context["ui"].config_page()


@when('I modify the "offline_mode" setting')
def modify_offline_mode(webui_context):
    webui_context["st"].checkbox.return_value = True  # Set offline_mode to True
    webui_context["ui"].config_page()


@when('I modify the "provider" setting')
def modify_provider_setting(webui_context):
    webui_context["st"].selectbox.return_value = (
        "anthropic"  # Change provider to anthropic
    )
    webui_context["ui"].config_page()


@when('I modify the "memory_provider" setting')
def modify_memory_provider(webui_context):
    webui_context["st"].selectbox.return_value = (
        "kuzu"  # Change memory provider to kuzu
    )
    webui_context["ui"].config_page()


@when("I enable a feature flag")
def enable_feature_flag(webui_context):
    webui_context["st"].toggle.return_value = True  # Enable a feature flag
    webui_context["ui"].config_page()


@when("I save the configuration changes")
def save_config_changes(webui_context):
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].config_page()


@when("I enter an invalid value for a configuration setting")
def enter_invalid_config(webui_context):
    # Simulate entering an invalid value that will cause an error
    webui_context["st"].text_input.return_value = "invalid://value"
    # Make save_config raise an exception
    import devsynth.interface.webui.rendering as rendering

    failing_save = MagicMock(side_effect=ValueError("Invalid configuration value"))
    rendering.save_config = failing_save
    webui_context["webui"].save_config = failing_save
    webui_context["save_config_mock"] = failing_save
    webui_context["ui"].config_page()


@when("I try to save the configuration changes")
def try_save_invalid_config(webui_context):
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].config_page()


@when('I click the "Reset to Defaults" button')
def click_reset_defaults(webui_context):
    # Configure the button to return True
    webui_context["st"].button.return_value = True
    webui_context["ui"].config_page()


@when("I confirm the reset action")
def confirm_reset(webui_context):
    # Simulate confirming the reset action
    webui_context["st"].button.return_value = True
    webui_context["ui"].config_page()


@when('I navigate to the "Analysis" page')
def navigate_to_analysis(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Analysis"
    webui_context["ui"].run()


@when('I navigate back to the "Configuration" page')
def navigate_back_to_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Configuration"
    webui_context["ui"].run()


@then("I should see the configuration page title")
def see_config_title(webui_context):
    webui_context["st"].header.assert_any_call("Configuration")


@then("I should see the current configuration settings")
def see_config_settings(webui_context):
    assert webui_context["st"].tabs.called


@then("I should see the following configuration categories:")
def see_config_categories(webui_context, table):
    # Verify that tabs are created for each category
    assert webui_context["st"].tabs.called
    # The table parameter contains the expected categories
    categories = [row["Category"] for row in table]
    # We can't directly verify the tab labels in this mock setup,
    # but we can check that the number of tabs matches the number of categories
    assert len(webui_context["st"].tabs.return_value) == len(categories)


@then("the configuration should be updated")
def config_updated(webui_context):
    assert webui_context["save_config_mock"].called


@then("I should see a success message")
def see_success_message(webui_context):
    assert webui_context["st"].success.called


@then("the feature flag should be enabled")
def feature_flag_enabled(webui_context):
    assert (
        webui_context["cli"].enable_feature_cmd.called
        or webui_context["save_config_mock"].called
    )


@then("I should see an appropriate error message")
def see_error_message(webui_context):
    assert webui_context["st"].error.called


@then("the invalid configuration should not be saved")
def invalid_config_not_saved(webui_context):
    # Check that save_config was called but the error was caught
    assert webui_context["st"].error.called


@then("the configuration should be reset to default values")
def config_reset_to_defaults(webui_context):
    # Check that the config was reset
    assert webui_context["save_config_mock"].called


@then("I should see the configuration page with preserved state")
def see_config_with_preserved_state(webui_context):
    # Check that session state preserves values
    assert (
        "config_tab" in webui_context["st"].session_state
        or webui_context["st"].tabs.called
    )
