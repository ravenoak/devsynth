---

author: DevSynth Team
date: '2025-07-31'
last_reviewed: "2025-07-31"
status: published
tags:
- development
- cli
- formatting
- ux
title: Command Output Formatting Guide
version: "0.1.0-alpha.1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Command Output Formatting Guide
</div>

# Command Output Formatting Guide

This guide explains how to use the CommandOutput utility to format command output consistently across all DevSynth commands and interfaces.

## Overview

The CommandOutput utility provides a standardized way to format and display different types of output (messages, errors, warnings, tables, etc.) with consistent styling and error handling. It ensures that all DevSynth commands present information to users in a clear, consistent, and visually appealing way.

## Basic Usage

### Importing the Utility

```python
from devsynth.interface.command_output import command_output, MessageType
```

The module provides a singleton instance `command_output` for easy access, as well as a `MessageType` enum for standard message types.

### Displaying Messages

To display a simple message:

```python
# Display a normal message
command_output.display_message("Operation completed")

# Display a message with a specific type
command_output.display_message("Operation completed successfully", MessageType.SUCCESS)

# Display a highlighted message
command_output.display_message("Important information", highlight=True)
```

### Using Specialized Methods

The utility provides specialized methods for different types of messages:

```python
# Display a success message
command_output.display_success("Operation completed successfully")

# Display an error message
command_output.display_error("Failed to complete operation")

# Display a warning message
command_output.display_warning("Operation may take a long time")

# Display an info message
command_output.display_info("Processing file: example.txt")

# Display a heading
command_output.display_heading("Operation Results", level=2)
```

### Formatting Without Displaying

If you need to format a message without displaying it immediately:

```python
# Format a message
formatted = command_output.format_message("Operation completed", MessageType.SUCCESS)

# Format an error message
formatted_error = command_output.format_error("Failed to complete operation")

# Format a success message
formatted_success = command_output.format_success("Operation completed successfully")
```

## Formatting Structured Data

### Tables

To display tabular data:

```python
data = {
    "name": "example",
    "version": "1.0.0",
    "status": "active"
}

# Display a table
command_output.display_table(data, title="Project Information")
```

### Lists

To display a list of items:

```python
items = ["item1", "item2", "item3"]

# Display a list
command_output.display_list(items, title="Available Items")
```

### JSON and YAML

To display data in JSON or YAML format:

```python
data = {
    "name": "example",
    "version": "1.0.0",
    "status": "active",
    "dependencies": ["dep1", "dep2"]
}

# Display as JSON
command_output.display_json(data, title="Project Configuration")

# Display as YAML
command_output.display_yaml(data, title="Project Configuration")
```

## Command Results

For CLI commands that return structured results, use the `display_command_result` method:

```python
result = {
    "status": "success",
    "message": "Operation completed successfully",
    "data": {
        "name": "example",
        "version": "1.0.0"
    }
}

# Display the command result in the default format
command_output.display_command_result(result, title="Operation Result")

# Display the command result in a specific format
command_output.display_command_result(result, format_name="json", title="Operation Result")
```

## Error Handling

The utility provides enhanced error handling with actionable suggestions:

```python
try:
    # Some operation that might fail
    with open("nonexistent_file.txt", "r") as f:
        content = f.read()
except Exception as e:
    # Display the error with suggestions
    command_output.display_error(e)
```

The error message will include actionable suggestions based on the error content, such as:

- For permission errors: "Check file permissions or run with elevated privileges"
- For "not found" errors: "Verify the file path or resource name"
- For timeout errors: "Check network connectivity or increase timeout settings"
- For API key errors: "Verify your API key is correctly set in the configuration"

## Integration with UXBridge

The CommandOutput utility is designed to work with the UXBridge interface. To use it in a class that extends UXBridge:

```python
from devsynth.interface.ux_bridge import UXBridge
from devsynth.interface.command_output import command_output

class MyCommand(UXBridge):
    def __init__(self):
        super().__init__()
        # Set the console for the command_output utility
        command_output.set_console(self.console)

    def display_result(self, message: str, *, highlight: bool = False, message_type: str = None) -> None:
        """Override the display_result method to use CommandOutput."""
        command_output.display_message(message, message_type, highlight)

    def handle_error(self, error: Exception) -> None:
        """Override the handle_error method to use CommandOutput."""
        command_output.display_error(error)
```

## Best Practices

### Message Types

Use the appropriate message type for each situation:

- `MessageType.SUCCESS`: For successful operations
- `MessageType.ERROR`: For errors and failures
- `MessageType.WARNING`: For warnings and potential issues
- `MessageType.INFO`: For informational messages
- `MessageType.HEADING`: For section headings
- `MessageType.NORMAL`: For normal messages (default)

### Formatting Guidelines

1. **Be Consistent**: Use the same formatting for similar types of information across all commands.
2. **Be Clear**: Use clear and concise language in messages.
3. **Use Headings**: Use headings to organize complex output.
4. **Provide Context**: Include relevant context in error messages.
5. **Offer Solutions**: Include actionable suggestions in error messages.
6. **Use Color Appropriately**: Use color to highlight important information, but don't rely on it exclusively (consider colorblind users).

### Command Output Structure

For commands that produce structured output, follow this general structure:

1. **Title**: A clear title describing the output
2. **Summary**: A brief summary of the operation result
3. **Details**: Detailed information about the operation
4. **Next Steps**: Suggested next steps for the user

Example:

```python
# Display a heading for the command
command_output.display_heading("Generate Specifications", level=1)

# Display a summary of the operation
command_output.display_success("Specifications generated successfully")

# Display details about the operation
command_output.display_info(f"Generated {len(specs)} specifications from {requirements_file}")

# Display the generated specifications
command_output.display_table(specs, title="Generated Specifications")

# Display next steps
command_output.display_info("Next steps:")
command_output.display_list([
    "Review the generated specifications",
    "Run 'devsynth test' to generate tests from specifications",
    "Run 'devsynth code' to generate code from tests"
])
```

## Conclusion

Using the CommandOutput utility ensures that all DevSynth commands present information to users in a consistent and user-friendly way. By following the guidelines in this document, you can create commands that provide a seamless and intuitive user experience.
