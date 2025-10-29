---
title: "DevSynth CLI UX Guide"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "user-guide"
  - "cli"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# DevSynth CLI UX Guide

This guide provides information on the user experience features of the DevSynth command-line interface (CLI). It covers progress indicators, error handling, shell completion, and output formatting.

## Table of Contents

- [Progress Indicators](#progress-indicators)
  - [Basic Progress Indicators](#basic-progress-indicators)
  - [Long-Running Progress Indicators](#long-running-progress-indicators)
  - [Using Progress Indicators in Your Code](#using-progress-indicators-in-your-code)
- [Error Handling](#error-handling)
  - [Actionable Error Suggestions](#actionable-error-suggestions)
  - [Context-Specific Suggestions](#context-specific-suggestions)
  - [Using Enhanced Error Handling in Your Code](#using-enhanced-error-handling-in-your-code)
- [Shell Completion](#shell-completion)
  - [Installing Shell Completion](#installing-shell-completion)
  - [Using Shell Completion](#using-shell-completion)
- [Command Output Formatting](#command-output-formatting)
  - [Output Types](#output-types)
  - [Output Styles](#output-styles)
  - [Using Standardized Output Formatting in Your Code](#using-standardized-output-formatting-in-your-code)

## Progress Indicators

DevSynth provides progress indicators to give users feedback during long-running operations. These indicators show the progress of the operation, estimated time remaining, and other useful information.

### Basic Progress Indicators

Basic progress indicators are suitable for most operations and provide a simple progress bar with a description and percentage complete.

Example:

```text
[######################] 100% Complete
```

### Long-Running Progress Indicators

For operations that take a long time to complete, DevSynth provides enhanced progress indicators with additional features:

- Estimated completion time
- Operation history tracking
- Periodic status updates
- Adaptive refresh rate
- Detailed subtask tracking
- Checkpoint saving

Example:

```text
Main task [######################] 100% 10/10 0:00:00 Complete
  ↳ Subtask 1 [######################] 100% Complete
  ↳ Subtask 2 [######################] 100% Complete
  ↳ Subtask 3 [######################] 100% Complete

Task completed in 0:05:23
```

### Using Progress Indicators in Your Code

To use progress indicators in your code, you can use the `CLIProgressIndicator` class for basic progress indicators or the `LongRunningProgressIndicator` class for long-running operations.

#### Basic Progress Indicator

```python
from devsynth.interface.cli import CLIUXBridge

def my_command(bridge=None):
    # Get the bridge
    ux_bridge = bridge or CLIUXBridge()

    # Create a progress indicator
    progress = ux_bridge.create_progress("Processing files", total=100)

    # Update the progress
    for i in range(100):
        # Do some work
        progress.update(advance=1)

    # Complete the progress
    progress.complete()
```

#### Long-Running Progress Indicator

```python
from devsynth.interface.cli import CLIUXBridge
from devsynth.application.cli.long_running_progress import run_with_long_running_progress

def my_long_running_task(progress_callback=None):
    # Do some work
    for i in range(100):
        # Update the progress
        if progress_callback:
            progress_callback(advance=1, status=f"Processing item {i}")

    # Return the result
    return "Task completed successfully"

def my_command(bridge=None):
    # Get the bridge
    ux_bridge = bridge or CLIUXBridge()

    # Run the task with a long-running progress indicator
    result = run_with_long_running_progress(
        "My long-running task",
        my_long_running_task,
        ux_bridge,
        total=100,
        subtasks=[
            {"name": "Subtask 1", "total": 100},
            {"name": "Subtask 2", "total": 100},
            {"name": "Subtask 3", "total": 100},
        ]
    )

    # Display the result
    ux_bridge.display_result(result, message_type="success")
```

## Error Handling

DevSynth provides enhanced error handling with actionable suggestions to help users resolve errors quickly. When an error occurs, DevSynth displays a detailed error message with suggestions for how to fix the error.

### Actionable Error Suggestions

Actionable error suggestions provide specific steps that users can take to resolve an error. They include:

- A description of the error
- Actionable steps to resolve the error
- Links to relevant documentation
- Example commands or code
- Related errors

Example:

```text
Error: MemorySyncError

An error occurred while executing the command.

Error Type: MemorySyncError
Message: Failed to synchronize memory stores

Suggestions:

There may be issues with cross-store memory synchronization.

Actionable steps:
1. Check that all memory stores are properly configured
2. Verify that the memory synchronization service is running
3. Check the memory integration logs for errors
4. Try restarting the memory synchronization service

Documentation: https://devsynth.readthedocs.io/en/latest/user_guides/memory_integration.html

Example command: devsynth doctor --check-memory-integration

Example code:
# Example of proper memory store configuration
memory_manager = MemoryManager(
    adapters={
        "primary": PrimaryMemoryAdapter(),
        "secondary": SecondaryMemoryAdapter()
    },
    sync_enabled=True
)

Related errors:
- MemorySyncError
- CrossStoreIntegrationError
- MemoryAdapterNotFoundError

For more help, run: devsynth doctor or visit: https://devsynth.readthedocs.io/en/latest/user_guides/troubleshooting.html
```

### Context-Specific Suggestions

DevSynth also provides context-specific suggestions based on the current state of the system. For example, if an error occurs during test execution, DevSynth will provide suggestions specific to testing.

### Using Enhanced Error Handling in Your Code

To use enhanced error handling in your code, you can use the `ImprovedErrorHandler` class.

```python
from devsynth.interface.enhanced_error_handler import improved_error_handler
from devsynth.interface.cli import CLIUXBridge
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.exceptions import DevSynthError

def my_command(bridge=None):
    # Get the bridge
    ux_bridge = bridge or CLIUXBridge()

    try:
        # Do some work that might raise an error
        memory_manager = MemoryManager()

        # This might raise a DevSynthError if the memory store is not configured
        result = memory_manager.get("key_that_might_not_exist")

        # Display the result
        ux_bridge.display_result(result, message_type="success")
    except DevSynthError as e:
        # Use the improved error handler to format the error
        formatted_error = improved_error_handler.format_error(e)

        # Display the error
        ux_bridge.console.print(formatted_error)
```

## Shell Completion

DevSynth provides shell completion for bash, zsh, and fish shells to make it easier to use the CLI. Shell completion allows you to press the Tab key to complete commands, options, and arguments.

### Installing Shell Completion

Pre-built completion scripts are available in `scripts/completions/` for Bash, Zsh, and Fish. You can source these files directly or install them using the `completion` command:

```bash
# Install shell completion for the current shell
devsynth completion --install

# Install shell completion for a specific shell
devsynth completion --shell bash --install

# Use Typer's built-in helper
devsynth --install-completion
```

### Using Shell Completion

Once shell completion is installed, you can use it by pressing the Tab key while typing a DevSynth command:

```bash
# Press Tab to complete the command
devsynth comp<Tab>  # Completes to "devsynth completion"

# Press Tab to see available options
devsynth completion --<Tab>  # Shows available options: --shell, --install, --output

# Press Tab to complete option values
devsynth completion --shell <Tab>  # Shows available shells: bash, zsh, fish
```

## Command Output Formatting

DevSynth provides standardized output formatting for different types of command output to ensure a consistent user experience across all commands.

### Output Types

DevSynth supports the following output types:

- **RESULT**: General command result
- **SUCCESS**: Success message
- **ERROR**: Error message
- **WARNING**: Warning message
- **INFO**: Informational message
- **DATA**: Data output (table, list, etc.)
- **HELP**: Help text
- **DEBUG**: Debug information

Each output type has a specific style to make it easy to distinguish between different types of output.

### Output Styles

DevSynth supports the following output styles:

- **MINIMAL**: Minimal styling (plain text)
- **SIMPLE**: Simple styling (basic formatting)
- **STANDARD**: Standard styling (default)
- **DETAILED**: Detailed styling (more information)
- **COMPACT**: Compact styling (less whitespace)
- **EXPANDED**: Expanded styling (more whitespace)

### Using Standardized Output Formatting in Your Code

To use standardized output formatting in your code, you can use the `StandardizedOutputFormatter` class.

```python
from devsynth.application.cli.command_output_formatter import (
    standardized_formatter,
    CommandOutputType,
    CommandOutputStyle,
)

def my_command():
    # Format a message
    message = standardized_formatter.format_message(
        "Operation completed successfully",
        output_type=CommandOutputType.SUCCESS,
        output_style=CommandOutputStyle.STANDARD,
        title="Success",
    )

    # Display the message
    standardized_formatter.console.print(message)

    # Format a table
    data = [
        {"name": "Item 1", "value": 42},
        {"name": "Item 2", "value": 84},
        {"name": "Item 3", "value": 126},
    ]
    table = standardized_formatter.format_table(
        data,
        output_style=CommandOutputStyle.STANDARD,
        title="Results",
    )

    # Display the table
    standardized_formatter.console.print(table)

    # Format a list
    items = ["Item 1", "Item 2", "Item 3"]
    list_output = standardized_formatter.format_list(
        items,
        output_style=CommandOutputStyle.STANDARD,
        title="Items",
    )

    # Display the list
    standardized_formatter.console.print(list_output)

    # Format code
    code = """
    def hello_world():
        print("Hello, world!")
    """
    code_output = standardized_formatter.format_code(
        code,
        language="python",
        output_style=CommandOutputStyle.STANDARD,
        title="Example Code",
    )

    # Display the code
    standardized_formatter.console.print(code_output)

    # Format help text
    help_output = standardized_formatter.format_help(
        "my-command",
        "This command does something useful",
        "devsynth my-command [OPTIONS]",
        [
            {"description": "Basic usage", "command": "devsynth my-command"},
            {"description": "Advanced usage", "command": "devsynth my-command --option value"},
        ],
        [
            {"name": "--option", "description": "An option", "default": "default"},
            {"name": "--flag", "description": "A flag"},
        ],
        output_style=CommandOutputStyle.STANDARD,
    )

    # Display the help text
    standardized_formatter.console.print(help_output)

    # Format and display a command result in one step
    standardized_formatter.display(
        "Operation completed successfully",
        output_type=CommandOutputType.SUCCESS,
        output_style=CommandOutputStyle.STANDARD,
        title="Success",
    )
```

## Conclusion

DevSynth provides a rich set of CLI UX features to enhance the user experience, including progress indicators, error handling, shell completion, and output formatting. By using these features in your code, you can provide a consistent and user-friendly experience for DevSynth users.
