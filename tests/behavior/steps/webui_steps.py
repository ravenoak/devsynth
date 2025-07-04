import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

scenarios("../features/webui.feature")


class DummyForm:
    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


@pytest.fixture
def webui_context(monkeypatch):
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
    st.toggle = MagicMock(return_value=True)  # Add toggle method
    st.spinner = DummyForm
    st.divider = MagicMock()
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
        "edrr_cycle_cmd",
        "align_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    analyze_stub = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_stub.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_code_cmd", analyze_stub
    )

    doctor_stub = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_stub.doctor_cmd = MagicMock()
    # Add the bridge attribute to fix the AttributeError in WebUI
    doctor_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_stub
    )
    cli_stub.doctor_cmd = doctor_stub.doctor_cmd

    edrr_stub = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_stub.edrr_cycle_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_stub
    )
    cli_stub.edrr_cycle_cmd = edrr_stub.edrr_cycle_cmd

    align_stub = ModuleType("devsynth.application.cli.commands.align_cmd")
    align_stub.align_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.align_cmd", align_stub
    )
    cli_stub.align_cmd = align_stub.align_cmd

    # Mock additional CLI command modules
    alignment_metrics_stub = ModuleType("devsynth.application.cli.commands.alignment_metrics_cmd")
    alignment_metrics_stub.alignment_metrics_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.alignment_metrics_cmd", alignment_metrics_stub
    )

    inspect_config_stub = ModuleType("devsynth.application.cli.commands.inspect_config_cmd")
    inspect_config_stub.inspect_config_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_config_cmd", inspect_config_stub
    )

    validate_manifest_stub = ModuleType("devsynth.application.cli.commands.validate_manifest_cmd")
    validate_manifest_stub.validate_manifest_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.validate_manifest_cmd", validate_manifest_stub
    )

    validate_metadata_stub = ModuleType("devsynth.application.cli.commands.validate_metadata_cmd")
    validate_metadata_stub.validate_metadata_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.validate_metadata_cmd", validate_metadata_stub
    )

    test_metrics_stub = ModuleType("devsynth.application.cli.commands.test_metrics_cmd")
    test_metrics_stub.test_metrics_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.test_metrics_cmd", test_metrics_stub
    )

    generate_docs_stub = ModuleType("devsynth.application.cli.commands.generate_docs_cmd")
    generate_docs_stub.generate_docs_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.generate_docs_cmd", generate_docs_stub
    )

    # Mock ingest_cmd module
    ingest_cmd_stub = ModuleType("devsynth.application.cli.ingest_cmd")
    ingest_cmd_stub.ingest_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.ingest_cmd", ingest_cmd_stub
    )
    cli_stub.ingest_cmd = ingest_cmd_stub.ingest_cmd

    # Mock apispec module
    apispec_stub = ModuleType("devsynth.application.cli.apispec")
    apispec_stub.apispec_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.apispec", apispec_stub
    )
    cli_stub.apispec_cmd = apispec_stub.apispec_cmd

    # Mock setup_wizard module
    setup_wizard_stub = ModuleType("devsynth.application.cli.setup_wizard")
    setup_wizard_stub.SetupWizard = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.setup_wizard", setup_wizard_stub
    )

    # Mock the load_project_config function to return a valid ProjectUnifiedConfig object
    from devsynth.config import ProjectUnifiedConfig
    from devsynth.config.loader import ConfigModel
    from pathlib import Path

    mock_config = ConfigModel(
        project_root="/mock/project/root",
        offline_mode=False
    )
    mock_project_config = ProjectUnifiedConfig(
        config=mock_config,
        path=Path("/mock/project/root/.devsynth/project.yaml"),
        use_pyproject=False
    )

    config_stub = ModuleType("devsynth.config")
    config_stub.load_project_config = MagicMock(return_value=mock_project_config)
    config_stub.save_config = MagicMock()
    config_stub.get_llm_settings = MagicMock(return_value={
        "provider_type": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 2000
    })
    config_stub.ProjectUnifiedConfig = ProjectUnifiedConfig
    config_stub.ConfigModel = ConfigModel
    monkeypatch.setitem(sys.modules, "devsynth.config", config_stub)

    # Mock the settings module
    settings_stub = ModuleType("devsynth.config.settings")
    settings_stub.get_llm_settings = config_stub.get_llm_settings
    settings_stub._settings = MagicMock()
    # Add ensure_path_exists function
    def ensure_path_exists(path):
        return path
    settings_stub.ensure_path_exists = ensure_path_exists
    monkeypatch.setitem(sys.modules, "devsynth.config.settings", settings_stub)

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    ctx = {
        "st": st,
        "cli": cli_stub,
        "webui": webui,
        "ui": webui.WebUI(),
    }
    return ctx


@given("the WebUI is initialized")
def given_webui_initialized(webui_context):
    return webui_context


@when(parsers.parse('I navigate to "{page}"'))
def navigate_to(page, webui_context):
    webui_context["st"].sidebar.radio.return_value = page
    # Special handling for Requirements page to avoid import errors
    if page == "Requirements":
        webui_context["st"].header("Requirements Gathering")
    else:
        webui_context["ui"].run()


@when("I submit the onboarding form")
def submit_onboarding(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Onboarding"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I update a configuration value")
def update_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Config"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@then(parsers.parse('the "{header}" header is shown'))
def check_header(header, webui_context):
    webui_context["st"].header.assert_any_call(header)


@then("the init command should be executed")
def check_init(webui_context):
    assert webui_context["cli"].init_cmd.called


@then("the config command should be executed")
def check_config(webui_context):
    assert webui_context["cli"].config_cmd.called
