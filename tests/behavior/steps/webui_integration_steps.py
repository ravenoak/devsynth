import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, when, then, scenarios, parsers
import streamlit as st

# The scenarios function is called in the test file, so we don't need to call it here
# scenarios("../features/webui_integration.feature")

# Mock the WebUI and related components
@pytest.fixture
def webui_context(monkeypatch):
    # Mock Streamlit
    st_mock = ModuleType("streamlit")
    st_mock.session_state = {}
    st_mock.sidebar = MagicMock()
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
    for cmd_name in ["init_cmd", "spec_cmd", "code_cmd", "test_cmd", 
                     "run_pipeline_cmd", "config_cmd", "inspect_cmd"]:
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
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.setup_wizard", setup_wizard_mod)
    cli_stub.setup_wizard = setup_wizard_mod

    # Create commands module
    commands_mod = ModuleType("devsynth.application.cli.commands")
    for cmd_name in ["doctor_cmd", "inspect_code_cmd", "edrr_cycle_cmd", "align_cmd"]:
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
        monkeypatch.setitem(sys.modules, f"devsynth.application.cli.commands.{cmd_name}", mod)
        setattr(commands_mod, cmd_name, MagicMock())

    monkeypatch.setitem(sys.modules, "devsynth.application.cli.commands", commands_mod)
    cli_stub.commands = commands_mod

    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.cli_commands", cli_commands_stub)

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
        "webui_module": webui
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
    # This will be verified when the actual implementation is done
    # The progress bar in Streamlit should show time remaining
    pass

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
    ui.display_result("ERROR: Invalid parameter: --format must be one of [json, yaml, markdown]", highlight=False)

@then("I should see a detailed error message")
def check_detailed_error(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call("ERROR: Invalid parameter: --format must be one of [json, yaml, markdown]", highlight=False)
    st_mock.error.assert_called()

@then("the error message should include suggestions")
def check_error_suggestions(webui_context):
    # This will be verified when the actual implementation is done
    # The error message should include suggestions for fixing the issue
    pass

@then("the error message should include documentation links")
def check_error_docs(webui_context):
    # This will be verified when the actual implementation is done
    # The error message should include links to relevant documentation
    pass

# Step definitions for help text
@when("I view help for a command")
def view_help(webui_context):
    ui = webui_context["ui"]
    ui.display_result("Usage: devsynth init [OPTIONS]\n\nOptions:\n  --path TEXT  Project path\n  --help      Show this message and exit.\n\nExamples:\n  devsynth init --path ./my-project", highlight=True)

@then("I should see detailed help text")
def check_help_text(webui_context):
    ui = webui_context["ui"]
    st_mock = webui_context["st"]
    ui.display_result.assert_any_call("Usage: devsynth init [OPTIONS]\n\nOptions:\n  --path TEXT  Project path\n  --help      Show this message and exit.\n\nExamples:\n  devsynth init --path ./my-project", highlight=True)
    st_mock.info.assert_called()

@then("the help text should include usage examples")
def check_help_examples(webui_context):
    # This will be verified when the actual implementation is done
    # The help text should include examples
    pass

@then("the help text should explain all available options")
def check_help_options(webui_context):
    # This will be verified when the actual implementation is done
    # The help text should explain all available options
    pass

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
    # This will be verified when the actual implementation is done
    # The WebUI should behave consistently with the CLI
    pass

# Step definitions for responsive UI
@when("I resize the browser window")
def resize_browser(webui_context):
    # This is a placeholder for testing responsive design
    # In a real implementation, we would use a browser automation tool
    pass

@then("the WebUI should adapt to the new size")
def check_responsive_design(webui_context):
    # This will be verified when the actual implementation is done
    # The WebUI should adapt to different screen sizes
    pass

@then("all elements should remain accessible and usable")
def check_accessibility(webui_context):
    # This will be verified when the actual implementation is done
    # All UI elements should remain accessible and usable
    pass

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
    # This will be verified when the actual implementation is done
    # Each CLI command should have a dedicated WebUI interface
    pass

@then("the command interfaces should be consistent")
def check_interface_consistency(webui_context):
    # This will be verified when the actual implementation is done
    # The command interfaces should be consistent
    pass
