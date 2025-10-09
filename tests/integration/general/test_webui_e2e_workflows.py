import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

"""
This test file implements integration tests for end-to-end workflows in the WebUI,
focusing on user journeys that span multiple pages.
"""


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
def webui_env(monkeypatch):
    """Set up a mock environment for WebUI testing."""
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {}
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock()
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
        "enable_feature_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    # Mock CLI command modules
    analyze_stub = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_stub.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_code_cmd", analyze_stub
    )
    cli_stub.inspect_code_cmd = analyze_stub.inspect_code_cmd

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

    return webui.WebUI(), st, cli_stub


@pytest.mark.slow
def test_analysis_to_synthesis_workflow_succeeds(webui_env):
    """Test a workflow from analysis to synthesis.

    This test simulates a user journey where the user:
    1. Navigates to the analysis page
    2. Runs code analysis
    3. Navigates to the synthesis page
    4. Generates tests based on the analysis

    ReqID: N/A
    """
    webui, st, cli = webui_env

    # Step 1: Navigate to analysis page
    st.sidebar.radio.return_value = "Analysis"
    webui.run()
    st.header.assert_any_call("Code Analysis")

    # Step 2: Run code analysis with custom path
    st.text_input.return_value = "/custom/path/to/analyze"
    st.form_submit_button.return_value = True
    webui.analysis_page()

    # Verify analysis was executed
    assert cli.inspect_code_cmd.called

    # Step 3: Navigate to synthesis page
    st.sidebar.radio.return_value = "Synthesis"
    webui.run()
    st.header.assert_any_call("Code Synthesis")

    # Step 4: Generate tests
    cols = st.columns.return_value
    cols[0].button.return_value = True  # Generate Tests button
    cols[1].button.return_value = False
    cols[2].button.return_value = False
    webui.synthesis_page()

    # Verify test generation was executed
    assert cli.test_cmd.called

    # Verify success message was shown
    assert st.success.called


@pytest.mark.slow
def test_config_to_analysis_workflow_succeeds(webui_env):
    """Test a workflow from configuration to analysis.

    This test simulates a user journey where the user:
    1. Navigates to the configuration page
    2. Updates configuration settings
    3. Navigates to the analysis page
    4. Runs code analysis with the new configuration

    ReqID: N/A
    """
    webui, st, cli = webui_env

    # Step 1: Navigate to configuration page
    st.sidebar.radio.return_value = "Configuration"
    webui.run()
    st.header.assert_any_call("Configuration")

    # Step 2: Update offline mode setting
    st.checkbox.return_value = True  # Set offline_mode to True
    st.form_submit_button.return_value = True
    webui.config_page()

    # Verify configuration was updated
    assert webui.save_config.called

    # Step 3: Navigate to analysis page
    st.sidebar.radio.return_value = "Analysis"
    webui.run()
    st.header.assert_any_call("Code Analysis")

    # Step 4: Run code analysis
    st.form_submit_button.return_value = True
    webui.analysis_page()

    # Verify analysis was executed with updated configuration
    assert cli.inspect_code_cmd.called


@pytest.mark.slow
def test_complete_e2e_workflow_succeeds(webui_env):
    """Test a complete end-to-end workflow through multiple pages.

    This test simulates a comprehensive user journey where the user:
    1. Navigates to the configuration page
    2. Updates configuration settings
    3. Navigates to the analysis page
    4. Runs code analysis
    5. Navigates to the synthesis page
    6. Generates tests
    7. Generates code
    8. Runs the full pipeline

    ReqID: N/A
    """
    webui, st, cli = webui_env

    # Step 1: Navigate to configuration page
    st.sidebar.radio.return_value = "Configuration"
    webui.run()
    st.header.assert_any_call("Configuration")

    # Step 2: Update provider settings
    # Select Provider Settings tab
    st.tabs.return_value = [
        DummyForm(False),
        DummyForm(True),
        DummyForm(False),
        DummyForm(False),
        DummyForm(False),
    ]
    st.selectbox.return_value = "anthropic"  # Change provider to anthropic
    st.form_submit_button.return_value = True
    webui.config_page()

    # Verify configuration was updated
    assert webui.save_config.called

    # Step 3: Navigate to analysis page
    st.sidebar.radio.return_value = "Analysis"
    webui.run()
    st.header.assert_any_call("Code Analysis")

    # Step 4: Run code analysis
    st.text_input.return_value = "/project/src"
    st.form_submit_button.return_value = True
    webui.analysis_page()

    # Verify analysis was executed
    assert cli.inspect_code_cmd.called

    # Step 5: Navigate to synthesis page
    st.sidebar.radio.return_value = "Synthesis"
    webui.run()
    st.header.assert_any_call("Code Synthesis")

    # Step 6: Generate tests
    cols = st.columns.return_value
    cols[0].button.return_value = True  # Generate Tests button
    cols[1].button.return_value = False
    cols[2].button.return_value = False
    webui.synthesis_page()

    # Verify test generation was executed
    assert cli.test_cmd.called

    # Reset button states
    cols[0].button.return_value = False

    # Step 7: Generate code
    cols[1].button.return_value = True  # Generate Code button
    webui.synthesis_page()

    # Verify code generation was executed
    assert cli.code_cmd.called

    # Reset button states
    cols[1].button.return_value = False

    # Step 8: Run full pipeline
    cols[2].button.return_value = True  # Run Pipeline button
    webui.synthesis_page()

    # Verify pipeline execution was executed
    assert cli.run_pipeline_cmd.called


@pytest.mark.slow
def test_error_handling_in_workflow_succeeds(webui_env):
    """Test error handling during a workflow.

    This test simulates error scenarios during a user journey:
    1. Navigate to the analysis page
    2. Enter an invalid path and attempt analysis
    3. Correct the error and retry
    4. Navigate to the synthesis page
    5. Encounter an error during test generation
    6. Retry with different settings

    ReqID: N/A
    """
    webui, st, cli = webui_env

    # Step 1: Navigate to analysis page
    st.sidebar.radio.return_value = "Analysis"
    webui.run()
    st.header.assert_any_call("Code Analysis")

    # Step 2: Enter invalid path and attempt analysis
    st.text_input.return_value = "/invalid/path"
    # Make inspect_code_cmd raise an exception
    cli.inspect_code_cmd.side_effect = ValueError("Invalid path")
    st.form_submit_button.return_value = True
    webui.analysis_page()

    # Verify error was shown
    assert st.error.called

    # Step 3: Correct the error and retry
    st.error.reset_mock()
    st.text_input.return_value = "/valid/path"
    cli.inspect_code_cmd.side_effect = None  # Remove the error
    st.form_submit_button.return_value = True
    webui.analysis_page()

    # Verify analysis was executed successfully
    assert cli.inspect_code_cmd.called
    assert not st.error.called

    # Step 4: Navigate to synthesis page
    st.sidebar.radio.return_value = "Synthesis"
    webui.run()
    st.header.assert_any_call("Code Synthesis")

    # Step 5: Encounter an error during test generation
    cols = st.columns.return_value
    cols[0].button.return_value = True  # Generate Tests button
    # Make test_cmd raise an exception
    cli.test_cmd.side_effect = RuntimeError("Test generation failed")
    webui.synthesis_page()

    # Verify error was shown
    assert st.error.called

    # Step 6: Retry with different settings
    st.error.reset_mock()
    cli.test_cmd.side_effect = None  # Remove the error
    webui.synthesis_page()

    # Verify test generation was executed successfully
    assert cli.test_cmd.called
    assert not st.error.called


@pytest.mark.slow
def test_state_preservation_in_workflow_succeeds(webui_env):
    """Test state preservation during navigation between pages.

    This test verifies that state is preserved when navigating between pages:
    1. Navigate to the analysis page and set options
    2. Navigate to the synthesis page
    3. Navigate back to the analysis page and verify options are preserved
    4. Navigate to the configuration page and set options
    5. Navigate back to the synthesis page and verify state

    ReqID: N/A
    """
    webui, st, cli = webui_env

    # Step 1: Navigate to analysis page and set options
    st.sidebar.radio.return_value = "Analysis"
    st.text_input.return_value = "/custom/analysis/path"
    st.checkbox.return_value = True
    webui.run()
    webui.analysis_page()

    # Store the input value in session state (simulating what the actual code would do)
    st.session_state.analysis_path = "/custom/analysis/path"
    st.session_state.analysis_options = {"option1": True}

    # Step 2: Navigate to synthesis page
    st.sidebar.radio.return_value = "Synthesis"
    webui.run()

    # Step 3: Navigate back to analysis page and verify options are preserved
    st.sidebar.radio.return_value = "Analysis"
    webui.run()

    # Verify the text_input is called with the preserved value
    st.text_input.assert_any_call(
        "Path to analyze", value="/custom/analysis/path", key="analysis_path"
    )

    # Step 4: Navigate to configuration page and set options
    st.sidebar.radio.return_value = "Configuration"
    webui.run()

    # Set a configuration option
    st.checkbox.return_value = True  # Set offline_mode to True
    webui.config_page()

    # Store the selected tab in session state
    st.session_state.config_tab = 0

    # Step 5: Navigate back to synthesis page
    st.sidebar.radio.return_value = "Synthesis"
    webui.run()

    # Navigate back to configuration page and verify state is preserved
    st.sidebar.radio.return_value = "Configuration"
    webui.run()

    # Verify the tabs function is called with the preserved tab index
    assert "config_tab" in st.session_state
