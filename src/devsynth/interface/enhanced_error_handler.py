"""Enhanced error handler with actionable suggestions and documentation links.

This module extends the basic error handler with more specific error patterns
and suggestions, as well as improved formatting for error messages.
"""

import sys
from collections.abc import Sequence
from io import StringIO
from typing import TYPE_CHECKING, Any, assert_type, cast

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from devsynth.interface.error_handler import EnhancedErrorHandler, ErrorSuggestion
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ActionableErrorSuggestion(ErrorSuggestion):
    """Enhanced error suggestion with actionable steps.

    This class extends the basic ErrorSuggestion with more detailed
    actionable steps and examples.
    """

    def __init__(
        self,
        suggestion: str,
        documentation_link: str | None = None,
        command_example: str | None = None,
        actionable_steps: Sequence[str] | None = None,
        code_example: str | None = None,
        related_errors: Sequence[str] | None = None,
    ):
        """Initialize the actionable error suggestion.

        Args:
            suggestion: The suggestion text
            documentation_link: Optional link to documentation
            command_example: Optional example command
            actionable_steps: Optional list of actionable steps
            code_example: Optional code example
            related_errors: Optional list of related errors
        """
        super().__init__(suggestion, documentation_link, command_example)
        self.actionable_steps: list[str] = list(actionable_steps or [])
        self.code_example = code_example
        self.related_errors: list[str] = list(related_errors or [])

    def __str__(self) -> str:
        """Return a string representation of the suggestion."""
        parts = [self.suggestion]

        if self.actionable_steps:
            parts.append("\nActionable steps:")
            for i, step in enumerate(self.actionable_steps, 1):
                parts.append(f"{i}. {step}")

        if self.documentation_link:
            parts.append(f"\nDocumentation: {self.documentation_link}")

        if self.command_example:
            parts.append(f"\nExample command: {self.command_example}")

        if self.code_example:
            parts.append(f"\nExample code:\n{self.code_example}")

        if self.related_errors:
            parts.append("\nRelated errors:")
            for error in self.related_errors:
                parts.append(f"- {error}")

        return "\n".join(parts)


class ImprovedErrorHandler(EnhancedErrorHandler):
    """Improved error handler with more specific error patterns and suggestions."""

    # Additional error patterns and their suggestions
    ADDITIONAL_ERROR_PATTERNS: list[tuple[str, ActionableErrorSuggestion]] = [
        # Memory integration errors
        (
            r"(?i)cross-store\s+(?:memory|synchronization|integration)",
            ActionableErrorSuggestion(
                "There may be issues with cross-store memory synchronization.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/memory_integration.html",
                "devsynth doctor --check-memory-integration",
                actionable_steps=[
                    "Check that all memory stores are properly configured",
                    "Verify that the memory synchronization service is running",
                    "Check the memory integration logs for errors",
                    "Try restarting the memory synchronization service",
                ],
                code_example="""
# Example of proper memory store configuration
memory_manager = MemoryManager(
    adapters={
        "primary": PrimaryMemoryAdapter(),
        "secondary": SecondaryMemoryAdapter()
    },
    sync_enabled=True
)
                """,
                related_errors=[
                    "MemorySyncError",
                    "CrossStoreIntegrationError",
                    "MemoryAdapterNotFoundError",
                ],
            ),
        ),
        # WSDE peer review errors
        (
            r"(?i)wsde\s+(?:peer\s+review|workflow|collaboration)",
            ActionableErrorSuggestion(
                "There may be issues with the WSDE peer review workflow.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/wsde_peer_review.html",
                "devsynth doctor --check-wsde-workflow",
                actionable_steps=[
                    "Verify that the WSDE team is properly configured",
                    "Check that all required roles are assigned",
                    "Ensure that the peer review workflow is enabled",
                    "Check the WSDE logs for errors",
                ],
                code_example="""
# Example of proper WSDE team configuration
wsde_team = WSDETeam(
    name="MyTeam",
    members=[
        TeamMember(role="developer", name="Developer"),
        TeamMember(role="reviewer", name="Reviewer")
    ],
    workflow_enabled=True
)
                """,
                related_errors=[
                    "WSPEPeerReviewError",
                    "WorkflowConfigurationError",
                    "MissingTeamMemberError",
                ],
            ),
        ),
        # Test failures
        (
            r"(?i)test\s+(?:failure|error|issue)",
            ActionableErrorSuggestion(
                "There may be issues with the tests.",
                "https://devsynth.readthedocs.io/en/latest/developer_guides/testing.html",
                "devsynth run-tests --report",
                actionable_steps=[
                    "Run the tests with the --verbose flag to get more information",
                    "Check the test logs for specific error messages",
                    "Verify that the test environment is properly configured",
                    "Try running the failing tests individually",
                ],
                code_example="""
# Example of running specific tests
python -m pytest tests/unit/specific_test.py -v

# Example of running tests with a specific marker
python -m pytest -m "fast" -v
                """,
                related_errors=[
                    "AssertionError",
                    "TestSetupError",
                    "TestEnvironmentError",
                ],
            ),
        ),
        # CLI UX errors
        (
            r"(?i)cli\s+(?:ux|interface|display|output)",
            ActionableErrorSuggestion(
                "There may be issues with the CLI user interface.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/cli_ux.html",
                "devsynth doctor --check-cli",
                actionable_steps=[
                    "Check that the terminal supports Rich formatting",
                    "Verify that the CLI UX bridge is properly configured",
                    "Try running with the --no-color flag if terminal formatting is causing issues",
                    "Check the CLI logs for errors",
                ],
                code_example="""
# Example of proper CLI UX bridge configuration
bridge = CLIUXBridge(colorblind_mode=False)
bridge.display_result("Message", message_type="info")
                """,
                related_errors=[
                    "CLIUXBridgeError",
                    "OutputFormattingError",
                    "TerminalCompatibilityError",
                ],
            ),
        ),
        # Web UI errors
        (
            r"(?i)web\s*ui\s+(?:wizard|state|integration)",
            ActionableErrorSuggestion(
                "There may be issues with the Web UI.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/webui.html",
                "devsynth doctor --check-webui",
                actionable_steps=[
                    "Check that Streamlit is properly installed and configured",
                    "Verify that the WebUI state is properly initialized",
                    "Check the WebUI logs for errors",
                    "Try restarting the WebUI server",
                ],
                code_example="""
# Example of proper WebUI state initialization
import streamlit as st

if 'wizard_state' not in st.session_state:
    st.session_state.wizard_state = WizardState()
                """,
                related_errors=[
                    "WebUIStateError",
                    "StreamlitError",
                    "WizardStateError",
                ],
            ),
        ),
        # Shell completion errors
        (
            r"(?i)shell\s+(?:completion|tab\s+completion)",
            ActionableErrorSuggestion(
                "There may be issues with shell completion.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/shell_completion.html",
                "source scripts/completions/devsynth-completion.bash",
                actionable_steps=[
                    "Verify that the shell completion script is installed",
                    "Check that the shell completion script is sourced in your shell configuration",
                    "Try reinstalling the shell completion script",
                    "Check that your shell supports completion scripts",
                ],
                code_example="""
# Add to ~/.bashrc or ~/.bash_profile for Bash
source /path/to/devsynth/scripts/completions/devsynth-completion.bash

# Add to ~/.zshrc for Zsh
fpath=(/path/to/devsynth/scripts/completions $fpath)
autoload -U compinit
compinit
                """,
                related_errors=[
                    "ShellCompletionError",
                    "CompletionScriptNotFoundError",
                    "ShellConfigurationError",
                ],
            ),
        ),
        # Command output formatting errors
        (
            r"(?i)(?:command|output)\s+(?:format|formatting)",
            ActionableErrorSuggestion(
                "There may be issues with command output formatting.",
                "https://devsynth.readthedocs.io/en/latest/user_guides/command_output.html",
                "devsynth doctor --check-output-formatting",
                actionable_steps=[
                    "Check that the output formatter is properly configured",
                    "Verify that the terminal supports the requested output format",
                    "Try using a different output format (--format=text)",
                    "Check the output formatter logs for errors",
                ],
                code_example="""
# Example of proper output formatter configuration
formatter = OutputFormatter(console)
formatter.format_command_output(data, format_name="rich")
                """,
                related_errors=[
                    "OutputFormattingError",
                    "UnsupportedFormatError",
                    "TerminalCompatibilityError",
                ],
            ),
        ),
    ]

    def __init__(self, console: Console | None = None):
        """Initialize the improved error handler.

        Args:
            console: Optional Rich console for output
        """
        super().__init__(console)

        # Combine the base error patterns with the additional ones
        base_patterns = cast(
            list[tuple[str, ErrorSuggestion | ActionableErrorSuggestion]],
            list(EnhancedErrorHandler.ERROR_PATTERNS),
        )
        self.ERROR_PATTERNS = [
            *base_patterns,
            *self.ADDITIONAL_ERROR_PATTERNS,
        ]

        logger.debug("Initialized ImprovedErrorHandler with additional error patterns")

    def _find_suggestions(
        self, error_message: str
    ) -> list[ErrorSuggestion | ActionableErrorSuggestion]:
        """Find suggestions for an error message.

        This method overrides the base method to provide more specific suggestions
        based on the error message.

        Args:
            error_message: The error message to find suggestions for

        Returns:
            A list of suggestions
        """
        suggestions: list[
            ErrorSuggestion | ActionableErrorSuggestion
        ] = super()._find_suggestions(error_message)

        # Add context-specific suggestions based on the current state of the system
        try:
            # Check if this is a test-related error
            if "pytest" in sys.modules or "unittest" in sys.modules:
                suggestions.append(
                    ActionableErrorSuggestion(
                        "This error occurred during test execution.",
                        "https://devsynth.readthedocs.io/en/latest/developer_guides/testing.html",
                        "devsynth run-tests --verbose",
                        actionable_steps=[
                            "Check the test logs for more information",
                            "Try running the test with increased verbosity",
                            "Verify that the test environment is properly configured",
                        ],
                    )
                )

            # Check if this is a CLI-related error
            if "devsynth.interface.cli" in sys.modules:
                suggestions.append(
                    ActionableErrorSuggestion(
                        "This error occurred in the CLI interface.",
                        "https://devsynth.readthedocs.io/en/latest/user_guides/cli_reference.html",
                        "devsynth --help",
                        actionable_steps=[
                            "Check the command syntax",
                            "Verify that all required parameters are provided",
                            "Try running with the --verbose flag for more information",
                        ],
                    )
                )

            # Check if this is a WebUI-related error
            if "streamlit" in sys.modules or "devsynth.interface.webui" in sys.modules:
                suggestions.append(
                    ActionableErrorSuggestion(
                        "This error occurred in the Web UI.",
                        "https://devsynth.readthedocs.io/en/latest/user_guides/webui.html",
                        "devsynth webui --debug",
                        actionable_steps=[
                            "Check the WebUI logs for more information",
                            "Try restarting the WebUI server",
                            "Verify that Streamlit is properly configured",
                        ],
                    )
                )
        except Exception as e:
            # Don't let errors in suggestion generation prevent the main error from being displayed
            logger.warning(f"Error while generating context-specific suggestions: {e}")

        return suggestions

    def _format_rich_error(
        self,
        error_message: str,
        error_type: str,
        error_traceback: str,
        suggestions: list[ErrorSuggestion | ActionableErrorSuggestion],
    ) -> Panel:
        """Format an error with Rich formatting.

        This method overrides the base method to provide more detailed error formatting.

        Args:
            error_message: The error message
            error_type: The error type
            error_traceback: The error traceback
            suggestions: The suggestions for the error

        Returns:
            A Rich panel with the formatted error
        """
        # Create a table for the error details
        error_table = Table(show_header=False, box=None)
        error_table.add_column("Key", style="bold red")
        error_table.add_column("Value")

        # Add error type and message
        error_table.add_row("Error Type:", error_type)
        error_table.add_row("Message:", error_message)

        # Add timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_table.add_row("Timestamp:", timestamp)

        # Add traceback if available
        if error_traceback:
            syntax = Syntax(
                error_traceback,
                "python",
                theme="ansi_dark",
                line_numbers=True,
                word_wrap=True,
            )
            error_table.add_row("Traceback:", "")

        # Create a table for the suggestions
        if suggestions:
            suggestion_table = Table(title="Suggestions", show_header=False, box=None)
            suggestion_table.add_column("Suggestion", style="bold green")

            for suggestion in suggestions:
                if isinstance(suggestion, ActionableErrorSuggestion):
                    # Format actionable suggestion
                    suggestion_text = Text()
                    suggestion_text.append(
                        f"{suggestion.suggestion}\n\n", style="bold green"
                    )

                    if suggestion.actionable_steps:
                        suggestion_text.append("Actionable steps:\n", style="bold")
                        for i, step in enumerate(suggestion.actionable_steps, 1):
                            suggestion_text.append(f"{i}. {step}\n", style="green")
                        suggestion_text.append("\n")

                    if suggestion.documentation_link:
                        suggestion_text.append(f"Documentation: ", style="bold")
                        suggestion_text.append(f"{suggestion.documentation_link}\n\n")

                    if suggestion.command_example:
                        suggestion_text.append(f"Example command: ", style="bold")
                        suggestion_text.append(f"{suggestion.command_example}\n\n")

                    if suggestion.code_example:
                        suggestion_text.append(f"Example code:\n", style="bold")
                        suggestion_text.append(f"{suggestion.code_example}\n\n")

                    if suggestion.related_errors:
                        suggestion_text.append(f"Related errors:\n", style="bold")
                        for error in suggestion.related_errors:
                            suggestion_text.append(f"- {error}\n")

                    suggestion_table.add_row(suggestion_text)
                else:
                    # Format basic suggestion
                    suggestion_table.add_row(str(suggestion))

        def render_to_string(renderable: object) -> str:
            buffer = StringIO()
            capture_console = Console(file=buffer)
            capture_console.print(renderable)
            return buffer.getvalue()

        # Combine the tables into a panel
        content = Text()
        content.append(
            "An error occurred while executing the command.\n\n", style="bold red"
        )

        # Add the error table
        content.append(render_to_string(error_table))

        # Add the traceback if available
        if error_traceback:
            content.append("\nTraceback:\n", style="bold red")
            content.append(render_to_string(syntax))

        # Add the suggestion table if available
        if suggestions:
            content.append("\nSuggestions:\n", style="bold green")
            content.append(render_to_string(suggestion_table))

        # Create the panel
        return Panel(
            content,
            title=f"[bold red]Error: {error_type}[/bold red]",
            border_style="red",
            expand=False,
        )

    def format_error(
        self, error: Exception | dict[str, Any] | str
    ) -> str | Text | Panel:
        """Format an error with actionable suggestions and documentation links.

        This method overrides the base method to provide more detailed error formatting.

        Args:
            error: The error to format

        Returns:
            The formatted error message
        """
        # Use the base implementation for the basic formatting
        formatted_error = super().format_error(error)

        # Add additional context if available
        if isinstance(formatted_error, Panel):
            footer = Text()
            footer.append("\nFor more help, run: ", style="dim")
            footer.append("devsynth doctor", style="bold blue")
            footer.append(" or visit: ", style="dim")
            footer.append(
                "https://devsynth.readthedocs.io/en/latest/user_guides/troubleshooting.html",
                style="bold blue",
            )

            return Panel(
                formatted_error,
                subtitle=footer,
            )

        return formatted_error


# Create a singleton instance for easy access
improved_error_handler = ImprovedErrorHandler()


if TYPE_CHECKING:
    assert_type(
        improved_error_handler._find_suggestions("sample"),
        list[ErrorSuggestion | ActionableErrorSuggestion],
    )
