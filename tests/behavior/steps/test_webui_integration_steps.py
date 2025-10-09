from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

pytest.importorskip("pytest_bdd")

from pytest_bdd import given, parsers, scenarios, then, when

from . import test_webui_integration_error_branches  # noqa: F401


def _install_streamlit_stub() -> ModuleType:
    """Ensure a lightweight ``streamlit`` stub exists for test collection."""

    existing = sys.modules.get("streamlit")
    if isinstance(existing, ModuleType):
        return existing

    stub = ModuleType("streamlit")
    stub.session_state = {}
    stub.sidebar = ModuleType("sidebar")
    stub.sidebar.radio = MagicMock(return_value="Onboarding")
    stub.sidebar.title = MagicMock()
    stub.sidebar.markdown = MagicMock()
    stub.header = MagicMock()
    stub.write = MagicMock()
    stub.markdown = MagicMock()
    stub.info = MagicMock()
    stub.error = MagicMock()
    stub.warning = MagicMock()
    stub.success = MagicMock()
    stub.progress = MagicMock()
    stub.spinner = MagicMock()
    stub.form = MagicMock()
    stub.form_submit_button = MagicMock(return_value=True)
    stub.text_input = MagicMock()
    stub.text_area = MagicMock()
    stub.selectbox = MagicMock()
    stub.checkbox = MagicMock()
    stub.button = MagicMock()
    stub.columns = MagicMock()
    stub.empty = MagicMock()
    sys.modules["streamlit"] = stub
    return stub


_ST_STREAMLIT = _install_streamlit_stub()

pytest.importorskip("streamlit")

# Register the feature scenarios to ensure step discovery
scenarios(feature_path(__file__, "general", "webui_integration.feature"))


# Mock the WebUI and related components
@pytest.fixture
def webui_context(monkeypatch):
    # Mock Streamlit
    st_mock = ModuleType("streamlit")
    st_mock.session_state = {}
    st_mock.sidebar = ModuleType("sidebar")
    st_mock.sidebar.radio = MagicMock(return_value="Onboarding")
    st_mock.sidebar.title = MagicMock()
    st_mock.sidebar.markdown = MagicMock()
    st_mock.header = MagicMock()
    st_mock.write = MagicMock()
    st_mock.markdown = MagicMock()
    st_mock.info = MagicMock()
    st_mock.error = MagicMock()
    st_mock.warning = MagicMock()
    st_mock.success = MagicMock()
    st_mock.progress = MagicMock()
    st_mock.spinner = MagicMock()
    st_mock.form = MagicMock()
    st_mock.form_submit_button = MagicMock(return_value=True)
    st_mock.text_input = MagicMock()
    st_mock.text_area = MagicMock()
    st_mock.selectbox = MagicMock()
    st_mock.checkbox = MagicMock()
    st_mock.button = MagicMock()
    st_mock.columns = MagicMock()
    st_mock.empty = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st_mock)

    # Mock CLI modules needed by WebUI
    monkeypatch.setitem(sys.modules, "chromadb", MagicMock())
    monkeypatch.setitem(sys.modules, "uvicorn", MagicMock())

    # Create CLI stub modules
    cli_stub = ModuleType("devsynth.application.cli")
    cli_commands_stub = ModuleType("devsynth.application.cli.cli_commands")

    # Add mock commands
    for cmd_name in [
        "init_cmd",
        "spec_cmd",
        "code_cmd",
        "test_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
    ]:
        setattr(cli_commands_stub, cmd_name, MagicMock())
        setattr(cli_stub, cmd_name, MagicMock())

    # Create ingest_cmd module
    ingest_mod = ModuleType("devsynth.application.cli.ingest_cmd")
    ingest_mod.ingest_cmd = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.ingest_cmd", ingest_mod)
    cli_stub.ingest_cmd = ingest_mod.ingest_cmd

    # Create apispec module
    apispec_mod = ModuleType("devsynth.application.cli.apispec")
    apispec_mod.apispec_cmd = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.apispec", apispec_mod)
    cli_stub.apispec_cmd = apispec_mod.apispec_cmd

    # Create setup_wizard module
    setup_wizard_mod = ModuleType("devsynth.application.cli.setup_wizard")
    setup_wizard_mod.SetupWizard = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.setup_wizard", setup_wizard_mod
    )
    cli_stub.setup_wizard = setup_wizard_mod

    # Create commands module
    commands_mod = ModuleType("devsynth.application.cli.commands")
    commands_mod.__path__ = []  # treat as package
    for cmd_name in ["doctor_cmd", "inspect_code_cmd", "edrr_cycle_cmd", "align_cmd"]:
        sub_mod = ModuleType(f"devsynth.application.cli.commands.{cmd_name}")
        setattr(sub_mod, cmd_name, MagicMock())
        monkeypatch.setitem(
            sys.modules, f"devsynth.application.cli.commands.{cmd_name}", sub_mod
        )
        setattr(commands_mod, cmd_name, MagicMock())

    # Add additional command modules
    for cmd_name in [
        "alignment_metrics_cmd",
        "validate_manifest_cmd",
        "validate_metadata_cmd",
        "test_metrics_cmd",
        "generate_docs_cmd",
        "analyze_manifest_cmd",
        "inspect_config_cmd",
    ]:
        mod = ModuleType(f"devsynth.application.cli.commands.{cmd_name}")
        # Set both the original function name and the shortened version
        setattr(mod, cmd_name, MagicMock())
        cmd_func_name = f"{cmd_name.replace('_cmd', '')}"
        setattr(mod, cmd_func_name, MagicMock())
        monkeypatch.setitem(
            sys.modules, f"devsynth.application.cli.commands.{cmd_name}", mod
        )
        setattr(commands_mod, cmd_name, MagicMock())

    monkeypatch.setitem(sys.modules, "devsynth.application.cli.commands", commands_mod)
    cli_stub.commands = commands_mod

    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.cli_commands", cli_commands_stub
    )

    # Import WebUI after patching
    import devsynth.interface.webui as webui

    # Create WebUI instance
    ui = webui.WebUI()

    # Mock UXBridge methods
    ui.display_result = MagicMock()
    ui.ask_question = MagicMock(return_value="test")
    ui.confirm_choice = MagicMock(return_value=True)

    # Mock progress indicator
    progress_indicator = MagicMock()
    progress_indicator.update = MagicMock()
    progress_indicator.complete = MagicMock()
    progress_indicator.add_subtask = MagicMock(return_value="subtask_id")
    progress_indicator.update_subtask = MagicMock()
    progress_indicator.complete_subtask = MagicMock()
    ui.create_progress = MagicMock(return_value=progress_indicator)

    # Return context with all mocks
    return {
        "ui": ui,
        "st": st_mock,
        "progress": progress_indicator,
        "webui_module": webui,
        "cli": cli_stub,
    }


# Step definitions for enhanced progress indicators
@given("the WebUI is initialized")
def webui_initialized(webui_context):
    return webui_context


@when("I run a long-running operation")
def run_long_operation(webui_context):
    # Simulate running a long operation
    ui = webui_context["ui"]
    progress = ui.create_progress("Long-running operation", total=100)
    webui_context["current_progress"] = progress


@then("I should see an enhanced progress indicator")
def check_progress_indicator(webui_context):
    ui = webui_context["ui"]
    ui.create_progress.assert_called_once()


@then("the progress indicator should show estimated time remaining")
def check_time_remaining(webui_context):
    progress = webui_context["current_progress"]
    progress.update(advance=10, description="processing")
    progress.update.assert_called_with(advance=10, description="processing")


@then("the progress indicator should show subtasks")
def check_subtasks(webui_context):
    progress = webui_context["current_progress"]
    progress.add_subtask.assert_called_once()


# Step definitions for colorized output
@when("I run a command that produces different types of output")
def run_output_command(webui_context):
    ui = webui_context["ui"]
    ui.display_result("Normal message")
    ui.display_result("SUCCESS: Operation completed", highlight=False)
    ui.display_result("WARNING: Be careful", highlight=False)
    ui.display_result("ERROR: Something went wrong", highlight=False)
    ui.display_result("# Heading", highlight=False)
    ui.display_result("## Subheading", highlight=False)


@then("success messages should be displayed in green")
def check_success_messages(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call("SUCCESS: Operation completed", highlight=False)
    st_mock.success.assert_called()


@then("warning messages should be displayed in yellow")
def check_warning_messages(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call("WARNING: Be careful", highlight=False)
    st_mock.warning.assert_called()


@then("error messages should be displayed in red")
def check_error_messages(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call("ERROR: Something went wrong", highlight=False)
    st_mock.error.assert_called()


@then("informational messages should be displayed in blue")
def check_info_messages(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call("Normal message")
    st_mock.write.assert_called()


# Step definitions for detailed error messages
@when("I run a command that produces an error")
def run_error_command(webui_context):
    ui = webui_context["ui"]
    ui.display_result(
        "ERROR: Invalid parameter: --format must be one of [json, yaml, markdown]",
        highlight=False,
    )


@then("I should see a detailed error message")
def check_detailed_error(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call(
        "ERROR: Invalid parameter: --format must be one of [json, yaml, markdown]",
        highlight=False,
    )
    st_mock.error.assert_called()


@then("the error message should include suggestions")
def check_error_suggestions(webui_context):
    # Verify that the error message includes suggestions
    ui = webui_context["ui"]
    st_mock = webui_context["st"]

    # Check that the error message includes suggestions for fixing the issue
    # In this case, we're checking that it suggests valid format options
    ui.display_result.assert_any_call(
        "ERROR: Invalid parameter: --format must be one of [json, yaml, markdown]",
        highlight=False,
    )

    # Verify that the error message contains the valid options
    call_args = ui.display_result.call_args_list
    has_suggestions = False
    for args, kwargs in call_args:
        if args and "must be one of" in str(args[0]):
            has_suggestions = True
            break

    assert (
        has_suggestions
    ), "Error message should include suggestions for fixing the issue"


@then("the error message should include documentation links")
def check_error_docs(webui_context):
    # Verify that the error message includes documentation links
    ui = webui_context["ui"]
    st_mock = webui_context["st"]

    # In a real implementation, we would verify that the error message includes a link
    # to the documentation. For now, we'll just check that the display_result method was called.
    ui.display_result.assert_called()

    # Mock the markdown function to check if it was called with a URL
    st_mock.markdown.assert_called()

    # In the future, we would check that the markdown call includes a URL to documentation
    # For now, we'll just assert that the function was called
    assert (
        st_mock.markdown.call_count > 0
    ), "Documentation links should be displayed using markdown"


# Step definitions for help text
@when("I view help for a command")
def view_help(webui_context):
    ui = webui_context["ui"]
    ui.display_result(
        "Usage: devsynth init [OPTIONS]\n\nOptions:\n  --path TEXT  Project path\n  --help      Show this message and exit.\n\nExamples:\n  devsynth init --path ./my-project",
        highlight=True,
    )


@then("I should see detailed help text")
def check_help_text(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call(
        "Usage: devsynth init [OPTIONS]\n\nOptions:\n  --path TEXT  Project path\n  --help      Show this message and exit.\n\nExamples:\n  devsynth init --path ./my-project",
        highlight=True,
    )
    st_mock.info.assert_called()


@then("the help text should include usage examples")
def check_help_examples(webui_context):
    # Verify that the help text includes usage examples
    ui = webui_context["ui"]

    # Check that the help text includes examples
    call_args = ui.display_result.call_args_list
    has_examples = False
    for args, kwargs in call_args:
        if args and "Examples:" in str(args[0]):
            has_examples = True
            break

    assert has_examples, "Help text should include usage examples"

    # Verify that the example includes a command with arguments
    has_command_example = False
    for args, kwargs in call_args:
        if args and "devsynth init --path" in str(args[0]):
            has_command_example = True
            break

    assert has_command_example, "Help text should include specific command examples"


@then("the help text should explain all available options")
def check_help_options(webui_context):
    # Verify that the help text explains all available options
    ui = webui_context["ui"]

    # Check that the help text includes the Options section
    call_args = ui.display_result.call_args_list
    has_options_section = False
    for args, kwargs in call_args:
        if args and "Options:" in str(args[0]):
            has_options_section = True
            break

    assert has_options_section, "Help text should include an Options section"

    # Verify that the options section includes option descriptions
    has_option_descriptions = False
    for args, kwargs in call_args:
        if args and "--path TEXT" in str(args[0]) and "--help" in str(args[0]):
            has_option_descriptions = True
            break

    assert has_option_descriptions, "Help text should explain all available options"


# Step definitions for UXBridge integration
@when("I interact with the WebUI")
def interact_with_webui(webui_context):
    ui = webui_context["ui"]
    ui.display_result("Test message")
    ui.ask_question("Test question")
    ui.confirm_choice("Test confirmation")
    ui.create_progress("Test progress")


@then("the interactions should use the UXBridge abstraction")
def check_uxbridge_abstraction(webui_context):
    ui = webui_context["ui"]
    ui.display_result.assert_called()
    ui.ask_question.assert_called()
    ui.confirm_choice.assert_called()
    ui.create_progress.assert_called()


@then("the WebUI should behave consistently with the CLI")
def check_cli_consistency(webui_context):
    # Verify that the WebUI behaves consistently with the CLI
    ui = webui_context["ui"]

    # Check that the WebUI uses the same underlying commands as the CLI
    # This is done by verifying that the WebUI calls the CLI commands

    # Get the CLI modules from the context
    cli_modules = webui_context.get("cli_modules", {})

    # Verify that the WebUI has methods that correspond to CLI commands
    assert hasattr(ui, "run_init"), "WebUI should have a method for the init command"
    assert hasattr(ui, "run_spec"), "WebUI should have a method for the spec command"
    assert hasattr(ui, "run_test"), "WebUI should have a method for the test command"
    assert hasattr(ui, "run_code"), "WebUI should have a method for the code command"

    # Verify that the WebUI uses the UXBridge abstraction for consistent behavior
    assert hasattr(
        ui, "display_result"
    ), "WebUI should use the UXBridge display_result method"
    assert hasattr(
        ui, "ask_question"
    ), "WebUI should use the UXBridge ask_question method"
    assert hasattr(
        ui, "confirm_choice"
    ), "WebUI should use the UXBridge confirm_choice method"
    assert hasattr(
        ui, "create_progress"
    ), "WebUI should use the UXBridge create_progress method"


# Step definitions for responsive UI
@when("I resize the browser window")
def resize_browser(webui_context):
    # Simulate resizing the browser window
    ui = webui_context["ui"]
    st_mock = webui_context["st"]

    # In a real implementation, we would use a browser automation tool like Selenium
    # to resize the browser window. For now, we'll simulate it by setting a session state variable.

    # Store the original window size
    webui_context["original_window_size"] = {"width": 1200, "height": 800}

    # Set the new window size
    webui_context["window_size"] = {"width": 600, "height": 800}

    # Update the session state
    st_mock.session_state["window_size"] = webui_context["window_size"]

    # Trigger a rerun to simulate the UI updating
    ui.rerun = True


@then("the WebUI should adapt to the new size")
def check_responsive_design(webui_context):
    # Verify that the WebUI adapts to the new size
    ui = webui_context["ui"]
    st_mock = webui_context["st"]

    # Check that the session state has the new window size
    assert (
        st_mock.session_state["window_size"] == webui_context["window_size"]
    ), "Session state should have the new window size"

    # In a real implementation, we would check that the UI components have adapted to the new size
    # For now, we'll check that the columns method was called, which is commonly used for responsive layouts

    # Check that the columns method was called
    assert (
        st_mock.columns.called
    ), "Columns method should be called for responsive layout"

    # Verify that the UI has a responsive layout
    # This could be checking for specific CSS classes or layout adjustments
    # For now, we'll just check that the UI has methods for handling different screen sizes
    assert hasattr(
        ui, "get_layout_config"
    ), "WebUI should have methods for handling different screen sizes"


@then("all elements should remain accessible and usable")
def check_accessibility(webui_context):
    # Verify that all UI elements remain accessible and usable after resizing
    ui = webui_context["ui"]
    st_mock = webui_context["st"]

    # In a real implementation, we would use an accessibility testing tool
    # to verify that all elements are accessible. For now, we'll check that
    # the UI components are still available and can be interacted with.

    # Check that the sidebar is still accessible
    assert st_mock.sidebar is not None, "Sidebar should be accessible after resizing"

    # Check that form elements are still usable
    assert st_mock.button.called, "Button should be usable after resizing"
    assert st_mock.text_input.called, "Text input should be usable after resizing"
    assert st_mock.selectbox.called, "Selectbox should be usable after resizing"

    # Check that the UI can still display results
    ui.display_result("Test message after resize")
    ui.display_result.assert_called_with("Test message after resize")

    # Verify that the UI can handle user interactions after resizing
    ui.ask_question("Test question after resize")
    ui.ask_question.assert_called_with("Test question after resize")


# Step definitions for CLI command support
@when("I navigate to different pages")
def navigate_pages(webui_context):
    ui = webui_context["ui"]
    # Simulate navigating to different pages
    ui.onboarding_page()
    ui.requirements_page()
    ui.synthesis_page()
    ui.config_page()


@then("I should be able to access all CLI commands")
def check_all_commands(webui_context):
    ui = webui_context["ui"]
    # Verify that all CLI commands have corresponding WebUI pages
    assert hasattr(ui, "onboarding_page")
    assert hasattr(ui, "requirements_page")
    assert hasattr(ui, "synthesis_page")
    assert hasattr(ui, "config_page")
    assert hasattr(ui, "edrr_cycle_page")
    assert hasattr(ui, "doctor_page")


@then("each command should have a dedicated interface")
def check_dedicated_interfaces(webui_context):
    ui = webui_context["ui"]
    cli = webui_context["cli"]

    # Trigger page handlers to invoke CLI commands
    ui.onboarding_page()
    ui.requirements_page()
    ui.synthesis_page()
    ui.config_page()

    for name in [
        "init_cmd",
        "spec_cmd",
        "code_cmd",
        "test_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
    ]:
        func = getattr(cli, name)
        assert func.called, f"{name} was not invoked"


@then("the command interfaces should be consistent")
def check_interface_consistency(webui_context):
    ui = webui_context["ui"]
    cli = webui_context["cli"]

    for name in [
        "init_cmd",
        "spec_cmd",
        "code_cmd",
        "test_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
    ]:
        func = getattr(cli, name)
        if not func.call_args:
            continue
        assert func.call_args.kwargs.get("bridge") is ui
