"""Streamlit WebUI implementation for DevSynth.

This module provides a graphical interface that mirrors the CLI workflows
through the :class:`~devsynth.interface.ux_bridge.UXBridge` abstraction.
The :class:`WebUI` exposes multiple pages available from a sidebar:

- **Project Onboarding** – initialize or onboard projects.
- **Requirements Gathering** – generate and inspect specifications.
- **Code Analysis** – analyze the project code base.
- **Synthesis Execution** – generate tests, code and run the pipeline.
- **Configuration Editing** – view or update settings.
- **EDRR Cycle** – execute a full Expand-Differentiate-Refine-Retrospect cycle.
- **Alignment** – check SDLC artifacts for traceability and consistency.
- **Alignment Metrics** – collect SDLC traceability metrics.
- **Inspect Config** – analyze and update project configuration.
- **Validate Manifest** – schema validation of project manifests.
- **Validate Metadata** – check Markdown front matter for consistency.
- **Test Metrics** – analyze commit history for test-first practices.
- **Generate Docs** – build API reference documentation.
- **Ingest Project** – run the ingestion pipeline.
- **API Spec** – generate API specifications.
- **Doctor** – quick diagnostics.
- **Diagnostics** – run detailed diagnostics.

All pages use collapsible sections and progress indicators to reflect the
UX guidance for clarity and responsiveness.
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, TypeVar
from unittest.mock import MagicMock

import streamlit as st

# ``webui`` is imported in several unit tests with a partially mocked
# :mod:`devsynth.application.cli` module. Direct imports would raise
# :class:`ImportError` when the expected attributes are missing. To make the
# module resilient to such scenarios we attempt the import defensively and
# fall back to ``None`` for any unavailable command.
try:  # pragma: no cover - optional dependency handling
    import importlib

    _cli_mod = importlib.import_module("devsynth.application.cli")  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _cli_mod = None


def _cli(name: str):
    """Return a CLI command by name if available."""

    return getattr(_cli_mod, name, None) if _cli_mod else None


try:  # pragma: no cover - optional dependency handling
    from devsynth.application.cli.commands.inspect_code_cmd import inspect_code_cmd
except Exception:  # pragma: no cover - optional dependency
    inspect_code_cmd = None
try:
    from devsynth.application.cli.commands.doctor_cmd import doctor_cmd
except Exception:  # pragma: no cover - optional dependency
    doctor_cmd = None
try:
    from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd
except Exception:  # pragma: no cover - optional dependency
    edrr_cycle_cmd = None
try:
    from devsynth.application.cli.commands.align_cmd import align_cmd
except Exception:  # pragma: no cover - optional dependency
    align_cmd = None
try:
    from devsynth.application.cli.commands.alignment_metrics_cmd import (
        alignment_metrics_cmd,
    )
except Exception:  # pragma: no cover - optional dependency
    alignment_metrics_cmd = None
try:
    from devsynth.application.cli.commands.inspect_config_cmd import inspect_config_cmd
except Exception:  # pragma: no cover - optional dependency
    inspect_config_cmd = None
try:
    from devsynth.application.cli.commands.validate_manifest_cmd import (
        validate_manifest_cmd,
    )
except Exception:  # pragma: no cover - optional dependency
    validate_manifest_cmd = None
try:
    from devsynth.application.cli.commands.validate_metadata_cmd import (
        validate_metadata_cmd,
    )
except Exception:  # pragma: no cover - optional dependency
    validate_metadata_cmd = None
try:
    from devsynth.application.cli.commands.test_metrics_cmd import test_metrics_cmd
except Exception:  # pragma: no cover - optional dependency
    test_metrics_cmd = None
try:
    from devsynth.application.cli.commands.generate_docs_cmd import generate_docs_cmd
except Exception:  # pragma: no cover - optional dependency
    generate_docs_cmd = None
try:
    from devsynth.application.cli.ingest_cmd import ingest_cmd
except Exception:  # pragma: no cover - optional dependency
    ingest_cmd = None
try:
    from devsynth.application.cli.apispec import apispec_cmd
except Exception:  # pragma: no cover - optional dependency
    apispec_cmd = None
try:
    from devsynth.application.cli.setup_wizard import SetupWizard
except Exception:  # pragma: no cover - optional dependency
    SetupWizard = None
from devsynth.config import load_project_config, save_config
from devsynth.domain.models.requirement import RequirementPriority, RequirementType
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge, sanitize_output


class WebUI(UXBridge):
    """Streamlit implementation of :class:`UXBridge` with navigation pages."""

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    # Type variable for the return type of the wrapped function
    T = TypeVar("T")

    def get_layout_config(self) -> dict:
        """Get layout configuration based on screen size.

        Returns:
            A dictionary with layout configuration parameters.
        """
        # Get screen width from session state or use default
        session_state = getattr(st, "session_state", None)
        screen_width = (
            getattr(session_state, "screen_width", 1200) if session_state else 1200
        )

        # Define layout configurations for different screen sizes
        if screen_width < 768:  # Mobile
            return {
                "columns": 1,
                "sidebar_width": "100%",
                "content_width": "100%",
                "font_size": "small",
                "padding": "0.5rem",
                "is_mobile": True,
            }
        elif screen_width < 992:  # Tablet
            return {
                "columns": 2,
                "sidebar_width": "30%",
                "content_width": "70%",
                "font_size": "medium",
                "padding": "1rem",
                "is_mobile": False,
            }
        else:  # Desktop
            return {
                "columns": 3,
                "sidebar_width": "20%",
                "content_width": "80%",
                "font_size": "medium",
                "padding": "1.5rem",
                "is_mobile": False,
            }

    def _handle_command_errors(
        self,
        func: Callable[..., T],
        error_message: str = "An error occurred",
        *args: Any,
        **kwargs: Any,
    ) -> Optional[T]:
        """Execute a command with error handling.

        Args:
            func: The function to execute
            error_message: The message to display if an error occurs
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call, or None if an error occurred
        """
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            self.display_result(
                f"ERROR: File not found: {e.filename}",
                highlight=False,
                message_type="error",
            )
            self.display_result(
                f"Make sure the file exists and the path is correct.", highlight=False
            )
            return None
        except PermissionError as e:
            self.display_result(
                f"ERROR: Permission denied: {e.filename}",
                highlight=False,
                message_type="error",
            )
            self.display_result(
                f"Make sure you have the necessary permissions to access this file.",
                highlight=False,
                message_type="info",
            )
            return None
        except ValueError as e:
            self.display_result(
                f"ERROR: Invalid value: {str(e)}", highlight=False, message_type="error"
            )
            self.display_result(
                f"Please check your input and try again.",
                highlight=False,
                message_type="info",
            )
            return None
        except Exception as e:
            self.display_result(
                f"ERROR: {error_message}: {str(e)}",
                highlight=False,
                message_type="error",
            )
            # Get the traceback for debugging
            tb = traceback.format_exc()
            # Display a more user-friendly message
            self.display_result(
                "An unexpected error occurred. Here are some suggestions:",
                highlight=False,
                message_type="info",
            )
            self.display_result(
                "1. Check your input values and try again",
                highlight=False,
                message_type="info",
            )
            self.display_result(
                "2. Make sure all required files exist",
                highlight=False,
                message_type="info",
            )
            self.display_result(
                "3. Check the logs for more details",
                highlight=False,
                message_type="info",
            )
            # Add a collapsible section with the full traceback for debugging
            with st.expander("Technical Details (for debugging)"):
                st.code(tb, language="python")
            return None

    # ------------------------------------------------------------------
    # UXBridge API
    # ------------------------------------------------------------------
    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        if choices:
            index = 0
            if default in choices:
                index = list(choices).index(default)
            return st.selectbox(message, list(choices), index=index, key=message)
        return st.text_input(message, value=default or "", key=message)

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        return st.checkbox(message, value=default, key=message)

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        """Display a message to the user with appropriate styling.

        Args:
            message: The message to display
            highlight: Whether to highlight the message
        """
        message = sanitize_output(message)

        # Process Rich markup in the message if present
        if "[" in message and "]" in message:
            # Convert Rich markup to Markdown
            # [bold] -> **
            # [italic] -> *
            # [red] -> <span style="color:red">
            message = (
                message.replace("[bold]", "**")
                .replace("[/bold]", "**")
                .replace("[italic]", "*")
                .replace("[/italic]", "*")
                .replace("[green]", '<span style="color:green">')
                .replace("[/green]", "</span>")
                .replace("[red]", '<span style="color:red">')
                .replace("[/red]", "</span>")
                .replace("[blue]", '<span style="color:blue">')
                .replace("[/blue]", "</span>")
                .replace("[yellow]", '<span style="color:orange">')
                .replace("[/yellow]", "</span>")
                .replace("[cyan]", '<span style="color:cyan">')
                .replace("[/cyan]", "</span>")
            )
            markdown_fn = getattr(st, "markdown", st.write)
            markdown_fn(message, unsafe_allow_html=True)
            return

        # Apply appropriate styling based on message content and highlight flag
        if highlight:
            getattr(st, "info", st.write)(message)
        elif message.startswith("ERROR") or message.startswith("FAILED"):
            # Display error message
            st.error(message)

            # Add suggestions and documentation links for common errors
            error_type = self._get_error_type(message)
            if error_type:
                # Add suggestions
                suggestions = self._get_error_suggestions(error_type)
                if suggestions:
                    st.markdown("**Suggestions:**")
                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")

                # Add documentation links
                doc_links = self._get_documentation_links(error_type)
                if doc_links:
                    st.markdown("**Documentation:**")
                    for title, url in doc_links.items():
                        st.markdown(f"- [{title}]({url})")
        elif message.startswith("WARNING"):
            st.warning(message)
        elif message.startswith("SUCCESS") or "successfully" in message.lower():
            st.success(message)
        elif message.startswith("#"):
            # Handle markdown-style headings
            level = len(message.split(" ")[0])
            if level == 1:
                st.header(message[2:])
            elif level == 2:
                st.subheader(message[3:])
            else:
                st.markdown(f"**{message[level+1:]}**")
        else:
            st.write(message)

    def _get_error_type(self, message: str) -> str:
        """Extract the error type from an error message.

        Args:
            message: The error message

        Returns:
            The error type, or an empty string if no type could be determined
        """
        if "File not found" in message:
            return "file_not_found"
        elif "Permission denied" in message:
            return "permission_denied"
        elif "Invalid parameter" in message:
            return "invalid_parameter"
        elif "Invalid format" in message:
            return "invalid_format"
        elif "Configuration error" in message:
            return "config_error"
        elif "Connection error" in message:
            return "connection_error"
        elif "API error" in message:
            return "api_error"
        elif "Validation error" in message:
            return "validation_error"
        elif "Syntax error" in message:
            return "syntax_error"
        elif "Import error" in message:
            return "import_error"
        else:
            return ""

    def _get_error_suggestions(self, error_type: str) -> list[str]:
        """Get suggestions for fixing an error.

        Args:
            error_type: The type of error

        Returns:
            A list of suggestions
        """
        suggestions = {
            "file_not_found": [
                "Check that the file path is correct",
                "Verify that the file exists in the specified location",
                "If using a relative path, make sure you're in the correct directory",
            ],
            "permission_denied": [
                "Check that you have the necessary permissions to access the file",
                "Try running the command with elevated privileges",
                "Verify that the file is not locked by another process",
            ],
            "invalid_parameter": [
                "Check the command syntax and parameters",
                "Refer to the documentation for the correct parameter format",
                "Use the --help flag to see available options",
            ],
            "invalid_format": [
                "Check that the file format is supported",
                "Verify that the file content matches the expected format",
                "Try using a different format option if available",
            ],
            "config_error": [
                "Check your configuration file for errors",
                "Verify that all required configuration options are set",
                "Try resetting to default configuration with 'devsynth config --reset'",
            ],
            "connection_error": [
                "Check your internet connection",
                "Verify that the service you're trying to connect to is available",
                "Check if a firewall is blocking the connection",
            ],
            "api_error": [
                "Verify that your API key is valid",
                "Check that you have sufficient quota for the API",
                "Verify that the API endpoint is correct",
            ],
            "validation_error": [
                "Check that your input meets all validation requirements",
                "Verify that all required fields are provided",
                "Check for formatting errors in your input",
            ],
            "syntax_error": [
                "Check for syntax errors in your code or input",
                "Verify that all brackets, quotes, and parentheses are properly closed",
                "Check for typos or missing characters",
            ],
            "import_error": [
                "Verify that the required package is installed",
                "Check that the package name is spelled correctly",
                "Try reinstalling the package",
            ],
        }

        return suggestions.get(error_type, [])

    def _get_documentation_links(self, error_type: str) -> dict[str, str]:
        """Get documentation links for an error.

        Args:
            error_type: The type of error

        Returns:
            A dictionary mapping link titles to URLs
        """
        base_url = "https://devsynth.readthedocs.io/en/latest"
        links = {
            "file_not_found": {
                "File Handling Guide": f"{base_url}/user_guides/file_handling.html",
                "Common File Errors": f"{base_url}/user_guides/troubleshooting.html#file-errors",
            },
            "permission_denied": {
                "Permission Issues": f"{base_url}/user_guides/troubleshooting.html#permission-issues",
                "Security Configuration": f"{base_url}/user_guides/security_config.html",
            },
            "invalid_parameter": {
                "Command Reference": f"{base_url}/user_guides/cli_reference.html",
                "Parameter Syntax": f"{base_url}/user_guides/command_syntax.html",
            },
            "invalid_format": {
                "Supported Formats": f"{base_url}/user_guides/file_formats.html",
                "Format Conversion": f"{base_url}/user_guides/format_conversion.html",
            },
            "config_error": {
                "Configuration Guide": f"{base_url}/user_guides/configuration.html",
                "Configuration Troubleshooting": f"{base_url}/user_guides/troubleshooting.html#configuration-issues",
            },
            "connection_error": {
                "Network Configuration": f"{base_url}/user_guides/network_config.html",
                "Connection Troubleshooting": f"{base_url}/user_guides/troubleshooting.html#connection-issues",
            },
            "api_error": {
                "API Integration Guide": f"{base_url}/user_guides/api_integration.html",
                "API Troubleshooting": f"{base_url}/user_guides/troubleshooting.html#api-issues",
            },
            "validation_error": {
                "Input Validation": f"{base_url}/user_guides/input_validation.html",
                "Validation Rules": f"{base_url}/user_guides/validation_rules.html",
            },
            "syntax_error": {
                "Syntax Guide": f"{base_url}/user_guides/syntax_guide.html",
                "Common Syntax Errors": f"{base_url}/user_guides/troubleshooting.html#syntax-issues",
            },
            "import_error": {
                "Package Management": f"{base_url}/user_guides/package_management.html",
                "Import Troubleshooting": f"{base_url}/user_guides/troubleshooting.html#import-issues",
            },
        }

        return links.get(error_type, {})

    class _UIProgress(ProgressIndicator):
        def __init__(self, description: str, total: int) -> None:
            self._description = description
            self._total = total
            self._current = 0
            self._subtasks = {}
            empty_fn = getattr(st, "empty", lambda: MagicMock())
            progress_fn = getattr(st, "progress", lambda *_, **__: MagicMock())
            self._status_container = empty_fn()
            self._bar_container = progress_fn(0.0)
            self._time_container = empty_fn()
            self._subtask_containers = {}
            self._start_time = time.time()
            self._update_times = []
            self._update_display()

        def _update_display(self) -> None:
            """Update the progress display with current status."""
            progress_pct = min(1.0, self._current / self._total)
            current_time = time.time()

            # Record update time for ETA calculation
            self._update_times.append((current_time, self._current))

            # Calculate estimated time remaining
            eta_text = ""
            if self._current > 0 and progress_pct < 1.0:
                # Use the last 5 updates to calculate rate
                recent_updates = (
                    self._update_times[-5:]
                    if len(self._update_times) > 5
                    else self._update_times
                )
                if len(recent_updates) > 1:
                    # Calculate progress rate (units per second)
                    first_time, first_progress = recent_updates[0]
                    last_time, last_progress = recent_updates[-1]
                    time_diff = last_time - first_time
                    progress_diff = last_progress - first_progress

                    if time_diff > 0 and progress_diff > 0:
                        rate = progress_diff / time_diff
                        remaining_progress = self._total - self._current
                        eta_seconds = remaining_progress / rate

                        # Format ETA
                        if eta_seconds < 60:
                            eta_text = f"ETA: {int(eta_seconds)} seconds"
                        elif eta_seconds < 3600:
                            eta_text = f"ETA: {int(eta_seconds / 60)} minutes"
                        else:
                            eta_text = f"ETA: {int(eta_seconds / 3600)} hours, {int((eta_seconds % 3600) / 60)} minutes"

            # Update status text with description and percentage
            status_text = f"**{self._description}** - {int(progress_pct * 100)}%"
            self._status_container.markdown(status_text)

            # Update ETA text
            if eta_text:
                self._time_container.info(eta_text)
            else:
                self._time_container.empty()

            # Update progress bar
            self._bar_container.progress(progress_pct)

        def update(
            self, *, advance: float = 1, description: Optional[str] = None
        ) -> None:
            """Update the progress indicator."""
            self._current += advance
            if description:
                self._description = sanitize_output(description)
            self._update_display()

        def complete(self) -> None:
            """Mark the progress indicator as complete."""
            self._current = self._total
            self._update_display()

            # Mark all subtasks as complete
            for subtask_id in self._subtasks:
                self.complete_subtask(subtask_id)

            # Add success message
            getattr(st, "success", st.write)(f"Completed: {self._description}")

        def add_subtask(self, description: str, total: int = 100) -> str:
            """Add a subtask to the progress indicator.

            Args:
                description: Description of the subtask
                total: Total steps for the subtask

            Returns:
                task_id: ID of the created subtask
            """
            # Create a unique ID for the subtask
            task_id = f"subtask_{len(self._subtasks)}"

            # Store subtask information
            self._subtasks[task_id] = {
                "description": sanitize_output(description),
                "total": total,
                "current": 0,
            }

            # Create container and store progress bar
            with st.container() as container:
                progress_bar = container.progress(0.0)
            self._subtask_containers[task_id] = {
                "container": container,
                "bar": progress_bar,
            }

            # Update subtask display
            self._update_subtask_display(task_id)

            return task_id

        def _update_subtask_display(self, task_id: str) -> None:
            """Update the display for a specific subtask."""
            if task_id not in self._subtasks or task_id not in self._subtask_containers:
                return

            subtask = self._subtasks[task_id]
            containers = self._subtask_containers[task_id]

            progress_pct = min(1.0, subtask["current"] / subtask["total"])

            # Update status text with indentation, description and percentage
            status_text = f"&nbsp;&nbsp;&nbsp;&nbsp;**{subtask['description']}** - {int(progress_pct * 100)}%"
            containers["container"].markdown(status_text)

            # Update progress bar
            containers["bar"].progress(progress_pct)

        def update_subtask(
            self, task_id: str, advance: float = 1, description: Optional[str] = None
        ) -> None:
            """Update a subtask's progress.

            Args:
                task_id: ID of the subtask to update
                advance: Amount to advance the progress
                description: New description for the subtask
            """
            if task_id not in self._subtasks:
                return

            # Update subtask information
            self._subtasks[task_id]["current"] += advance
            if description:
                self._subtasks[task_id]["description"] = sanitize_output(description)

            # Update subtask display
            self._update_subtask_display(task_id)

        def complete_subtask(self, task_id: str) -> None:
            """Mark a subtask as complete.

            Args:
                task_id: ID of the subtask to complete
            """
            if task_id not in self._subtasks:
                return

            # Set current progress to total
            self._subtasks[task_id]["current"] = self._subtasks[task_id]["total"]

            # Update subtask display
            self._update_subtask_display(task_id)
            subtask = self._subtasks[task_id]
            containers = self._subtask_containers.get(task_id)
            if containers:
                containers["container"].success(f"Completed: {subtask['description']}")

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator with the given description and total steps."""
        return self._UIProgress(sanitize_output(description), total)

    # ------------------------------------------------------------------
    # Page rendering helpers
    # ------------------------------------------------------------------
    def onboarding_page(self) -> None:
        """Render the onboarding page."""
        st.header("Project Onboarding")
        with st.expander("Initialize Project", expanded=True):
            with st.form("onboard"):
                path = st.text_input("Project Path", ".")
                project_root = st.text_input("Project Root", ".")
                language = st.text_input("Primary Language", "python")
                goals = st.text_input("Project Goals", "")
                submitted = st.form_submit_button("Initialize")
                if submitted:
                    with st.spinner("Initializing project..."):
                        cmd = _cli("init_cmd")
                        if cmd:
                            cmd(
                                path=path,
                                project_root=project_root,
                                language=language,
                                goals=goals or None,
                                bridge=self,
                            )
            if st.button("Guided Setup", key="guided_setup"):
                with st.spinner("Starting guided setup..."):
                    SetupWizard(self).run()

    def requirements_page(self) -> None:
        """Render the requirements gathering page."""
        st.header("Requirements Gathering")
        with st.expander("Specification Generation", expanded=True):
            with st.form("requirements"):
                req_file = st.text_input("Requirements File", "requirements.md")
                # Add validation for the requirements file
                if not req_file:
                    st.error("Please enter a requirements file path")

                submitted = st.form_submit_button("Generate Specs")
                if submitted and req_file:
                    # Validate that the requirements file exists
                    if not Path(req_file).exists():
                        st.error(f"Requirements file '{req_file}' not found")
                        st.info("Make sure the file exists and the path is correct")
                    else:
                        with st.spinner("Generating specifications..."):
                            cmd = _cli("spec_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to generate specifications",
                                    requirements_file=req_file,
                                    bridge=self,
                                )
        if hasattr(st, "divider"):
            st.divider()
        with st.expander("Inspect Requirements", expanded=True):
            with st.form("inspect"):
                input_file = st.text_input("Inspect File", "requirements.md")
                # Add validation for the input file
                if not input_file:
                    st.error("Please enter a file path to inspect")

                submitted = st.form_submit_button("Inspect Requirements")
                if submitted and input_file:
                    # Validate that the input file exists
                    if not Path(input_file).exists():
                        st.error(f"File '{input_file}' not found")
                        st.info("Make sure the file exists and the path is correct")
                    else:
                        with st.spinner("Inspecting requirements..."):
                            cmd = _cli("inspect_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to inspect requirements",
                                    input_file=input_file,
                                    interactive=False,
                                    bridge=self,
                                )
        if hasattr(st, "divider"):
            st.divider()
        with st.expander("Specification Editor", expanded=True):
            spec_path = st.text_input("Specification File", "specs.md")
            # Add validation for the spec path
            if not spec_path:
                st.error("Please enter a specification file path")

            if st.button("Load Spec", key="load_spec") and spec_path:
                try:
                    with open(spec_path, "r", encoding="utf-8") as f:
                        st.session_state.spec_content = f.read()
                    st.success(f"Loaded specification from {spec_path}")
                except FileNotFoundError:
                    st.error(f"Specification file '{spec_path}' not found")
                    st.info("Creating a new specification file")
                    st.session_state.spec_content = ""
                except Exception as e:
                    st.error(f"Error loading specification: {str(e)}")
                    st.session_state.spec_content = ""

            content = st.text_area(
                "Specification Content",
                st.session_state.get("spec_content", ""),
                height=300,
            )

            col1, col2 = st.columns(2)
            if col1.button("Save Spec", key="save_spec") and spec_path:
                try:
                    with open(spec_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    st.success(f"Saved specification to {spec_path}")

                    with st.spinner("Regenerating specifications..."):
                        cmd = _cli("spec_cmd")
                        if cmd:
                            self._handle_command_errors(
                                cmd,
                                "Failed to regenerate specifications",
                                requirements_file=spec_path,
                                bridge=self,
                            )
                    st.session_state.spec_content = content
                    st.markdown(content)
                except Exception as e:
                    st.error(f"Error saving specification: {str(e)}")

            if col2.button("Save Only", key="save_only") and spec_path:
                try:
                    with open(spec_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    st.success(f"Saved specification to {spec_path}")
                    st.session_state.spec_content = content
                    st.markdown(content)
                except Exception as e:
                    st.error(f"Error saving specification: {str(e)}")
        if hasattr(st, "divider"):
            st.divider()
        self._requirements_wizard()
        if hasattr(st, "divider"):
            st.divider()
        self._gather_wizard()

    def _requirements_wizard(self) -> None:
        """Interactive requirements wizard using progress steps."""
        # ``st.session_state`` behaves like an object with attribute access.  The
        # tests stub it using a simple ``dict`` subclass where values are set as
        # attributes rather than mapping keys.  Using ``in`` on such an object
        # does not reflect attribute presence, so ``hasattr`` is required to
        # detect prior wizard state correctly.
        steps = ["Title", "Description", "Type", "Priority", "Constraints"]
        # ``streamlit.session_state`` may be patched in tests as a ``dict``
        # subclass where attributes are set directly rather than as mapping
        # keys.  Support both styles when retrieving the current wizard step
        # and data.
        step_val = getattr(st.session_state, "wizard_step", None)
        if not isinstance(step_val, int):
            if isinstance(st.session_state, dict):
                step_val = st.session_state.get("wizard_step", step_val)
            if step_val is None:
                try:  # fall back to mapping access if attribute missing
                    step_val = st.session_state["wizard_step"]
                except Exception:  # pragma: no cover - defensive
                    step_val = 0
        # ``wizard_step`` may be stored as a string when persisted between
        # sessions.  Convert any digit-like value to ``int`` rather than
        # resetting to zero which would break navigation.
        if isinstance(step_val, str) and step_val.isdigit():
            step_val = int(step_val)
        if not isinstance(step_val, int):
            step_val = 0
        st.session_state.wizard_step = max(0, min(len(steps) - 1, step_val))
        if hasattr(st.session_state, "__setitem__"):
            st.session_state["wizard_step"] = st.session_state.wizard_step

        defaults = {
            "title": "",
            "description": "",
            "type": RequirementType.FUNCTIONAL.value,
            "priority": RequirementPriority.MEDIUM.value,
            "constraints": "",
        }
        raw_data = getattr(st.session_state, "wizard_data", None)
        if raw_data is None and isinstance(st.session_state, dict):
            raw_data = st.session_state.get("wizard_data", {})
        data = raw_data.copy() if isinstance(raw_data, dict) else {}
        for key, val in defaults.items():
            data.setdefault(key, val)

        step = st.session_state.wizard_step
        st.write(f"Step {step + 1} of {len(steps)}: {steps[step]}")
        st.progress((step + 1) / len(steps))

        if step == len(steps) - 1 and st.button("Save Requirements"):
            try:
                result = {
                    "title": data["title"],
                    "description": data["description"],
                    "type": data["type"],
                    "priority": data["priority"],
                    "constraints": [
                        c.strip() for c in data["constraints"].split(",") if c.strip()
                    ],
                }
                with open("requirements_wizard.json", "w", encoding="utf-8") as f:
                    f.write(json.dumps(result, indent=2))
                self.display_result(
                    "[green]Requirements saved to requirements_wizard.json[/green]"
                )
                if hasattr(st.session_state, "__setitem__"):
                    st.session_state["wizard_step"] = st.session_state.wizard_step
                    st.session_state["wizard_data"] = st.session_state.wizard_data
                return result
            except Exception as exc:  # pragma: no cover - error path tested
                self.display_result(
                    f"[red]ERROR saving requirements: {exc}[/red]",
                    highlight=False,
                )
                return None

        if step == 0:
            data["title"] = st.text_input("Requirement Title", data["title"])
        elif step == 1:
            data["description"] = st.text_area(
                "Requirement Description", data["description"]
            )
        elif step == 2:
            options = [t.value for t in RequirementType]
            index = options.index(data["type"])
            data["type"] = st.selectbox("Requirement Type", options, index=index)
        elif step == 3:
            options = [p.value for p in RequirementPriority]
            index = options.index(data["priority"])
            data["priority"] = st.selectbox(
                "Requirement Priority", options, index=index
            )
        elif step == 4:
            data["constraints"] = st.text_area(
                "Constraints (comma separated)", data["constraints"]
            )

        col1, col2 = st.columns(2)
        if col1.button("Back", disabled=step == 0):
            st.session_state.wizard_step = max(0, step - 1)
        elif col2.button("Next", disabled=step >= len(steps) - 1):
            st.session_state.wizard_step = min(len(steps) - 1, step + 1)

        st.session_state.wizard_data = data
        if hasattr(st.session_state, "__setitem__"):
            st.session_state["wizard_step"] = st.session_state.wizard_step
            st.session_state["wizard_data"] = st.session_state.wizard_data
        return

    def _gather_wizard(self) -> None:
        """Run the requirements gathering workflow via :mod:`core.workflows`."""
        if st.button(
            "Start Requirements Plan Wizard",
            key="Start Requirements Plan Wizard",
        ) and not getattr(st.session_state, "gather_running", False):
            st.session_state.gather_running = True
            if hasattr(st.session_state, "__setitem__"):
                st.session_state["gather_running"] = True
            try:
                from devsynth.core.workflows import gather_requirements
            except Exception as exc:  # pragma: no cover - defensive
                self.display_result(
                    f"[red]ERROR importing gather_requirements: {exc}[/red]"
                )
                st.session_state.gather_running = False
                if hasattr(st.session_state, "__setitem__"):
                    st.session_state["gather_running"] = False
                return

            try:
                with st.spinner("Collecting requirements ..."):
                    gather_requirements(self)
            except Exception as exc:  # pragma: no cover - defensive
                self.display_result(
                    f"[red]ERROR running gather_requirements: {exc}[/red]"
                )
            finally:
                st.session_state.gather_running = False
                if hasattr(st.session_state, "__setitem__"):
                    st.session_state["gather_running"] = False

    def analysis_page(self) -> None:
        """Render the code analysis page."""
        st.header("Code Analysis")
        with st.expander("Inspect Code", expanded=True):
            with st.form("analysis"):
                path = st.text_input("Path", ".")
                # Add validation for the path
                if not path:
                    st.error("Please enter a path to inspect")

                submitted = st.form_submit_button("Inspect")
                if submitted and path:
                    # Validate that the path exists
                    if not Path(path).exists():
                        st.error(f"Path '{path}' not found")
                        st.info(
                            "Make sure the directory or file exists and the path is correct"
                        )
                    else:
                        with st.spinner("Inspecting code..."):
                            cmd = inspect_code_cmd
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to inspect code",
                                    path=path,
                                    bridge=self,
                                )

    def synthesis_page(self) -> None:
        """Render the synthesis execution page."""
        st.header("Synthesis Execution")
        with st.expander("Generate Tests", expanded=True):
            with st.form("tests"):
                spec_file = st.text_input("Spec File", "specs.md")
                # Add validation for the spec file
                if not spec_file:
                    st.error("Please enter a specification file path")

                submitted = st.form_submit_button("Generate Tests")
                if submitted and spec_file:
                    # Validate that the spec file exists
                    if not Path(spec_file).exists():
                        st.error(f"Specification file '{spec_file}' not found")
                        st.info("Make sure the file exists and the path is correct")
                    else:
                        with st.spinner("Generating tests..."):
                            cmd = _cli("test_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to generate tests",
                                    spec_file=spec_file,
                                    bridge=self,
                                )

        if hasattr(st, "divider"):
            st.divider()
        with st.expander("Execute Code Generation", expanded=True):
            if st.button("Generate Code"):
                with st.spinner("Generating code..."):
                    cmd = _cli("code_cmd")
                    if cmd:
                        self._handle_command_errors(
                            cmd,
                            "Failed to generate code",
                            bridge=self,
                        )

            if st.button("Run Pipeline"):
                with st.spinner("Running pipeline..."):
                    cmd = _cli("run_pipeline_cmd")
                    if cmd:
                        self._handle_command_errors(
                            cmd,
                            "Failed to run pipeline",
                            bridge=self,
                        )

    def config_page(self) -> None:
        """Render the configuration editing page."""
        st.header("Configuration Editing")

        try:
            cfg = load_project_config()
            offline_toggle = st.toggle(
                "Offline Mode",
                value=cfg.config.offline_mode,
                key="offline_mode_toggle",
            )

            if st.button("Save Offline Mode", key="offline_mode_save"):
                cfg.config.offline_mode = offline_toggle
                with st.spinner("Saving configuration..."):
                    try:
                        save_config(
                            cfg.config,
                            use_pyproject=cfg.use_pyproject,
                            path=cfg.config.project_root,
                        )
                        st.success("Offline mode setting saved successfully")
                    except Exception as e:
                        st.error(f"Error saving configuration: {str(e)}")
                        st.info(
                            "Make sure you have write permissions to the configuration file"
                        )

            with st.expander("Update Settings", expanded=True):
                with st.form("config"):
                    key = st.text_input("Key")
                    value = st.text_input("Value")

                    # Add validation for the key
                    if not key and st.form_submit_button():
                        st.error("Please enter a configuration key")

                    submitted = st.form_submit_button("Update")
                    if submitted and key:
                        with st.spinner("Updating configuration..."):
                            cmd = _cli("config_cmd")
                            if cmd:
                                self._handle_command_errors(
                                    cmd,
                                    "Failed to update configuration",
                                    key=key,
                                    value=value or None,
                                    bridge=self,
                                )

            if st.button("View All Config"):
                with st.spinner("Loading configuration..."):
                    cmd = _cli("config_cmd")
                    if cmd:
                        self._handle_command_errors(
                            cmd,
                            "Failed to load configuration",
                            bridge=self,
                        )

        except Exception as e:
            st.error(f"Error loading configuration: {str(e)}")
            st.info(
                "Make sure your project is properly initialized with a valid configuration file"
            )

            # Provide a button to initialize the project
            if st.button("Initialize Project"):
                with st.spinner("Initializing project..."):
                    cmd = _cli("init_cmd")
                    if cmd:
                        self._handle_command_errors(
                            cmd,
                            "Failed to initialize project",
                            bridge=self,
                        )

    def edrr_cycle_page(self) -> None:
        """Run an Expand-Differentiate-Refine-Retrospect cycle."""
        st.header("EDRR Cycle")
        with st.form("edrr_cycle"):
            manifest = self.ask_question("Manifest Path", default="manifest.yaml")
            auto = self.confirm_choice("Auto Progress", default=True)

            # Add validation for the manifest path
            if not manifest:
                st.error("Please enter a manifest path")

            submitted = st.form_submit_button("Run Cycle")

        if submitted and manifest:
            # Validate that the manifest file exists
            if not Path(manifest).exists():
                st.error(f"Manifest file '{manifest}' not found")
                st.info("Make sure the file exists and the path is correct")

                # Provide guidance on creating a manifest
                with st.expander("How to create a manifest file"):
                    st.markdown(
                        """
                    A manifest file is a YAML file that defines the structure of your project.
                    It includes information about requirements, specifications, and code organization.

                    Example manifest.yaml:
                    ```yaml
                    project:
                      name: my-project
                      description: A sample project
                    requirements:
                      path: requirements.md
                    specifications:
                      path: specs.md
                    ```
                    """
                    )
            else:
                with st.spinner("Running EDRR cycle..."):
                    import sys

                    module = sys.modules.get(
                        "devsynth.application.cli.commands.edrr_cycle_cmd"
                    )
                    if module is None:  # pragma: no cover - defensive fallback
                        import devsynth.application.cli.commands.edrr_cycle_cmd as module

                    original = module.bridge
                    module.bridge = self
                    try:
                        self._handle_command_errors(
                            module.edrr_cycle_cmd,
                            "Failed to run EDRR cycle",
                            manifest=manifest,
                            auto=auto,
                        )
                    finally:
                        module.bridge = original

    def alignment_page(self) -> None:
        """Check SDLC alignment between artifacts."""
        st.header("Alignment")
        with st.form("alignment"):
            path = self.ask_question("Project Path", default=".")
            verbose = self.confirm_choice("Verbose Output", default=False)
            submitted = st.form_submit_button("Check Alignment")
        if submitted:
            with st.spinner("Checking alignment..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.commands.align_cmd")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.align_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.align_cmd(path=path, verbose=verbose)
                finally:
                    module.bridge = original

    def alignment_metrics_page(self) -> None:
        """Collect and display alignment metrics."""
        st.header("Alignment Metrics")
        with st.form("alignment_metrics"):
            path = self.ask_question("Project Path", default=".")
            metrics_file = self.ask_question(
                "Metrics File", default=".devsynth/alignment_metrics.json"
            )
            output = st.text_input("Report File", "")
            submitted = st.form_submit_button("Collect Metrics")
        if submitted:
            with st.spinner("Collecting metrics..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.alignment_metrics_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.alignment_metrics_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.alignment_metrics_cmd(
                        path=path,
                        metrics_file=metrics_file,
                        output=output or None,
                    )
                finally:
                    module.bridge = original

    def inspect_config_page(self) -> None:
        """Analyze and optionally update the project configuration."""
        st.header("Inspect Config")
        with st.form("inspect_config"):
            path = self.ask_question("Project Path", default=".")
            update = self.confirm_choice("Update", default=False)
            prune = self.confirm_choice("Prune", default=False)
            submitted = st.form_submit_button("Inspect Config")
        if submitted:
            with st.spinner("Inspecting configuration..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.inspect_config_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.inspect_config_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.inspect_config_cmd(
                        path=path,
                        update=update,
                        prune=prune,
                    )
                finally:
                    module.bridge = original

    def validate_manifest_page(self) -> None:
        """Validate the project manifest against its schema."""
        st.header("Validate Manifest")
        with st.form("validate_manifest"):
            manifest_path = st.text_input("Manifest Path", "manifest.yaml")
            schema_path = st.text_input("Schema Path", "")
            submitted = st.form_submit_button("Validate Manifest")
        if submitted:
            with st.spinner("Validating manifest..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.validate_manifest_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.validate_manifest_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.validate_manifest_cmd(
                        manifest_path=manifest_path or None,
                        schema_path=schema_path or None,
                    )
                finally:
                    module.bridge = original

    def validate_metadata_page(self) -> None:
        """Validate Markdown front-matter metadata."""
        st.header("Validate Metadata")
        with st.form("validate_metadata"):
            directory = st.text_input("Docs Directory", "docs")
            file = st.text_input("Single File", "")
            verbose = self.confirm_choice("Verbose Output", default=False)
            submitted = st.form_submit_button("Validate Metadata")
        if submitted:
            with st.spinner("Validating metadata..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.validate_metadata_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.validate_metadata_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.validate_metadata_cmd(
                        directory=directory or None,
                        file=file or None,
                        verbose=verbose,
                    )
                finally:
                    module.bridge = original

    def test_metrics_page(self) -> None:
        """Analyze test-first development metrics."""
        st.header("Test Metrics")
        with st.form("test_metrics"):
            days = st.number_input("Days", min_value=1, step=1, value=30)
            output_file = st.text_input("Output File", "")
            submitted = st.form_submit_button("Analyze Metrics")
        if submitted:
            with st.spinner("Analyzing metrics..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.test_metrics_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.test_metrics_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.test_metrics_cmd(
                        days=int(days), output_file=output_file or None
                    )
                finally:
                    module.bridge = original

    def docs_generation_page(self) -> None:
        """Generate API reference documentation."""
        st.header("Generate Docs")
        with st.form("generate_docs"):
            path = st.text_input("Project Path", ".")
            output_dir = st.text_input("Output Directory", "")
            submitted = st.form_submit_button("Generate Docs")
        if submitted:
            with st.spinner("Generating documentation..."):
                import sys

                module = sys.modules.get(
                    "devsynth.application.cli.commands.generate_docs_cmd"
                )
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.generate_docs_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.generate_docs_cmd(
                        path=path or None,
                        output_dir=output_dir or None,
                    )
                finally:
                    module.bridge = original

    def ingestion_page(self) -> None:
        """Run the ingestion pipeline."""
        st.header("Ingest Project")
        with st.form("ingest"):
            manifest_path = st.text_input("Manifest Path", "manifest.yaml")
            dry_run = self.confirm_choice("Dry Run", default=False)
            verbose = self.confirm_choice("Verbose Output", default=False)
            validate_only = self.confirm_choice("Validate Only", default=False)
            submitted = st.form_submit_button("Ingest Project")
        if submitted:
            with st.spinner("Running ingestion..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.ingest_cmd")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.ingest_cmd as module

                original = module.bridge
                module.bridge = self
                try:
                    module.ingest_cmd(
                        manifest_path=manifest_path or None,
                        dry_run=dry_run,
                        verbose=verbose,
                        validate_only=validate_only,
                    )
                finally:
                    module.bridge = original

    def apispec_page(self) -> None:
        """Generate an API specification."""
        st.header("API Spec")
        with st.form("apispec"):
            api_type = st.selectbox("API Type", ("rest", "graphql", "grpc"))
            format_type = st.text_input("Format", "openapi")
            name = st.text_input("Name", "api")
            path = st.text_input("Path", ".")
            submitted = st.form_submit_button("Generate Spec")
        if submitted:
            with st.spinner("Generating API spec..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.apispec")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.apispec as module

                original = module.bridge
                module.bridge = self
                try:
                    module.apispec_cmd(
                        api_type=api_type,
                        format_type=format_type,
                        name=name,
                        path=path,
                    )
                finally:
                    module.bridge = original

    def refactor_page(self) -> None:
        """Suggest refactor workflows based on project state."""
        st.header("Refactor Suggestions")
        with st.form("refactor"):
            path = st.text_input("Project Path", ".")
            submitted = st.form_submit_button("Run Refactor")
        if submitted:
            with st.spinner("Running refactor analysis..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.cli_commands")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.cli_commands as module

                original = getattr(module, "bridge", None)
                module.bridge = self
                try:
                    module.refactor_cmd(path=path or None, bridge=self)
                finally:
                    module.bridge = original

    def webapp_page(self) -> None:
        """Generate a starter web application."""
        st.header("Web App Helper")
        with st.form("webapp"):
            framework = st.text_input("Framework", "flask")
            name = st.text_input("Name", "webapp")
            path = st.text_input("Path", ".")
            submitted = st.form_submit_button("Generate Web App")
        if submitted:
            with st.spinner("Generating web app..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.cli_commands")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.cli_commands as module

                original = getattr(module, "bridge", None)
                module.bridge = self
                try:
                    module.webapp_cmd(
                        framework=framework,
                        name=name,
                        path=path,
                        bridge=self,
                    )
                finally:
                    module.bridge = original

    def serve_page(self) -> None:
        """Run the DevSynth API server."""
        st.header("Serve API")
        with st.form("serve"):
            host = st.text_input("Host", "0.0.0.0")
            port = st.number_input("Port", value=8000)
            submitted = st.form_submit_button("Start Server")
        if submitted:
            with st.spinner("Starting server..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.cli_commands")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.cli_commands as module

                original = getattr(module, "bridge", None)
                module.bridge = self
                try:
                    module.serve_cmd(host=host, port=int(port), bridge=self)
                finally:
                    module.bridge = original

    def dbschema_page(self) -> None:
        """Generate a database schema."""
        st.header("Database Schema")
        with st.form("dbschema"):
            db_type = st.text_input("Database Type", "sqlite")
            name = st.text_input("Name", "database")
            path = st.text_input("Path", ".")
            submitted = st.form_submit_button("Generate Schema")
        if submitted:
            with st.spinner("Generating schema..."):
                import sys

                module = sys.modules.get("devsynth.application.cli.cli_commands")
                if module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.cli_commands as module

                original = getattr(module, "bridge", None)
                module.bridge = self
                try:
                    module.dbschema_cmd(
                        db_type=db_type,
                        name=name,
                        path=path,
                        bridge=self,
                    )
                finally:
                    module.bridge = original

    def doctor_page(self) -> None:
        """Render the doctor diagnostics page."""
        st.header("Doctor")
        with st.spinner("Validating configuration..."):
            import sys

            doc_module = sys.modules.get("devsynth.application.cli.commands.doctor_cmd")
            if doc_module is None:  # pragma: no cover - defensive fallback
                import devsynth.application.cli.commands.doctor_cmd as doc_module

            original = doc_module.bridge
            doc_module.bridge = self
            try:
                doc_module.doctor_cmd()
            finally:
                doc_module.bridge = original

    def diagnostics_page(self) -> None:
        """Run environment diagnostics via :func:`doctor_cmd`."""
        st.header("Diagnostics")
        with st.form("diagnostics"):
            config_dir = st.text_input("Config Directory", "config")
            submitted = st.form_submit_button("Run Diagnostics")
        if submitted:
            with st.spinner("Running diagnostics..."):
                import sys

                doc_module = sys.modules.get(
                    "devsynth.application.cli.commands.doctor_cmd"
                )
                if doc_module is None:  # pragma: no cover - defensive fallback
                    import devsynth.application.cli.commands.doctor_cmd as doc_module

                original = doc_module.bridge
                doc_module.bridge = self
                try:
                    doc_module.doctor_cmd(config_dir)
                finally:
                    doc_module.bridge = original

    # ------------------------------------------------------------------
    # Application entry point
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Run the Streamlit application."""
        try:
            st.set_page_config(page_title="DevSynth WebUI", layout="wide")
        except Exception as exc:  # noqa: BLE001
            try:
                self.display_result(f"ERROR: {exc}")
            except Exception:
                raise exc
            return

        # Add JavaScript to detect screen width and store in session state
        js_code = """
        <script>
        // Function to update screen width in session state
        function updateScreenWidth() {
            const width = window.innerWidth;
            const data = {
                width: width,
                height: window.innerHeight
            };

            // Use Streamlit's setComponentValue to update session state
            if (window.parent.streamlit) {
                window.parent.streamlit.setComponentValue(data);
            }
        }

        // Update on page load
        updateScreenWidth();

        // Update on window resize
        window.addEventListener('resize', updateScreenWidth);
        </script>
        """
        components = getattr(st, "components", None)
        html_fn = None
        if components and hasattr(components, "v1"):
            html_fn = getattr(components.v1, "html", None)
        if callable(html_fn):
            try:
                html_fn(js_code, height=0)
            except Exception as exc:  # noqa: BLE001
                try:
                    self.display_result(f"ERROR: {exc}")
                except Exception:
                    raise exc
                return

        # Get screen dimensions from component value
        if getattr(st, "session_state", None) is not None:
            if "screen_width" not in st.session_state:
                st.session_state.screen_width = 1200
                st.session_state.screen_height = 800

        # Apply layout configuration based on screen size
        layout_config = self.get_layout_config()

        # Apply custom CSS for consistent styling
        custom_css = f"""
        <style>
            .main .block-container {{
                padding: {layout_config["padding"]};
            }}
            .stSidebar .sidebar-content {{
                width: {layout_config["sidebar_width"]};
            }}
            .main {{
                font-size: {layout_config["font_size"]};
            }}
            /* DevSynth branding colors */
            .devsynth-primary {{
                color: #4A90E2;
            }}
            .devsynth-secondary {{
                color: #50E3C2;
            }}
            .devsynth-accent {{
                color: #F5A623;
            }}
            .devsynth-error {{
                color: #D0021B;
            }}
            .devsynth-success {{
                color: #7ED321;
            }}
            .devsynth-warning {{
                color: #F8E71C;
            }}
            /* Consistent form styling */
            .stForm {{
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
            }}
            /* Consistent button styling */
            .stButton>button {{
                background-color: #4A90E2;
                color: white;
                border-radius: 4px;
                border: none;
                padding: 0.5rem 1rem;
            }}
            .stButton>button:hover {{
                background-color: #3A80D2;
            }}
        </style>
        """
        markdown_fn = getattr(st, "markdown", lambda *a, **k: None)
        markdown_fn(custom_css, unsafe_allow_html=True)

        # Apply branding
        if getattr(st.sidebar, "title", None):
            st.sidebar.title("DevSynth")
        if getattr(st.sidebar, "markdown", None):
            st.sidebar.markdown(
                '<div class="devsynth-secondary" style="font-size: 0.8rem; margin-bottom: 2rem;">Intelligent Software Development</div>',
                unsafe_allow_html=True,
            )

        # Navigation with responsive layout
        nav_items = {
            "Onboarding": self.onboarding_page,
            "Requirements": self.requirements_page,
            "Analysis": self.analysis_page,
            "Synthesis": self.synthesis_page,
            "EDRR Cycle": self.edrr_cycle_page,
            "Alignment": self.alignment_page,
            "Alignment Metrics": self.alignment_metrics_page,
            "Inspect Config": self.inspect_config_page,
            "Validate Manifest": self.validate_manifest_page,
            "Validate Metadata": self.validate_metadata_page,
            "Test Metrics": self.test_metrics_page,
            "Generate Docs": self.docs_generation_page,
            "Ingest": self.ingestion_page,
            "API Spec": self.apispec_page,
            "Refactor": self.refactor_page,
            "Web App": self.webapp_page,
            "Serve": self.serve_page,
            "DB Schema": self.dbschema_page,
            "Config": self.config_page,
            "Doctor": self.doctor_page,
            "Diagnostics": self.diagnostics_page,
        }

        try:
            nav = st.sidebar.radio("Navigation", list(nav_items))
        except Exception as exc:  # noqa: BLE001
            try:
                self.display_result(f"ERROR: {exc}")
            except Exception:
                raise exc
            return

        page_func = nav_items.get(nav)
        if page_func is None:
            self.display_result("ERROR: Invalid navigation option")
            return

        try:
            page_func()
        except Exception as exc:  # noqa: BLE001
            try:
                self.display_result(f"ERROR: {exc}")
            except Exception:
                raise exc


def run() -> None:
    """Convenience entry point for ``streamlit run`` or the CLI."""
    WebUI().run()


# Backwards compatibility with older docs
run_webui = run


__all__ = ["WebUI", "run"]


if __name__ == "__main__":  # pragma: no cover - manual invocation
    run()
