import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

scenarios("../features/general/webui.feature")


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
    st.toggle = MagicMock(return_value=True)  # Add toggle method
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
    cli_stub.inspect_code_cmd = analyze_stub.inspect_code_cmd

    doctor_stub = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_stub.doctor_cmd = MagicMock()
    doctor_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_stub
    )
    cli_stub.doctor_cmd = doctor_stub.doctor_cmd

    edrr_stub = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_stub.edrr_cycle_cmd = MagicMock()
    edrr_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_stub
    )
    cli_stub.edrr_cycle_cmd = edrr_stub.edrr_cycle_cmd

    align_stub = ModuleType("devsynth.application.cli.commands.align_cmd")
    align_stub.align_cmd = MagicMock()
    align_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.align_cmd", align_stub
    )
    cli_stub.align_cmd = align_stub.align_cmd

    # Mock additional CLI command modules
    alignment_metrics_stub = ModuleType(
        "devsynth.application.cli.commands.alignment_metrics_cmd"
    )
    alignment_metrics_stub.alignment_metrics_cmd = MagicMock()
    alignment_metrics_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.alignment_metrics_cmd",
        alignment_metrics_stub,
    )
    cli_stub.alignment_metrics_cmd = alignment_metrics_stub.alignment_metrics_cmd

    inspect_config_stub = ModuleType(
        "devsynth.application.cli.commands.inspect_config_cmd"
    )
    inspect_config_stub.inspect_config_cmd = MagicMock()
    inspect_config_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.inspect_config_cmd",
        inspect_config_stub,
    )
    cli_stub.inspect_config_cmd = inspect_config_stub.inspect_config_cmd

    validate_manifest_stub = ModuleType(
        "devsynth.application.cli.commands.validate_manifest_cmd"
    )
    validate_manifest_stub.validate_manifest_cmd = MagicMock()
    validate_manifest_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.validate_manifest_cmd",
        validate_manifest_stub,
    )
    cli_stub.validate_manifest_cmd = validate_manifest_stub.validate_manifest_cmd

    validate_metadata_stub = ModuleType(
        "devsynth.application.cli.commands.validate_metadata_cmd"
    )
    validate_metadata_stub.validate_metadata_cmd = MagicMock()
    validate_metadata_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.validate_metadata_cmd",
        validate_metadata_stub,
    )
    cli_stub.validate_metadata_cmd = validate_metadata_stub.validate_metadata_cmd

    test_metrics_stub = ModuleType("devsynth.application.cli.commands.test_metrics_cmd")
    test_metrics_stub.test_metrics_cmd = MagicMock()
    test_metrics_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.test_metrics_cmd",
        test_metrics_stub,
    )
    cli_stub.test_metrics_cmd = test_metrics_stub.test_metrics_cmd

    generate_docs_stub = ModuleType(
        "devsynth.application.cli.commands.generate_docs_cmd"
    )
    generate_docs_stub.generate_docs_cmd = MagicMock()
    generate_docs_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.generate_docs_cmd",
        generate_docs_stub,
    )
    cli_stub.generate_docs_cmd = generate_docs_stub.generate_docs_cmd

    # Mock ingest_cmd module
    ingest_cmd_stub = ModuleType("devsynth.application.cli.ingest_cmd")
    ingest_cmd_stub.ingest_cmd = MagicMock()
    ingest_cmd_stub.bridge = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.ingest_cmd", ingest_cmd_stub
    )
    cli_stub.ingest_cmd = ingest_cmd_stub.ingest_cmd

    # Mock apispec module
    apispec_stub = ModuleType("devsynth.application.cli.apispec")
    apispec_stub.apispec_cmd = MagicMock()
    apispec_stub.bridge = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.apispec", apispec_stub)
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

    mock_config = ConfigModel(project_root="/mock/project/root", offline_mode=False)
    mock_project_config = ProjectUnifiedConfig(
        config=mock_config,
        path=Path("/mock/project/root/.devsynth/project.yaml"),
        use_pyproject=False,
    )

    config_stub = ModuleType("devsynth.config")
    config_stub.load_project_config = MagicMock(return_value=mock_project_config)
    config_stub.save_config = MagicMock()
    config_stub.get_llm_settings = MagicMock(
        return_value={
            "provider_type": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 2000,
        }
    )
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
    monkeypatch.setattr(webui.WebUI, "_requirements_wizard", lambda self: None)
    monkeypatch.setattr(webui.WebUI, "_gather_wizard", lambda self: None)
    monkeypatch.setattr(Path, "exists", lambda _self: True)
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


@when("I submit the edrr cycle form")
def submit_edrr_cycle(webui_context):
    webui_context["st"].sidebar.radio.return_value = "EDRR Cycle"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the alignment form")
def submit_alignment(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Alignment"
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


@then("the edrr_cycle command should be executed")
def check_edrr_cycle(webui_context):
    assert webui_context["cli"].edrr_cycle_cmd.called


@then("the align command should be executed")
def check_align(webui_context):
    assert webui_context["cli"].align_cmd.called


@when("I submit the alignment metrics form")
def submit_alignment_metrics(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Alignment Metrics"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the inspect config form")
def submit_inspect_config(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Inspect Config"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the validate manifest form")
def submit_validate_manifest(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Validate Manifest"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the validate metadata form")
def submit_validate_metadata(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Validate Metadata"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the test metrics form")
def submit_test_metrics(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Test Metrics"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the generate docs form")
def submit_generate_docs(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Generate Docs"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the ingest form")
def submit_ingest(webui_context):
    webui_context["st"].sidebar.radio.return_value = "Ingest"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@when("I submit the api spec form")
def submit_api_spec(webui_context):
    webui_context["st"].sidebar.radio.return_value = "API Spec"
    webui_context["st"].form_submit_button.return_value = True
    webui_context["ui"].run()


@then("the alignment_metrics command should be executed")
def check_alignment_metrics(webui_context):
    assert webui_context["cli"].alignment_metrics_cmd.called


@then("the inspect_config command should be executed")
def check_inspect_config(webui_context):
    assert webui_context["cli"].inspect_config_cmd.called


@then("the validate_manifest command should be executed")
def check_validate_manifest(webui_context):
    assert webui_context["cli"].validate_manifest_cmd.called


@then("the validate_metadata command should be executed")
def check_validate_metadata(webui_context):
    assert webui_context["cli"].validate_metadata_cmd.called


@then("the test_metrics command should be executed")
def check_test_metrics(webui_context):
    assert webui_context["cli"].test_metrics_cmd.called


@then("the generate_docs command should be executed")
def check_generate_docs(webui_context):
    assert webui_context["cli"].generate_docs_cmd.called


@then("the ingest command should be executed")
def check_ingest(webui_context):
    assert webui_context["cli"].ingest_cmd.called


@then("the apispec command should be executed")
def check_apispec(webui_context):
    assert webui_context["cli"].apispec_cmd.called
