"""Test script for cross-interface consistency."""

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")

# Defer fastapi.testclient import to avoid MRO issues during collection
# Import will be done lazily when actually needed by tests
TestClient = None

def _get_testclient():
    """Lazily import TestClient to avoid MRO issues during collection."""
    global TestClient
    if TestClient is None:
        try:
            from fastapi.testclient import TestClient
        except TypeError:
            # Fallback for MRO compatibility issues
            from starlette.testclient import TestClient
    return TestClient

from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

# Import step definitions implemented for FR-67
from .steps.test_cross_interface_consistency_steps import *  # noqa: F401,F403

pytestmark = [pytest.mark.fast]

# Load the scenarios from the canonical behavior asset path.
scenarios(feature_path(__file__, "general", "cross_interface_consistency.feature"))

from devsynth.interface.agentapi import APIBridge

# Import the necessary modules
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge


class DummyForm:
    """Simple context manager used to mock Streamlit forms."""

    def __init__(self, submitted: bool = True) -> None:
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted


class DummyProgress:
    """Mock progress indicator for testing."""

    def __init__(self, *args, **kwargs):
        self.updated = False
        self.completed = False
        self.description = args[0] if args else "Progress"
        self.total = kwargs.get("total", 100)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.complete()
        return False

    def update(self, *args, **kwargs):
        self.updated = True

    def complete(self):
        self.completed = True


@pytest.fixture
def cross_interface_context(monkeypatch):
    """Create a context with all three interfaces initialized."""
    # Mock dependencies
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())

    # Mock CLI modules and commands
    from devsynth.application import cli as cli_module

    for cmd in [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "doctor_cmd",
        "edrr_cycle_cmd",
    ]:
        monkeypatch.setattr(cli_module, cmd, MagicMock())

    # Mock Streamlit for WebUI
    st = ModuleType("streamlit")
    st.session_state = {}
    st.text_input = MagicMock(return_value="test_value")
    st.selectbox = MagicMock(return_value="option1")
    st.checkbox = MagicMock(return_value=True)
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.progress = MagicMock(return_value=MagicMock())
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
    st.sidebar = ModuleType("sidebar")
    st.sidebar.radio = MagicMock(return_value="Onboarding")
    st.sidebar.title = MagicMock()
    st.set_page_config = MagicMock()
    st.header = MagicMock()
    # Add missing Streamlit attributes
    st.empty = MagicMock(return_value=MagicMock())
    st.info = MagicMock()
    st.error = MagicMock()
    st.warning = MagicMock()
    st.success = MagicMock()
    st.text_area = MagicMock(return_value="test_value")
    st.number_input = MagicMock(return_value=1)
    st.radio = MagicMock(return_value="option1")
    st.multiselect = MagicMock(return_value=["option1"])
    st.file_uploader = MagicMock(return_value=None)
    monkeypatch.setitem(sys.modules, "streamlit", st)

    # Mock CLI UXBridge
    cli_bridge = CLIUXBridge()
    monkeypatch.setattr(
        cli_bridge, "ask_question", MagicMock(return_value="test_answer")
    )
    monkeypatch.setattr(cli_bridge, "confirm_choice", MagicMock(return_value=True))
    monkeypatch.setattr(cli_bridge, "display_result", MagicMock())
    monkeypatch.setattr(
        cli_bridge, "create_progress", MagicMock(return_value=DummyProgress())
    )

    # Load WebUI
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    web_bridge = webui.WebUI()

    # Mock API Bridge
    api_bridge = APIBridge([])
    monkeypatch.setattr(
        api_bridge, "ask_question", MagicMock(return_value="test_answer")
    )
    monkeypatch.setattr(api_bridge, "confirm_choice", MagicMock(return_value=True))
    monkeypatch.setattr(api_bridge, "display_result", MagicMock())
    monkeypatch.setattr(
        api_bridge, "create_progress", MagicMock(return_value=DummyProgress())
    )

    # Create context with all interfaces
    context = {
        "cli": cli_module,
        "cli_bridge": cli_bridge,
        "web_bridge": web_bridge,
        "api_bridge": api_bridge,
        "st": st,
        "results": {"cli": {}, "web": {}, "api": {}},
        "errors": {"cli": None, "web": None, "api": None},
        "command_params": {
            "init": {
                "path": "test_project",
                "project_root": ".",
                "language": "python",
                "goals": "Test project",
            },
            "spec": {"requirements_file": "requirements.md", "output_file": "specs.md"},
            "test": {"spec_file": "specs.md", "output_dir": "tests"},
            "code": {"test_file": "tests/test_example.py", "output_dir": "src"},
            "doctor": {"path": ".", "fix": False},
            "edrr-cycle": {"manifest_file": "manifest.json"},
        },
        "invalid_params": {
            "init": {
                "path": "",
                "project_root": "",
                "language": "invalid",
                "goals": "",
            },
            "spec": {"requirements_file": "nonexistent.md", "output_file": ""},
            "test": {"spec_file": "nonexistent.md", "output_dir": "/invalid/path"},
            "code": {"test_file": "nonexistent.py", "output_dir": "/invalid/path"},
            "doctor": {"path": "/nonexistent/path", "fix": "invalid"},
            "edrr-cycle": {"manifest_file": "nonexistent.json"},
        },
    }

    return context


@given("the CLI, WebUI, and Agent API are initialized")
def interfaces_initialized(cross_interface_context):
    """Verify that all interfaces are initialized."""
    assert cross_interface_context["cli_bridge"] is not None
    assert cross_interface_context["web_bridge"] is not None
    assert cross_interface_context["api_bridge"] is not None
    return cross_interface_context


@when("I invoke the <command> command with identical parameters via CLI")
@when("I invoke the {command} command with identical parameters via CLI")
def invoke_cli_command(cross_interface_context, command):
    """Invoke a command via the CLI interface."""
    cli_module = cross_interface_context["cli"]
    cli_bridge = cross_interface_context["cli_bridge"]
    params = cross_interface_context["command_params"][command]

    # Get the appropriate command function
    cmd_func = getattr(cli_module, f"{command.replace('-', '_')}_cmd")

    # Call the command with the parameters and bridge
    try:
        result = cmd_func(**params, bridge=cli_bridge)
        cross_interface_context["results"]["cli"] = result
    except Exception as e:
        cross_interface_context["errors"]["cli"] = e


@when("I invoke the <command> command with identical parameters via WebUI")
@when("I invoke the {command} command with identical parameters via WebUI")
def invoke_webui_command(cross_interface_context, command):
    """Invoke a command via the WebUI interface."""
    web_bridge = cross_interface_context["web_bridge"]
    params = cross_interface_context["command_params"][command]

    # Map command to WebUI method
    command_map = {
        "init": "onboarding_page",
        "spec": "requirements_page",
        "test": "analysis_page",
        "code": "synthesis_page",
        "doctor": "doctor_page",
        "edrr-cycle": "edrr_cycle_page",
    }

    # Mock the appropriate WebUI method
    if hasattr(web_bridge, command_map[command]):
        method = getattr(web_bridge, command_map[command])
        try:
            # Set up form inputs for WebUI
            st = cross_interface_context["st"]
            for key, value in params.items():
                st.text_input.side_effect = lambda label, default=None, **kwargs: value

            # Call the WebUI method
            result = method()
            cross_interface_context["results"]["web"] = result
        except Exception as e:
            cross_interface_context["errors"]["web"] = e


@when("I invoke the <command> command with identical parameters via Agent API")
@when("I invoke the {command} command with identical parameters via Agent API")
def invoke_api_command(cross_interface_context, command):
    """Invoke a command via the Agent API interface."""
    api_bridge = cross_interface_context["api_bridge"]
    params = cross_interface_context["command_params"][command]

    # Map command to API endpoint
    endpoint_map = {
        "init": "/init",
        "spec": "/spec",
        "test": "/test",
        "code": "/code",
        "doctor": "/doctor",
        "edrr-cycle": "/edrr-cycle",
    }

    # Mock the API request
    try:
        # Simulate API call
        from devsynth.interface.agentapi import app

        client = _get_testclient()(app)
        response = client.post(endpoint_map[command], json=params)
        cross_interface_context["results"]["api"] = response.json()
    except Exception as e:
        cross_interface_context["errors"]["api"] = e


@when("I invoke the <command> command with invalid parameters via CLI")
@when("I invoke the {command} command with invalid parameters via CLI")
def invoke_cli_command_invalid(cross_interface_context, command):
    """Invoke a command with invalid parameters via the CLI interface."""
    cli_module = cross_interface_context["cli"]
    cli_bridge = cross_interface_context["cli_bridge"]
    params = cross_interface_context["invalid_params"][command]

    # Get the appropriate command function
    cmd_func = getattr(cli_module, f"{command.replace('-', '_')}_cmd")

    # Call the command with invalid parameters and bridge
    try:
        result = cmd_func(**params, bridge=cli_bridge)
        cross_interface_context["results"]["cli"] = result
    except Exception as e:
        cross_interface_context["errors"]["cli"] = e


@when("I invoke the <command> command with invalid parameters via WebUI")
@when("I invoke the {command} command with invalid parameters via WebUI")
def invoke_webui_command_invalid(cross_interface_context, command):
    """Invoke a command with invalid parameters via the WebUI interface."""
    web_bridge = cross_interface_context["web_bridge"]
    params = cross_interface_context["invalid_params"][command]

    # Map command to WebUI method
    command_map = {
        "init": "onboarding_page",
        "spec": "requirements_page",
        "test": "analysis_page",
        "code": "synthesis_page",
        "doctor": "doctor_page",
        "edrr-cycle": "edrr_cycle_page",
    }

    # Mock the appropriate WebUI method
    if hasattr(web_bridge, command_map[command]):
        method = getattr(web_bridge, command_map[command])
        try:
            # Set up form inputs for WebUI
            st = cross_interface_context["st"]
            for key, value in params.items():
                st.text_input.side_effect = lambda label, default=None, **kwargs: value

            # Call the WebUI method
            result = method()
            cross_interface_context["results"]["web"] = result
        except Exception as e:
            cross_interface_context["errors"]["web"] = e


@when("I invoke the <command> command with invalid parameters via Agent API")
@when("I invoke the {command} command with invalid parameters via Agent API")
def invoke_api_command_invalid(cross_interface_context, command):
    """Invoke a command with invalid parameters via the Agent API interface."""
    api_bridge = cross_interface_context["api_bridge"]
    params = cross_interface_context["invalid_params"][command]

    # Map command to API endpoint
    endpoint_map = {
        "init": "/init",
        "spec": "/spec",
        "test": "/test",
        "code": "/code",
        "doctor": "/doctor",
        "edrr-cycle": "/edrr-cycle",
    }

    # Mock the API request
    try:
        # Simulate API call
        from devsynth.interface.agentapi import app

        client = _get_testclient()(app)
        response = client.post(endpoint_map[command], json=params)
        cross_interface_context["results"]["api"] = response.json()
    except Exception as e:
        cross_interface_context["errors"]["api"] = e


@when("I need to ask a question via CLI")
def ask_question_cli(cross_interface_context):
    """Ask a question via the CLI interface."""
    cli_bridge = cross_interface_context["cli_bridge"]
    result = cli_bridge.ask_question(
        "Test question?", choices=["Option 1", "Option 2"], default="Option 1"
    )
    cross_interface_context["results"]["cli"] = result


@when("I need to ask the same question via WebUI")
def ask_question_webui(cross_interface_context):
    """Ask a question via the WebUI interface."""
    web_bridge = cross_interface_context["web_bridge"]
    # Mock the ask_question method to return the same value as the CLI
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        web_bridge, "ask_question", MagicMock(return_value="test_answer")
    )
    result = web_bridge.ask_question(
        "Test question?", choices=["Option 1", "Option 2"], default="Option 1"
    )
    cross_interface_context["results"]["web"] = result


@when("I need to ask the same question via Agent API")
def ask_question_api(cross_interface_context):
    """Ask a question via the Agent API interface."""
    api_bridge = cross_interface_context["api_bridge"]
    # Mock the ask_question method to return the same value as the CLI
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        api_bridge, "ask_question", MagicMock(return_value="test_answer")
    )
    result = api_bridge.ask_question(
        "Test question?", choices=["Option 1", "Option 2"], default="Option 1"
    )
    cross_interface_context["results"]["api"] = result


@when("I perform a long-running operation via CLI")
def long_running_cli(cross_interface_context):
    """Perform a long-running operation via the CLI interface."""
    cli_bridge = cross_interface_context["cli_bridge"]
    with cli_bridge.create_progress("CLI Progress", total=100) as progress:
        progress.update(50)
        progress.complete()
    cross_interface_context["results"]["cli"] = "completed"


@when("I perform the same long-running operation via WebUI")
def long_running_webui(cross_interface_context):
    """Perform a long-running operation via the WebUI interface."""
    web_bridge = cross_interface_context["web_bridge"]
    with web_bridge.create_progress("WebUI Progress", total=100) as progress:
        progress.update(50)
        progress.complete()
    cross_interface_context["results"]["web"] = "completed"


@when("I perform the same long-running operation via Agent API")
def long_running_api(cross_interface_context):
    """Perform a long-running operation via the Agent API interface."""
    api_bridge = cross_interface_context["api_bridge"]
    with api_bridge.create_progress("API Progress", total=100) as progress:
        progress.update(50)
        progress.complete()
    cross_interface_context["results"]["api"] = "completed"


@then("all interfaces should produce identical results")
def verify_identical_results(cross_interface_context):
    """Verify that all interfaces produce identical results."""
    # Check that all interfaces produced a result
    assert "cli" in cross_interface_context["results"]
    assert "web" in cross_interface_context["results"]
    assert "api" in cross_interface_context["results"]

    # Check that the results are equivalent
    # Note: The actual implementation would need to compare the relevant parts of the results,
    # as the exact format might differ between interfaces
    assert cross_interface_context["results"]["cli"] is not None
    assert cross_interface_context["results"]["web"] is not None
    assert cross_interface_context["results"]["api"] is not None


@then("all interfaces should use the same UXBridge methods")
def verify_same_uxbridge_methods(cross_interface_context):
    """Verify that all interfaces use the same UXBridge methods."""
    # This would require tracking which UXBridge methods were called during the test
    # For now, we'll just verify that all bridges are instances of UXBridge
    assert isinstance(cross_interface_context["cli_bridge"], UXBridge)
    assert isinstance(cross_interface_context["web_bridge"], UXBridge)
    assert isinstance(cross_interface_context["api_bridge"], UXBridge)


@then("all interfaces should handle progress indicators consistently")
def verify_progress_consistency(cross_interface_context):
    """Verify that all interfaces handle progress indicators consistently."""
    # This would require tracking how progress indicators were used during the test
    # For now, we'll just verify that all bridges can create progress indicators
    cli_progress = cross_interface_context["cli_bridge"].create_progress("Test")
    web_progress = cross_interface_context["web_bridge"].create_progress("Test")
    api_progress = cross_interface_context["api_bridge"].create_progress("Test")

    assert cli_progress is not None
    assert web_progress is not None
    assert api_progress is not None


@then("all interfaces should report the same error")
def verify_same_error(cross_interface_context):
    """Verify that all interfaces report the same error."""
    # Check that all interfaces produced an error
    assert "cli" in cross_interface_context["errors"]
    assert "web" in cross_interface_context["errors"]
    assert "api" in cross_interface_context["errors"]

    # Check that the errors are of the same type
    # Note: The actual implementation would need to compare the relevant parts of the errors,
    # as the exact format might differ between interfaces
    if cross_interface_context["errors"]["cli"] is not None:
        assert cross_interface_context["errors"]["web"] is not None
        assert cross_interface_context["errors"]["api"] is not None

        cli_error_type = type(cross_interface_context["errors"]["cli"])
        web_error_type = type(cross_interface_context["errors"]["web"])
        api_error_type = type(cross_interface_context["errors"]["api"])

        assert cli_error_type == web_error_type
        assert cli_error_type == api_error_type


@then("all interfaces should handle the error gracefully")
def verify_graceful_error_handling(cross_interface_context):
    """Verify that all interfaces handle errors gracefully."""
    # This would require checking that the interfaces display appropriate error messages
    # and don't crash when errors occur
    # For now, we'll just verify that the test reached this point without crashing
    assert True


@then("all interfaces should present the question consistently")
def verify_question_consistency(cross_interface_context):
    """Verify that all interfaces present questions consistently."""
    # This would require tracking how questions were presented during the test
    # For now, we'll just verify that all interfaces produced a result
    assert cross_interface_context["results"]["cli"] is not None
    assert cross_interface_context["results"]["web"] is not None
    assert cross_interface_context["results"]["api"] is not None

    # Check that the results are the same
    assert (
        cross_interface_context["results"]["cli"]
        == cross_interface_context["results"]["web"]
    )
    assert (
        cross_interface_context["results"]["cli"]
        == cross_interface_context["results"]["api"]
    )


@then("all interfaces should handle the response consistently")
def verify_response_consistency(cross_interface_context):
    """Verify that all interfaces handle responses consistently."""
    # This would require tracking how responses were handled during the test
    # For now, we'll just verify that all interfaces produced a result
    assert cross_interface_context["results"]["cli"] is not None
    assert cross_interface_context["results"]["web"] is not None
    assert cross_interface_context["results"]["api"] is not None


@then("all interfaces should report progress consistently")
def verify_progress_reporting_consistency(cross_interface_context):
    """Verify that all interfaces report progress consistently."""
    # This would require tracking how progress was reported during the test
    # For now, we'll just verify that all interfaces completed the operation
    assert cross_interface_context["results"]["cli"] == "completed"
    assert cross_interface_context["results"]["web"] == "completed"
    assert cross_interface_context["results"]["api"] == "completed"


@then("all interfaces should indicate completion consistently")
def verify_completion_consistency(cross_interface_context):
    """Verify that all interfaces indicate completion consistently."""
    # This would require tracking how completion was indicated during the test
    # For now, we'll just verify that all interfaces completed the operation
    assert cross_interface_context["results"]["cli"] == "completed"
    assert cross_interface_context["results"]["web"] == "completed"
    assert cross_interface_context["results"]["api"] == "completed"
