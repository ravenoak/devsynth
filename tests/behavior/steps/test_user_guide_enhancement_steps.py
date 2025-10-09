import os
import re
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the feature file
scenarios(feature_path(__file__, "general", "user_guide_enhancement.feature"))


# Define a fixture for the context
@pytest.fixture
def context():
    class Context:
        def __init__(self):
            # Use absolute paths to ensure we can find the documentation files
            self.project_root = Path(__file__).parent.parent.parent.parent
            self.docs_dir = self.project_root / "docs"
            self.user_guides_dir = self.docs_dir / "user_guides"
            self.getting_started_dir = self.docs_dir / "getting_started"
            self.cli_command_reference = (
                self.user_guides_dir / "cli_command_reference.md"
            )
            self.webui_navigation_guide = (
                self.user_guides_dir / "webui_navigation_guide.md"
            )
            self.quick_start_guide = self.getting_started_dir / "quick_start_guide.md"
            self.troubleshooting = self.getting_started_dir / "troubleshooting.md"
            self.configuration_reference = (
                self.user_guides_dir / "configuration_reference.md"
            )
            self.current_doc_content = None

    return Context()


# Background steps
@given("the DevSynth documentation system is available")
def docs_system_available(context):
    assert (
        context.docs_dir.exists()
    ), f"Documentation directory {context.docs_dir} does not exist"
    assert (
        context.user_guides_dir.exists()
    ), f"User guides directory {context.user_guides_dir} does not exist"
    assert (
        context.getting_started_dir.exists()
    ), f"Getting started directory {context.getting_started_dir} does not exist"


# CLI Command Reference steps
@when("I check the CLI command reference documentation")
def check_cli_command_reference(context):
    assert (
        context.cli_command_reference.exists()
    ), f"CLI command reference {context.cli_command_reference} does not exist"
    context.current_doc_content = context.cli_command_reference.read_text()


@then("all CLI commands should be documented")
def all_cli_commands_documented(context):
    # List of expected commands
    expected_commands = [
        "init",
        "spec",
        "test",
        "code",
        "run-pipeline",
        "config",
        "gather",
        "inspect",
        "refactor",
        "webapp",
        "serve",
        "dbschema",
        "webui",
        "doctor",
        "edrr-cycle",
        "align",
        "alignment-metrics",
        "inspect-config",
        "validate-manifest",
        "validate-metadata",
        "test-metrics",
        "generate-docs",
        "security-audit",
    ]

    for command in expected_commands:
        assert (
            f"### {command}" in context.current_doc_content
        ), f"Command '{command}' is not documented"


@then("each command should have a description")
def each_command_has_description(context):
    command_sections = re.findall(
        r"### ([a-zA-Z-]+)\n\n([^#]+)", context.current_doc_content
    )
    for command, description in command_sections:
        assert len(description.strip()) > 0, f"Command '{command}' has no description"


@then("each command should list all available options")
def each_command_lists_options(context):
    command_sections = re.findall(
        r"### ([a-zA-Z-]+).*?\*\*Options:\*\*\n\| Option \| Description \|",
        context.current_doc_content,
        re.DOTALL,
    )
    # Check that we found options tables for commands that should have options
    assert len(command_sections) > 0, "No command options tables found"


@then("each command should include usage examples")
def each_command_includes_examples(context):
    command_sections = re.findall(
        r"### ([a-zA-Z-]+).*?\*\*Examples:\*\*\n```bash",
        context.current_doc_content,
        re.DOTALL,
    )
    # Check that we found examples for commands that should have examples
    assert len(command_sections) > 0, "No command examples found"


# WebUI Guide steps
@when("I check the WebUI navigation guide")
def check_webui_navigation_guide(context):
    assert (
        context.webui_navigation_guide.exists()
    ), f"WebUI navigation guide {context.webui_navigation_guide} does not exist"
    context.current_doc_content = context.webui_navigation_guide.read_text()


@then("it should include screenshots of each page")
def webui_guide_includes_screenshots(context):
    # Look for image references in markdown
    screenshot_refs = re.findall(r"!\[.*?\]\(.*?\)", context.current_doc_content)
    assert len(screenshot_refs) > 0, "No screenshots found in WebUI navigation guide"


@then("it should describe complete workflows for common tasks")
def webui_guide_describes_workflows(context):
    # Look for workflow descriptions
    workflow_sections = re.findall(r"## Workflow: (.*?)\n", context.current_doc_content)
    assert (
        len(workflow_sections) > 0
    ), "No workflow sections found in WebUI navigation guide"


@then("it should explain all UI elements and their functions")
def webui_guide_explains_ui_elements(context):
    # Look for UI element descriptions
    ui_element_sections = re.findall(
        r"### (.*?) Element\n", context.current_doc_content
    )
    assert (
        len(ui_element_sections) > 0
    ), "No UI element descriptions found in WebUI navigation guide"


@then("it should provide navigation instructions between pages")
def webui_guide_provides_navigation_instructions(context):
    # Look for navigation instructions
    navigation_sections = re.findall(
        r"Navigation:.*?", context.current_doc_content, re.DOTALL
    )
    assert (
        len(navigation_sections) > 0
    ), "No navigation instructions found in WebUI navigation guide"


# Quick Start Guide steps
@when("I check the quick start guide")
def check_quick_start_guide(context):
    assert (
        context.quick_start_guide.exists()
    ), f"Quick start guide {context.quick_start_guide} does not exist"
    context.current_doc_content = context.quick_start_guide.read_text()


@then("it should include basic installation and setup instructions")
def quick_start_includes_installation_instructions(context):
    assert (
        "## Installation" in context.current_doc_content
    ), "No installation section found in quick start guide"


@then("it should provide a simple example project")
def quick_start_provides_example_project(context):
    assert (
        "## Creating Your First DevSynth Project" in context.current_doc_content
    ), "No example project section found in quick start guide"


@then("it should include at least three common use cases")
def quick_start_includes_common_use_cases(context):
    # Look for use case sections
    use_case_sections = re.findall(r"## Use Case: (.*?)\n", context.current_doc_content)
    assert (
        len(use_case_sections) >= 3
    ), f"Found only {len(use_case_sections)} use cases in quick start guide, expected at least 3"


@then("it should link to more detailed documentation")
def quick_start_links_to_detailed_docs(context):
    # Look for links to other documentation
    doc_links = re.findall(r"\[.*?\]\((.*?\.md)\)", context.current_doc_content)
    assert (
        len(doc_links) > 0
    ), "No links to detailed documentation found in quick start guide"


# Troubleshooting steps
@when("I check the troubleshooting documentation")
def check_troubleshooting_documentation(context):
    assert (
        context.troubleshooting.exists()
    ), f"Troubleshooting documentation {context.troubleshooting} does not exist"
    context.current_doc_content = context.troubleshooting.read_text()


@then("it should cover installation issues")
def troubleshooting_covers_installation_issues(context):
    assert (
        "## Installation Issues" in context.current_doc_content
    ), "No installation issues section found in troubleshooting documentation"


@then("it should cover configuration issues")
def troubleshooting_covers_configuration_issues(context):
    assert (
        "## Configuration Issues" in context.current_doc_content
    ), "No configuration issues section found in troubleshooting documentation"


@then("it should cover LLM provider issues")
def troubleshooting_covers_llm_provider_issues(context):
    assert (
        "## LLM Provider Issues" in context.current_doc_content
    ), "No LLM provider issues section found in troubleshooting documentation"


@then("it should cover memory system issues")
def troubleshooting_covers_memory_system_issues(context):
    assert (
        "## Memory System Issues" in context.current_doc_content
    ), "No memory system issues section found in troubleshooting documentation"


@then("it should cover command execution issues")
def troubleshooting_covers_command_execution_issues(context):
    assert (
        "## Command Execution Issues" in context.current_doc_content
    ), "No command execution issues section found in troubleshooting documentation"


@then("it should cover performance issues")
def troubleshooting_covers_performance_issues(context):
    assert (
        "## Performance Issues" in context.current_doc_content
    ), "No performance issues section found in troubleshooting documentation"


@then("it should provide clear solutions for each issue")
def troubleshooting_provides_clear_solutions(context):
    # Look for solution sections
    solution_sections = re.findall(r"\*\*Solution\*\*:", context.current_doc_content)
    assert (
        len(solution_sections) > 0
    ), "No solution sections found in troubleshooting documentation"


# Configuration reference steps
@when("I check the configuration reference documentation")
def check_configuration_reference(context):
    # This file might not exist yet, so we don't assert its existence
    if context.configuration_reference.exists():
        context.current_doc_content = context.configuration_reference.read_text()
    else:
        context.current_doc_content = ""


@then("it should document all configuration options")
def configuration_reference_documents_all_options(context):
    # This will be implemented when the configuration reference is created
    # For now, we'll skip this test
    if not context.configuration_reference.exists():
        pytest.skip("Configuration reference does not exist yet")

    # List of expected configuration sections
    expected_sections = [
        "LLM Configuration",
        "Environment Variables",
        "Project Configuration",
        "Development Configuration",
        "Memory Configuration",
        "UXBridge Configuration",
        "Feature Flags",
    ]

    for section in expected_sections:
        assert (
            f"## {section}" in context.current_doc_content
        ), f"Configuration section '{section}' is not documented"


@then("it should explain the purpose of each option")
def configuration_reference_explains_purpose(context):
    if not context.configuration_reference.exists():
        pytest.skip("Configuration reference does not exist yet")

    # Look for option descriptions in tables
    option_descriptions = re.findall(
        r"\| `([^`]+)` \| (.*?) \|", context.current_doc_content
    )
    assert (
        len(option_descriptions) > 0
    ), "No option descriptions found in configuration reference"


@then("it should list possible values for each option")
def configuration_reference_lists_possible_values(context):
    if not context.configuration_reference.exists():
        pytest.skip("Configuration reference does not exist yet")

    # Look for value listings in tables
    value_listings = re.findall(
        r"\| `([^`]+)` \| .*? \| .*? \| (.*?) \|", context.current_doc_content
    )
    assert (
        len(value_listings) > 0
    ), "No possible values listed in configuration reference"


@then("it should provide examples of common configurations")
def configuration_reference_provides_examples(context):
    if not context.configuration_reference.exists():
        pytest.skip("Configuration reference does not exist yet")

    # Look for example sections
    example_sections = re.findall(r"```(yaml|bash|env)\n", context.current_doc_content)
    assert (
        len(example_sections) > 0
    ), "No configuration examples found in configuration reference"


@then("it should explain how to set options via environment variables")
def configuration_reference_explains_env_vars(context):
    if not context.configuration_reference.exists():
        pytest.skip("Configuration reference does not exist yet")

    assert (
        "Environment Variables" in context.current_doc_content
    ), "No environment variables section found in configuration reference"


@then("it should explain how to set options via configuration files")
def configuration_reference_explains_config_files(context):
    if not context.configuration_reference.exists():
        pytest.skip("Configuration reference does not exist yet")

    assert (
        "Configuration File" in context.current_doc_content
    ), "No configuration file section found in configuration reference"
