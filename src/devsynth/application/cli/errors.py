"""Enhanced error handling for the DevSynth CLI.

This module provides enhanced error handling for the DevSynth CLI, with more
detailed error messages, visual distinction, and specific solutions.
"""

from typing import Union, Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.traceback import Traceback

from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import get_logger

# Common error patterns and their solutions
ERROR_SOLUTIONS = {
    "file not found": "Make sure the file exists and the path is correct. Use absolute paths if needed.",
    "permission denied": "Check file permissions. You may need to run with elevated privileges or change file permissions.",
    "invalid format": "Verify the file format matches what the command expects (e.g., YAML, JSON, Markdown).",
    "invalid parameter": "Check the command parameters. Use --help to see valid options.",
    "connection error": "Check your internet connection. If using a proxy, verify your proxy settings.",
    "timeout": "The operation timed out. Try again or increase the timeout setting in your configuration.",
    "api key": "Ensure your API key is correctly set in the environment or configuration file.",
    "out of memory": "The operation requires more memory. Try closing other applications or increasing available memory.",
    "configuration": "There may be an issue with your configuration. Run 'devsynth doctor' to diagnose configuration problems.",
    "import error": "A required module could not be imported. Make sure all dependencies are installed.",
    "syntax error": "There is a syntax error in your code or configuration file. Check for typos or missing characters.",
    "value error": "An invalid value was provided. Check the expected type and format of the value.",
    "type error": "An object of the wrong type was used. Check the expected type of the parameter.",
    "attribute error": "An attribute or method does not exist on the object. Check for typos or missing imports.",
    "key error": "A dictionary key was not found. Check that the key exists in the dictionary.",
    "index error": "An index is out of range. Check that the index is within the bounds of the list or array.",
    "name error": "A name is not defined. Check for typos or missing imports.",
    "assertion error": "An assertion failed. Check the condition that failed and why it might be false.",
    "runtime error": "An error occurred during execution. Check the error message for more details.",
    "io error": "An I/O error occurred. Check file permissions and disk space.",
    "os error": "An operating system error occurred. Check file permissions and system resources.",
}

# Documentation links for different error types
DOC_LINKS = {
    "file": "[link=https://devsynth.ai/docs/file-handling]File Handling Documentation[/link]",
    "parameter": "[link=https://devsynth.ai/docs/command-parameters]Command Parameters Documentation[/link]",
    "configuration": "[link=https://devsynth.ai/docs/configuration]Configuration Documentation[/link]",
    "api": "[link=https://devsynth.ai/docs/api-integration]API Integration Documentation[/link]",
    "network": "[link=https://devsynth.ai/docs/network-troubleshooting]Network Troubleshooting[/link]",
    "memory": "[link=https://devsynth.ai/docs/performance]Performance Optimization[/link]",
    "import": "[link=https://devsynth.ai/docs/dependencies]Dependency Management[/link]",
    "syntax": "[link=https://devsynth.ai/docs/syntax]Syntax Reference[/link]",
    "value": "[link=https://devsynth.ai/docs/validation]Input Validation[/link]",
    "type": "[link=https://devsynth.ai/docs/types]Type System[/link]",
    "attribute": "[link=https://devsynth.ai/docs/objects]Object Model[/link]",
    "key": "[link=https://devsynth.ai/docs/dictionaries]Dictionary Operations[/link]",
    "index": "[link=https://devsynth.ai/docs/lists]List Operations[/link]",
    "name": "[link=https://devsynth.ai/docs/namespaces]Namespaces and Scopes[/link]",
    "assertion": "[link=https://devsynth.ai/docs/assertions]Assertions and Contracts[/link]",
    "runtime": "[link=https://devsynth.ai/docs/runtime]Runtime Environment[/link]",
    "io": "[link=https://devsynth.ai/docs/io]I/O Operations[/link]",
    "os": "[link=https://devsynth.ai/docs/os]Operating System Integration[/link]",
}

# Recovery suggestions for different error types
RECOVERY_SUGGESTIONS = {
    "file not found": [
        "Check if the file exists in the current directory",
        "Use an absolute path to the file",
        "Create the file if it doesn't exist",
    ],
    "permission denied": [
        "Change the file permissions with chmod",
        "Run the command with elevated privileges",
        "Check if the file is locked by another process",
    ],
    "connection error": [
        "Check your internet connection",
        "Verify your proxy settings",
        "Try again later if the service might be down",
        "Check if the API endpoint URL is correct",
    ],
    "timeout": [
        "Increase the timeout setting in your configuration",
        "Try again when the network is less congested",
        "Break the operation into smaller chunks",
    ],
    "api key": [
        "Check if your API key is correctly set in the environment",
        "Verify that your API key is valid and not expired",
        "Generate a new API key if necessary",
    ],
    "out of memory": [
        "Close other applications to free up memory",
        "Increase the memory limit in your configuration",
        "Break the operation into smaller chunks",
    ],
    "configuration": [
        "Run 'devsynth doctor' to diagnose configuration problems",
        "Check your configuration file for errors",
        "Reset to default configuration with 'devsynth config --reset'",
    ],
}

def handle_error_enhanced(
    bridge: UXBridge, 
    error: Union[Exception, Dict[str, Any], str],
    console: Optional[Console] = None,
    show_traceback: bool = False,
) -> None:
    """Handle errors with enhanced visual feedback and specific solutions.

    Args:
        bridge: The UX bridge to use for displaying messages
        error: The error to handle, can be an Exception, a result dict, or a string
        console: Optional Rich console for enhanced output
        show_traceback: Whether to show the full traceback
    """
    logger = get_logger("cli_errors")
    
    # Create a console if not provided
    if console is None:
        console = Console()
    
    if isinstance(error, Exception):
        # Log the error for debugging with full traceback
        logger.error(f"Command error: {str(error)}", exc_info=True)

        # Get the error message and type
        error_msg = str(error)
        error_type = type(error).__name__

        # Create a panel with the error details
        error_panel = Panel(
            f"{error_msg}",
            title=f"[bold red]{error_type} Error[/bold red]",
            border_style="red",
            expand=False,
        )
        console.print(error_panel)

        # Show traceback if requested
        if show_traceback:
            console.print(Traceback.from_exception(type(error), error, error.__traceback__))

        # Find relevant solutions based on error message
        solutions = []
        for pattern, solution in ERROR_SOLUTIONS.items():
            if pattern.lower() in error_msg.lower() or pattern.lower() in error_type.lower():
                solutions.append(solution)

        # Find recovery suggestions based on error message
        recovery_suggestions = []
        for pattern, suggestions in RECOVERY_SUGGESTIONS.items():
            if pattern.lower() in error_msg.lower() or pattern.lower() in error_type.lower():
                recovery_suggestions.extend(suggestions)

        # Find relevant documentation links based on error type and message
        relevant_docs = []
        for keyword, link in DOC_LINKS.items():
            if keyword.lower() in error_msg.lower() or keyword.lower() in error_type.lower():
                relevant_docs.append(link)

        # Create a table with solutions and recovery suggestions
        if solutions or recovery_suggestions:
            help_table = Table(show_header=False, box=None, expand=False)
            help_table.add_column("Category", style="bold yellow")
            help_table.add_column("Content")

            if solutions:
                for solution in solutions:
                    help_table.add_row("Solution:", solution)

            if recovery_suggestions:
                for i, suggestion in enumerate(recovery_suggestions):
                    if i == 0:
                        help_table.add_row("Recovery:", suggestion)
                    else:
                        help_table.add_row("", suggestion)

            console.print(help_table)

        # Display documentation links if found
        if relevant_docs:
            docs_panel = Panel(
                "\n".join([f"• {doc}" for doc in relevant_docs]),
                title="[bold cyan]Relevant Documentation[/bold cyan]",
                border_style="cyan",
                expand=False,
            )
            console.print(docs_panel)

        # Always provide a general help tip
        bridge.display_result(
            "[dim]Run 'devsynth help' or 'devsynth <command> --help' for more information.[/dim]",
            highlight=False,
        )

    elif isinstance(error, dict):
        # Handle result dict with error message
        message = error.get("message", "Unknown error")
        code = error.get("code", "")
        details = error.get("details", "")

        # Log the error
        logger.error(f"Command error: {message} (Code: {code})")

        # Create a panel with the error details
        error_panel = Panel(
            f"{message}\n\n{details}" if details else message,
            title=f"[bold red]Error {code if code else ''}[/bold red]",
            border_style="red",
            expand=False,
        )
        console.print(error_panel)

        # Find relevant solutions based on error message
        solutions = []
        for pattern, solution in ERROR_SOLUTIONS.items():
            if pattern.lower() in message.lower():
                solutions.append(solution)

        # Find recovery suggestions based on error message
        recovery_suggestions = []
        for pattern, suggestions in RECOVERY_SUGGESTIONS.items():
            if pattern.lower() in message.lower():
                recovery_suggestions.extend(suggestions)

        # Create a table with solutions and recovery suggestions
        if solutions or recovery_suggestions:
            help_table = Table(show_header=False, box=None, expand=False)
            help_table.add_column("Category", style="bold yellow")
            help_table.add_column("Content")

            if solutions:
                for solution in solutions:
                    help_table.add_row("Solution:", solution)

            if recovery_suggestions:
                for i, suggestion in enumerate(recovery_suggestions):
                    if i == 0:
                        help_table.add_row("Recovery:", suggestion)
                    else:
                        help_table.add_row("", suggestion)

            console.print(help_table)

    else:
        # Handle string error message
        error_msg = str(error)
        logger.error(f"Command error: {error_msg}")

        # Create a panel with the error details
        error_panel = Panel(
            error_msg,
            title="[bold red]Error[/bold red]",
            border_style="red",
            expand=False,
        )
        console.print(error_panel)

    # Always provide a way to get help
    bridge.display_result(
        "[dim]For more help, visit https://devsynth.ai/docs or run 'devsynth doctor'.[/dim]",
        highlight=False,
    )