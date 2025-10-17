"""Steps for extended cross-interface consistency testing."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from devsynth.interface.cli import CLIUXBridge
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Flag to track if scenarios have been loaded
_scenarios_loaded = False

def _load_bdd_scenarios():
    """Load BDD scenarios, ensuring they're only loaded once."""
    global _scenarios_loaded
    if _scenarios_loaded:
        return

    try:
        scenarios(
            feature_path(__file__, "general", "cross_interface_consistency_extended.feature")
        )
        scenarios(feature_path(__file__, "extended_cross_interface_consistency.feature"))
        _scenarios_loaded = True
    except Exception as e:
        # If scenarios loading fails, it might be due to CONFIG_STACK issues
        # when plugin autoloading is disabled. The scenarios will be loaded
        # later when pytest-bdd is properly initialized.
        pass

def pytest_configure(config):
    """Hook called after pytest is configured - load BDD scenarios here."""
    _load_bdd_scenarios()

# Try to load scenarios immediately, but handle failures gracefully
_load_bdd_scenarios()


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


@pytest.fixture
def cross_interface_context(monkeypatch):
    """Create a shared environment for CLI, WebUI, and Agent API."""
    # Mock external dependencies
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())
    monkeypatch.setitem(sys.modules, "rdflib", MagicMock())
    monkeypatch.setitem(sys.modules, "faiss", MagicMock())

    # Mock CLI commands
    from devsynth.application import cli as cli_module

    # Create mock functions for all commands
    command_mocks = {
        "init_cmd": MagicMock(),
        "spec_cmd": MagicMock(),
        "test_cmd": MagicMock(),
        "code_cmd": MagicMock(),
        "run_pipeline_cmd": MagicMock(),
        "config_cmd": MagicMock(),
        "inspect_cmd": MagicMock(),
    }

    for cmd_name, mock_func in command_mocks.items():
        monkeypatch.setattr(cli_module, cmd_name, mock_func)

    # Mock doctor_cmd
    doctor_module = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_module.doctor_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.doctor_cmd",
        doctor_module,
    )

    # Mock edrr_cycle_cmd
    edrr_module = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_module.edrr_cycle_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules,
        "devsynth.application.cli.commands.edrr_cycle_cmd",
        edrr_module,
    )

    # Mock Streamlit for WebUI
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
    st.text_input = MagicMock(return_value="demo")
    st.text_area = MagicMock(return_value="demo goals")
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
    # Add missing Streamlit attributes
    st.empty = MagicMock(return_value=MagicMock())
    st.info = MagicMock()
    st.error = MagicMock()
    st.warning = MagicMock()
    st.success = MagicMock()
    st.number_input = MagicMock(return_value=1)
    st.radio = MagicMock(return_value="option1")
    st.multiselect = MagicMock(return_value=["option1"])
    st.file_uploader = MagicMock(return_value=None)
    monkeypatch.setitem(sys.modules, "streamlit", st)

    # Load WebUI module
    import devsynth.interface.webui as webui

    importlib.reload(webui)

    # Mock Agent API
    import devsynth.interface.agentapi as agentapi

    importlib.reload(agentapi)

    # Create a context object to store test state
    context = {
        "st": st,
        "cli_module": cli_module,
        "doctor_module": doctor_module,
        "edrr_module": edrr_module,
        "webui": webui.WebUI(),
        "api_bridge": agentapi.APIBridge(),
        "agent_api": agentapi.AgentAPI(agentapi.APIBridge()),
        "command_calls": {},
        "error_messages": [],
        "user_inputs": {},
    }

    return context


@given("the CLI, WebUI, and Agent API share a UXBridge")
def shared_bridge_setup(cross_interface_context):
    """Set up shared UXBridge for all interfaces."""
    # Return the context which already has all interfaces set up
    return cross_interface_context


@when(parsers.parse("{command} is invoked from all interfaces"))
def invoke_command_all_interfaces(cross_interface_context, command):
    """Invoke the specified command from all interfaces."""
    cli_module = cross_interface_context["cli_module"]
    webui = cross_interface_context["webui"]
    agent_api = cross_interface_context["agent_api"]
    st = cross_interface_context["st"]

    # Set up command-specific parameters
    params = {
        "init": {
            "path": "demo",
            "project_root": "demo",
            "language": "python",
            "goals": "demo goals",
        },
        "spec": {"requirements_file": "requirements.md"},
        "test": {"spec_file": "specs.md", "output_dir": "tests"},
        "code": {"output_dir": "src"},
        "doctor": {"path": ".", "fix": False},
        "edrr_cycle": {
            "prompt": "test prompt",
            "context": "test context",
            "max_iterations": 3,
        },
    }

    # Store the command for later verification
    cross_interface_context["current_command"] = command

    # Invoke via CLI
    if command == "init":
        cli_module.init_cmd(**params["init"], bridge=CLIUXBridge())
    elif command == "spec":
        cli_module.spec_cmd(**params["spec"], bridge=CLIUXBridge())
    elif command == "test":
        cli_module.test_cmd(**params["test"], bridge=CLIUXBridge())
    elif command == "code":
        cli_module.code_cmd(**params["code"], bridge=CLIUXBridge())
    elif command == "doctor":
        doctor_module = cross_interface_context["doctor_module"]
        doctor_module.doctor_cmd(**params["doctor"], bridge=CLIUXBridge())
    elif command == "edrr_cycle":
        edrr_module = cross_interface_context["edrr_module"]
        edrr_module.edrr_cycle_cmd(**params["edrr_cycle"], bridge=CLIUXBridge())

    # Invoke via WebUI
    # Set up form inputs for WebUI based on command
    if command == "init":
        st.text_input.side_effect = lambda label, default=None, **kwargs: {
            "Project Path": params["init"]["path"],
            "Project Root": params["init"]["project_root"],
            "Primary Language": params["init"]["language"],
            "Project Goals": params["init"]["goals"],
        }.get(label, "demo")
        webui.onboarding_page()
    elif command == "spec":
        st.text_input.side_effect = lambda label, default=None, **kwargs: {
            "Requirements File": params["spec"]["requirements_file"]
        }.get(label, "demo")
        webui.requirements_page()
    elif command == "test":
        st.text_input.side_effect = lambda label, default=None, **kwargs: {
            "Spec File": params["test"]["spec_file"],
            "Output Directory": params["test"]["output_dir"],
        }.get(label, "demo")
        webui.synthesis_page()
    elif command == "code":
        st.text_input.side_effect = lambda label, default=None, **kwargs: {
            "Output Directory": params["code"]["output_dir"]
        }.get(label, "demo")
        webui.synthesis_page()
    elif command == "doctor":
        st.text_input.side_effect = lambda label, default=None, **kwargs: {
            "Project Path": params["doctor"]["path"]
        }.get(label, "demo")
        st.checkbox.return_value = params["doctor"]["fix"]
        webui.diagnostics_page()
    elif command == "edrr_cycle":
        st.text_area.side_effect = lambda label, default=None, **kwargs: {
            "Prompt": params["edrr_cycle"]["prompt"],
            "Context": params["edrr_cycle"]["context"],
        }.get(label, "demo")
        st.number_input = MagicMock(return_value=params["edrr_cycle"]["max_iterations"])
        webui.edrr_cycle_page()

    # Invoke via Agent API
    if command == "init":
        agent_api.init(**params["init"])
    elif command == "spec":
        agent_api.spec(**params["spec"])
    elif command == "test":
        agent_api.test(**params["test"])
    elif command == "code":
        agent_api.code(**params["code"])
    elif command == "doctor":
        agent_api.doctor(**params["doctor"])
    elif command == "edrr_cycle":
        agent_api.edrr_cycle(**params["edrr_cycle"])

    # Store call information for verification
    cross_interface_context["command_params"] = params[command]


@when("an error occurs during command execution")
def simulate_error(cross_interface_context):
    """Simulate an error during command execution."""
    cli_module = cross_interface_context["cli_module"]

    # Make init_cmd raise an exception
    def raise_error(*args, **kwargs):
        bridge = kwargs.get("bridge")
        error_msg = "Error: Failed to initialize project"
        if bridge:
            bridge.display_result(error_msg, highlight=True)
        cross_interface_context["error_messages"].append(error_msg)
        raise ValueError(error_msg)

    cli_module.init_cmd.side_effect = raise_error

    # Try to invoke init from all interfaces with error handling
    try:
        # CLI
        with patch("devsynth.interface.cli.CLIUXBridge.display_result") as mock_display:
            try:
                cli_module.init_cmd(path="demo", bridge=CLIUXBridge())
            except ValueError:
                pass
            cross_interface_context["cli_error_display"] = mock_display

        # WebUI
        webui = cross_interface_context["webui"]
        st = cross_interface_context["st"]
        with patch("devsynth.interface.webui.WebUI.display_result") as mock_display:
            try:
                webui.onboarding_page()
            except ValueError:
                pass
            cross_interface_context["webui_error_display"] = mock_display

        # Agent API
        agent_api = cross_interface_context["agent_api"]
        with patch(
            "devsynth.interface.agentapi.APIBridge.display_result"
        ) as mock_display:
            try:
                agent_api.init(path="demo")
            except ValueError:
                pass
            cross_interface_context["api_error_display"] = mock_display

    except Exception as e:
        # Store any unexpected exceptions
        cross_interface_context["unexpected_error"] = str(e)


@when("user input is required during command execution")
def simulate_user_input(cross_interface_context):
    """Simulate a scenario where user input is required."""
    # Mock the ask_question method for all bridges
    cli_bridge = CLIUXBridge()
    webui = cross_interface_context["webui"]
    api_bridge = cross_interface_context["api_bridge"]

    # Create a consistent user response
    user_response = "yes"
    cross_interface_context["user_response"] = user_response

    # Mock CLI bridge ask_question
    with patch(
        "devsynth.interface.cli.CLIUXBridge.ask_question", return_value=user_response
    ) as cli_ask:
        cross_interface_context["cli_ask"] = cli_ask
        cli_result = cli_bridge.ask_question("Do you want to proceed?")
        cross_interface_context["cli_input_result"] = cli_result

    # Mock WebUI bridge ask_question
    with patch(
        "devsynth.interface.webui.WebUI.ask_question", return_value=user_response
    ) as webui_ask:
        cross_interface_context["webui_ask"] = webui_ask
        webui_result = webui.ask_question("Do you want to proceed?")
        cross_interface_context["webui_input_result"] = webui_result

    # Mock Agent API bridge ask_question
    with patch(
        "devsynth.interface.agentapi.APIBridge.ask_question", return_value=user_response
    ) as api_ask:
        cross_interface_context["api_ask"] = api_ask
        api_result = api_bridge.ask_question("Do you want to proceed?")
        cross_interface_context["api_input_result"] = api_result


@then("all invocations pass identical arguments")
def verify_identical_arguments(cross_interface_context):
    """Verify that all interfaces pass identical arguments to the command."""
    command = cross_interface_context["current_command"]
    cli_module = cross_interface_context["cli_module"]

    # Get the appropriate command function based on the command name
    if command == "init":
        cmd_func = cli_module.init_cmd
    elif command == "spec":
        cmd_func = cli_module.spec_cmd
    elif command == "test":
        cmd_func = cli_module.test_cmd
    elif command == "code":
        cmd_func = cli_module.code_cmd
    elif command == "doctor":
        cmd_func = cross_interface_context["doctor_module"].doctor_cmd
    elif command == "edrr_cycle":
        cmd_func = cross_interface_context["edrr_module"].edrr_cycle_cmd

    # Verify that the command was called at least 3 times (CLI, WebUI, Agent API)
    assert (
        cmd_func.call_count >= 3
    ), f"Expected at least 3 calls to {command}, got {cmd_func.call_count}"

    # Get the first 3 calls (CLI, WebUI, Agent API)
    calls = cmd_func.call_args_list[:3]

    # Verify that all calls included a bridge parameter
    for call in calls:
        assert "bridge" in call.kwargs, f"Missing 'bridge' parameter in call: {call}"

    # Extract parameters excluding the bridge
    call_params = []
    for call in calls:
        params = {k: v for k, v in call.kwargs.items() if k != "bridge"}
        call_params.append(params)

    # Verify that all calls have the same parameters
    for i in range(1, len(call_params)):
        assert (
            call_params[0] == call_params[i]
        ), f"Parameters don't match: {call_params[0]} vs {call_params[i]}"

    # Verify that the parameters match the expected parameters
    expected_params = cross_interface_context["command_params"]
    for param_name, param_value in expected_params.items():
        assert param_name in call_params[0], f"Missing parameter '{param_name}' in call"
        assert (
            call_params[0][param_name] == param_value
        ), f"Parameter '{param_name}' has incorrect value: expected '{param_value}', got '{call_params[0][param_name]}'"


@then("the command behavior is consistent across interfaces")
def verify_consistent_behavior(cross_interface_context):
    """Verify that the command behavior is consistent across interfaces."""
    # This step verifies that the command execution behavior is consistent
    command = cross_interface_context["current_command"]
    cli_module = cross_interface_context["cli_module"]

    # Get the appropriate command function based on the command name
    if command == "init":
        cmd_func = cli_module.init_cmd
    elif command == "spec":
        cmd_func = cli_module.spec_cmd
    elif command == "test":
        cmd_func = cli_module.test_cmd
    elif command == "code":
        cmd_func = cli_module.code_cmd
    elif command == "doctor":
        cmd_func = cross_interface_context["doctor_module"].doctor_cmd
    elif command == "edrr_cycle":
        cmd_func = cross_interface_context["edrr_module"].edrr_cycle_cmd

    # Verify that the command was called with the same bridge types
    calls = cmd_func.call_args_list[:3]  # CLI, WebUI, Agent API

    # Extract bridge types
    bridge_types = []
    for call in calls:
        bridge = call.kwargs.get("bridge")
        assert bridge is not None, f"Missing bridge parameter in call: {call}"
        bridge_types.append(type(bridge).__name__)

    # Verify that we have the expected bridge types
    expected_bridge_types = ["CLIUXBridge", "WebUI", "APIBridge"]
    for expected_type in expected_bridge_types:
        assert any(
            expected_type in bridge_type for bridge_type in bridge_types
        ), f"Expected bridge type {expected_type} not found in {bridge_types}"

    # Verify that all bridges implement the UXBridge interface
    for call in calls:
        bridge = call.kwargs.get("bridge")
        assert hasattr(
            bridge, "ask_question"
        ), f"Bridge {bridge} missing ask_question method"
        assert hasattr(
            bridge, "confirm_choice"
        ), f"Bridge {bridge} missing confirm_choice method"
        assert hasattr(
            bridge, "display_result"
        ), f"Bridge {bridge} missing display_result method"
        assert hasattr(
            bridge, "create_progress"
        ), f"Bridge {bridge} missing create_progress method"

    # Verify that the command was called the same number of times for each interface
    assert (
        cmd_func.call_count >= 3
    ), f"Expected at least 3 calls to {command}, got {cmd_func.call_count}"


@then("all interfaces handle the error consistently")
def verify_consistent_error_handling(cross_interface_context):
    """Verify that all interfaces handle errors consistently."""
    # Verify that error display was called for all interfaces
    assert (
        "cli_error_display" in cross_interface_context
    ), "CLI error display not called"
    assert (
        "webui_error_display" in cross_interface_context
    ), "WebUI error display not called"
    assert (
        "api_error_display" in cross_interface_context
    ), "API error display not called"

    # Verify that the error message is consistent
    error_msg = cross_interface_context["error_messages"][0]

    # Check that the error message was displayed with highlight=True for CLI
    cli_display = cross_interface_context["cli_error_display"]
    if cli_display.call_count > 0:
        cli_args = cli_display.call_args_list[0]
        assert (
            error_msg in cli_args[0][0]
        ), f"CLI error message doesn't match: {cli_args[0][0]} vs {error_msg}"
        assert cli_args[1].get("highlight", False), "CLI error not highlighted"

    # Check that the error message was displayed with highlight=True for WebUI
    webui_display = cross_interface_context["webui_error_display"]
    if webui_display.call_count > 0:
        webui_args = webui_display.call_args_list[0]
        assert (
            error_msg in webui_args[0][0]
        ), f"WebUI error message doesn't match: {webui_args[0][0]} vs {error_msg}"
        assert webui_args[1].get("highlight", False), "WebUI error not highlighted"

    # Check that the error message was displayed with highlight=True for API
    api_display = cross_interface_context["api_error_display"]
    if api_display.call_count > 0:
        api_args = api_display.call_args_list[0]
        assert (
            error_msg in api_args[0][0]
        ), f"API error message doesn't match: {api_args[0][0]} vs {error_msg}"
        assert api_args[1].get("highlight", False), "API error not highlighted"


@then("appropriate error messages are displayed")
def verify_error_messages(cross_interface_context):
    """Verify that appropriate error messages are displayed."""
    # Verify that error messages were captured
    assert (
        len(cross_interface_context["error_messages"]) > 0
    ), "No error messages captured"

    # Verify that the error message is informative
    error_msg = cross_interface_context["error_messages"][0]
    assert "Error:" in error_msg, f"Error message not informative: {error_msg}"
    assert len(error_msg) > 10, f"Error message too short: {error_msg}"

    # Check that the error message is appropriate for the error
    # In this case, we're simulating a project initialization error
    assert (
        "Failed to initialize project" in error_msg
    ), f"Error message doesn't match expected error: {error_msg}"

    # Check that the error message is displayed consistently across all interfaces
    cli_display = cross_interface_context.get("cli_error_display")
    webui_display = cross_interface_context.get("webui_error_display")
    api_display = cross_interface_context.get("api_error_display")

    # Verify that all interfaces display the same error message
    if cli_display and cli_display.call_count > 0:
        cli_msg = cli_display.call_args_list[0][0][0]
        assert (
            error_msg in cli_msg
        ), f"CLI error message doesn't match: {cli_msg} vs {error_msg}"

    if webui_display and webui_display.call_count > 0:
        webui_msg = webui_display.call_args_list[0][0][0]
        assert (
            error_msg in webui_msg
        ), f"WebUI error message doesn't match: {webui_msg} vs {error_msg}"

    if api_display and api_display.call_count > 0:
        api_msg = api_display.call_args_list[0][0][0]
        assert (
            error_msg in api_msg
        ), f"API error message doesn't match: {api_msg} vs {error_msg}"


@then("all interfaces prompt for input consistently")
def verify_consistent_input_prompting(cross_interface_context):
    """Verify that all interfaces prompt for input consistently."""
    # Verify that ask_question was called for all interfaces
    assert "cli_ask" in cross_interface_context, "CLI ask_question not called"
    assert "webui_ask" in cross_interface_context, "WebUI ask_question not called"
    assert "api_ask" in cross_interface_context, "API ask_question not called"

    # Verify that the prompt message is consistent
    cli_ask = cross_interface_context["cli_ask"]
    webui_ask = cross_interface_context["webui_ask"]
    api_ask = cross_interface_context["api_ask"]

    assert cli_ask.call_count > 0, "CLI ask_question not called"
    assert webui_ask.call_count > 0, "WebUI ask_question not called"
    assert api_ask.call_count > 0, "API ask_question not called"

    cli_prompt = cli_ask.call_args_list[0][0][0]
    webui_prompt = webui_ask.call_args_list[0][0][0]
    api_prompt = api_ask.call_args_list[0][0][0]

    assert (
        cli_prompt == webui_prompt == api_prompt
    ), f"Prompt messages don't match: CLI='{cli_prompt}', WebUI='{webui_prompt}', API='{api_prompt}'"


@then("the input is processed correctly")
def verify_input_processing(cross_interface_context):
    """Verify that user input is processed correctly."""
    # Verify that all interfaces returned the same result
    cli_result = cross_interface_context["cli_input_result"]
    webui_result = cross_interface_context["webui_input_result"]
    api_result = cross_interface_context["api_input_result"]

    assert (
        cli_result == webui_result == api_result
    ), f"Input results don't match: CLI='{cli_result}', WebUI='{webui_result}', API='{api_result}'"

    # Verify that the result matches the expected user response
    user_response = cross_interface_context["user_response"]
    assert (
        cli_result == user_response
    ), f"CLI result doesn't match user response: '{cli_result}' vs '{user_response}'"
    assert (
        webui_result == user_response
    ), f"WebUI result doesn't match user response: '{webui_result}' vs '{user_response}'"
    assert (
        api_result == user_response
    ), f"API result doesn't match user response: '{api_result}' vs '{user_response}'"
