"""Improved error handling for the DevSynth CLI.

This module provides improved error handling for the DevSynth CLI, including
detailed error messages with suggestions and documentation links.
"""

from typing import Dict, Optional, List, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from devsynth.exceptions import DevSynthError, CommandError, ValidationError, ConfigurationError


# Documentation links for different error types
DOCUMENTATION_LINKS = {
    "CommandError": "https://devsynth.ai/docs/cli/troubleshooting#command-errors",
    "ValidationError": "https://devsynth.ai/docs/cli/troubleshooting#validation-errors",
    "ConfigurationError": "https://devsynth.ai/docs/cli/troubleshooting#configuration-errors",
    "ProviderError": "https://devsynth.ai/docs/providers/troubleshooting",
    "LLMError": "https://devsynth.ai/docs/providers/llm/troubleshooting",
    "MemoryError": "https://devsynth.ai/docs/memory/troubleshooting",
    "default": "https://devsynth.ai/docs/troubleshooting",
}

# Suggestions for different error types
ERROR_SUGGESTIONS = {
    "CommandError": [
        "Check the command syntax and arguments",
        "Run the command with --help to see usage examples",
        "Ensure you're in the correct directory",
    ],
    "ValidationError": [
        "Check the input values against the expected format",
        "Ensure all required fields are provided",
        "Verify that file paths exist and are accessible",
    ],
    "ConfigurationError": [
        "Check your configuration file for syntax errors",
        "Ensure all required configuration options are set",
        "Run 'devsynth doctor' to diagnose configuration issues",
    ],
    "ProviderError": [
        "Check your provider API keys and credentials",
        "Verify your internet connection",
        "Ensure the provider service is available",
    ],
    "LLMError": [
        "Check your LLM provider API key",
        "Verify your internet connection",
        "Ensure you have sufficient quota with your LLM provider",
        "Try reducing the complexity of your prompt",
    ],
    "MemoryError": [
        "Check your memory store configuration",
        "Ensure required dependencies are installed",
        "Verify file permissions for file-based memory stores",
    ],
    "default": [
        "Check the command syntax and arguments",
        "Ensure you're in the correct directory",
        "Run 'devsynth doctor' to diagnose common issues",
    ],
}

# Common error patterns and their fixes
COMMON_ERRORS = {
    "No such file or directory": "The specified file or directory does not exist. Check the path and try again.",
    "Permission denied": "You don't have permission to access the specified file or directory. Check file permissions or run with elevated privileges.",
    "Connection refused": "Could not connect to the specified service. Ensure the service is running and accessible.",
    "API key": "There may be an issue with your API key. Check that it's correctly set in your configuration.",
    "Timeout": "The operation timed out. Check your internet connection or try again later.",
    "Invalid JSON": "The JSON data is invalid. Check the syntax and structure of your JSON file.",
    "YAML parsing error": "The YAML data is invalid. Check the syntax and structure of your YAML file.",
    "ImportError": "A required module could not be imported. Ensure all dependencies are installed.",
    "ModuleNotFoundError": "A required module could not be found. Ensure all dependencies are installed.",
}


def format_error_message(error: Exception) -> str:
    """Format an error message with detailed information.
    
    Args:
        error: The exception to format
        
    Returns:
        A formatted error message with detailed information
    """
    # Get the error type and message
    error_type = error.__class__.__name__
    error_message = str(error)
    
    # Get suggestions for this error type
    suggestions = ERROR_SUGGESTIONS.get(error_type, ERROR_SUGGESTIONS["default"])
    
    # Get documentation link for this error type
    doc_link = DOCUMENTATION_LINKS.get(error_type, DOCUMENTATION_LINKS["default"])
    
    # Check for common error patterns
    additional_info = None
    for pattern, fix in COMMON_ERRORS.items():
        if pattern.lower() in error_message.lower():
            additional_info = fix
            break
    
    # Format the error message
    formatted_message = f"[bold red]Error ({error_type}):[/bold red] {error_message}\n\n"
    
    if additional_info:
        formatted_message += f"[yellow]What happened:[/yellow] {additional_info}\n\n"
    
    formatted_message += "[yellow]Suggestions:[/yellow]\n"
    for suggestion in suggestions:
        formatted_message += f"- {suggestion}\n"
    
    formatted_message += f"\n[blue]Documentation:[/blue] {doc_link}"
    
    # If it's a DevSynthError, add details
    if isinstance(error, DevSynthError) and error.details:
        formatted_message += "\n\n[yellow]Details:[/yellow]"
        for key, value in error.details.items():
            formatted_message += f"\n- {key}: {value}"
    
    return formatted_message


def display_error(error: Exception, console: Console) -> None:
    """Display an error message with detailed information.
    
    Args:
        error: The exception to display
        console: The Rich console to use for output
    """
    formatted_message = format_error_message(error)
    console.print(Panel(formatted_message, title="Error", border_style="red"))


def create_error_table(errors: List[Dict[str, Any]], title: str = "Errors") -> Table:
    """Create a table of errors with their details.
    
    Args:
        errors: The list of errors
        title: The title of the table
        
    Returns:
        The table
    """
    table = Table(title=title)
    table.add_column("Error Type", style="red")
    table.add_column("Message")
    table.add_column("Suggestions", style="yellow")
    
    for error in errors:
        error_type = error.get("type", "Unknown")
        message = error.get("message", "")
        suggestions = error.get("suggestions", [])
        
        table.add_row(
            error_type,
            message,
            "\n".join([f"- {suggestion}" for suggestion in suggestions])
        )
        
    return table


def handle_command_error(error: CommandError, console: Console) -> None:
    """Handle a command error with detailed information.
    
    Args:
        error: The command error to handle
        console: The Rich console to use for output
    """
    # Get the command and arguments
    command = error.details.get("command", "Unknown")
    args = error.details.get("args", {})
    
    # Format the error message
    formatted_message = f"[bold red]Command Error:[/bold red] {error.message}\n\n"
    formatted_message += f"[yellow]Command:[/yellow] {command}\n"
    
    if args:
        formatted_message += "[yellow]Arguments:[/yellow]\n"
        for key, value in args.items():
            formatted_message += f"- {key}: {value}\n"
    
    # Get suggestions for this error
    suggestions = ERROR_SUGGESTIONS.get("CommandError", ERROR_SUGGESTIONS["default"])
    formatted_message += "\n[yellow]Suggestions:[/yellow]\n"
    for suggestion in suggestions:
        formatted_message += f"- {suggestion}\n"
    
    # Add documentation link
    doc_link = DOCUMENTATION_LINKS.get("CommandError", DOCUMENTATION_LINKS["default"])
    formatted_message += f"\n[blue]Documentation:[/blue] {doc_link}"
    
    # Display the error message
    console.print(Panel(formatted_message, title="Command Error", border_style="red"))


def handle_validation_error(error: ValidationError, console: Console) -> None:
    """Handle a validation error with detailed information.
    
    Args:
        error: The validation error to handle
        console: The Rich console to use for output
    """
    # Get the field, value, and constraints
    field = error.details.get("field", "Unknown")
    value = error.details.get("value", "")
    constraints = error.details.get("constraints", {})
    
    # Format the error message
    formatted_message = f"[bold red]Validation Error:[/bold red] {error.message}\n\n"
    formatted_message += f"[yellow]Field:[/yellow] {field}\n"
    formatted_message += f"[yellow]Value:[/yellow] {value}\n"
    
    if constraints:
        formatted_message += "[yellow]Constraints:[/yellow]\n"
        for key, value in constraints.items():
            formatted_message += f"- {key}: {value}\n"
    
    # Get suggestions for this error
    suggestions = ERROR_SUGGESTIONS.get("ValidationError", ERROR_SUGGESTIONS["default"])
    formatted_message += "\n[yellow]Suggestions:[/yellow]\n"
    for suggestion in suggestions:
        formatted_message += f"- {suggestion}\n"
    
    # Add documentation link
    doc_link = DOCUMENTATION_LINKS.get("ValidationError", DOCUMENTATION_LINKS["default"])
    formatted_message += f"\n[blue]Documentation:[/blue] {doc_link}"
    
    # Display the error message
    console.print(Panel(formatted_message, title="Validation Error", border_style="red"))


def handle_configuration_error(error: ConfigurationError, console: Console) -> None:
    """Handle a configuration error with detailed information.
    
    Args:
        error: The configuration error to handle
        console: The Rich console to use for output
    """
    # Get the config key and value
    config_key = error.details.get("config_key", "Unknown")
    config_value = error.details.get("config_value", "")
    
    # Format the error message
    formatted_message = f"[bold red]Configuration Error:[/bold red] {error.message}\n\n"
    formatted_message += f"[yellow]Configuration Key:[/yellow] {config_key}\n"
    formatted_message += f"[yellow]Value:[/yellow] {config_value}\n"
    
    # Get suggestions for this error
    suggestions = ERROR_SUGGESTIONS.get("ConfigurationError", ERROR_SUGGESTIONS["default"])
    formatted_message += "\n[yellow]Suggestions:[/yellow]\n"
    for suggestion in suggestions:
        formatted_message += f"- {suggestion}\n"
    
    # Add documentation link
    doc_link = DOCUMENTATION_LINKS.get("ConfigurationError", DOCUMENTATION_LINKS["default"])
    formatted_message += f"\n[blue]Documentation:[/blue] {doc_link}"
    
    # Display the error message
    console.print(Panel(formatted_message, title="Configuration Error", border_style="red"))


def handle_error(error: Exception, console: Console) -> None:
    """Handle an error with detailed information.
    
    This function dispatches to the appropriate handler based on the error type.
    
    Args:
        error: The error to handle
        console: The Rich console to use for output
    """
    if isinstance(error, CommandError):
        handle_command_error(error, console)
    elif isinstance(error, ValidationError):
        handle_validation_error(error, console)
    elif isinstance(error, ConfigurationError):
        handle_configuration_error(error, console)
    else:
        display_error(error, console)