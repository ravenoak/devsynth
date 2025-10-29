---

title: "UXBridge Architecture"
date: "2025-07-07"
version: "0.1.0a1"
tags:
  - "architecture"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; UXBridge Architecture
</div>

# UXBridge Architecture

## Overview

The UXBridge architecture is a core component of DevSynth's hexagonal architecture, providing a consistent interface for user interactions across different user interfaces (CLI, WebUI, API). This document explains the UXBridge architecture, its components, and how to extend it with new implementations.

## Purpose

The UXBridge serves as an abstraction layer between the application logic and the user interface, allowing DevSynth to:

1. **Maintain UI-agnostic core logic**: The application's core functionality doesn't need to know which UI is being used
2. **Provide consistent user experience**: Ensure that the same operations behave consistently across different interfaces
3. **Enable easy extension**: New user interfaces can be added without modifying the core application logic
4. **Facilitate testing**: Core logic can be tested independently of the UI


## Architecture Components

### UXBridge Abstract Base Class

The `UXBridge` abstract base class defines the interface that all UI implementations must follow. It includes methods for:

- Displaying results to the user
- Asking questions and collecting input
- Confirming choices
- Creating and managing progress indicators


### ProgressIndicator Abstract Base Class

The `ProgressIndicator` abstract base class defines the interface for progress tracking across different UIs. It includes methods for:

- Updating progress
- Completing progress
- Managing subtasks


### Concrete Implementations

DevSynth includes several concrete implementations of the UXBridge:

1. **CLIUXBridge**: Implementation for the command-line interface
2. **WebUI**: Implementation for the NiceGUI-based web interface
3. **APIBridge**: Implementation for the FastAPI-based API


Each implementation provides the same interface but renders the interactions appropriately for its target platform.

## Class Hierarchy

```text
UXBridge (Abstract Base Class)
├── CLIUXBridge
│   └── _CLIProgress (implements ProgressIndicator)
├── WebUI
│   └── _UIProgress (implements ProgressIndicator)
└── APIBridge
    └── _APIProgress (implements ProgressIndicator)
```

## Key Methods

### UXBridge Methods

| Method | Description |
|--------|-------------|
| `display_result(message, highlight=False)` | Display a message to the user |
| `ask_question(message, choices=None, default=None, show_default=True)` | Ask a question and return the user's response |
| `confirm_choice(message, default=False)` | Ask for confirmation and return a boolean |
| `create_progress(description, total=100)` | Create a progress indicator |

### ProgressIndicator Methods

| Method | Description |
|--------|-------------|
| `update(advance=1, description=None)` | Update progress by the specified amount |
| `complete()` | Mark the progress as complete |
| `add_subtask(description, total=100)` | Add a subtask with its own progress tracking |
| `update_subtask(task_id, advance=1, description=None)` | Update a subtask's progress |
| `complete_subtask(task_id)` | Mark a subtask as complete |

## Implementation Details

### CLIUXBridge

The CLI implementation uses the Rich library to provide colorful, formatted output in the terminal. It includes:

- Colorized output with syntax highlighting
- Progress bars with ETA and subtask support
- Interactive prompts for questions and confirmations


### WebUI

The WebUI implementation uses NiceGUI to render the user interface in a web browser. It includes:

- NiceGUI components for displaying messages
- Form inputs for questions
- Checkboxes for confirmations
- Progress bars with subtask support


### APIBridge

The API implementation captures messages and provides a way to pre-supply answers for questions. It includes:

- Message collection for later retrieval
- Pre-defined answers for non-interactive usage
- Progress tracking that captures updates as messages


## Extending UXBridge

To create a new UXBridge implementation:

1. Create a new class that inherits from `UXBridge`
2. Implement all required methods
3. Create a nested class that inherits from `ProgressIndicator` for progress tracking


### Example: Minimal Implementation

```python
from devsynth.interface.ux_bridge import UXBridge, ProgressIndicator, sanitize_output

class MinimalUXBridge(UXBridge):
    """A minimal UXBridge implementation."""

    def display_result(self, message: str, *, highlight: bool = False) -> None:
        """Display a message to the user."""
        print(sanitize_output(message))

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str:
        """Ask a question and return the user's response."""
        print(sanitize_output(message))
        if choices:
            print(f"Choices: {', '.join(choices)}")
        if default and show_default:
            print(f"Default: {default}")
        return input("> ") or default or ""

    def confirm_choice(self, message: str, *, default: bool = False) -> bool:
        """Ask for confirmation and return a boolean."""
        print(sanitize_output(message))
        print(f"Default: {'yes' if default else 'no'}")
        response = input("(y/n)> ").lower()
        if not response:
            return default
        return response.startswith("y")

    class _MinimalProgress(ProgressIndicator):
        """A minimal progress indicator."""

        def __init__(self, description: str, total: int) -> None:
            """Initialize with a description and total steps."""
            self.description = description
            self.total = total
            self.current = 0
            self.subtasks = {}
            print(f"Starting: {description} (0/{total})")

        def update(
            self,
            *,
            advance: float = 1,
            description: Optional[str] = None,
            status: Optional[str] = None,
        ) -> None:
            """Update progress by the specified amount."""
            self.current += advance
            if description:
                self.description = description
            status_msg = status or ""
            print(
                f"Progress: {self.description} ({self.current}/{self.total}) {status_msg}"
            )

        def complete(self) -> None:
            """Mark the progress as complete."""
            self.current = self.total
            print(f"Completed: {self.description}")

        def add_subtask(self, description: str, total: int = 100) -> str:
            """Add a subtask with its own progress tracking."""
            task_id = f"subtask_{len(self.subtasks)}"
            self.subtasks[task_id] = {
                "description": description,
                "total": total,
                "current": 0,
            }
            print(f"Subtask started: {description} (0/{total})")
            return task_id

        def update_subtask(
            self, task_id: str, advance: float = 1, description: Optional[str] = None
        ) -> None:
            """Update a subtask's progress."""
            if task_id not in self.subtasks:
                raise ValueError(f"Unknown subtask ID: {task_id}")

            subtask = self.subtasks[task_id]
            subtask["current"] += advance
            if description:
                subtask["description"] = description

            print(f"Subtask progress: {subtask['description']} ({subtask['current']}/{subtask['total']})")

        def complete_subtask(self, task_id: str) -> None:
            """Mark a subtask as complete."""
            if task_id not in self.subtasks:
                raise ValueError(f"Unknown subtask ID: {task_id}")

            subtask = self.subtasks[task_id]
            subtask["current"] = subtask["total"]
            print(f"Subtask completed: {subtask['description']}")

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator:
        """Create a progress indicator with the given description and total steps."""
        return self._MinimalProgress(sanitize_output(description), total)
```

## Best Practices

When implementing or extending UXBridge:

1. **Always sanitize output**: Use the `sanitize_output` function to prevent security issues
2. **Handle edge cases**: Account for None values, empty strings, and other edge cases
3. **Maintain consistency**: Ensure your implementation behaves consistently with other UXBridge implementations
4. **Write tests**: Create unit tests that verify your implementation works correctly
5. **Document your code**: Add docstrings and comments to explain your implementation


## Testing UXBridge Implementations

DevSynth includes several test suites for verifying UXBridge implementations:

1. **Unit tests**: Test each method in isolation
2. **Integration tests**: Test the UXBridge with actual application logic
3. **Behavior tests**: Test user interactions using BDD scenarios
4. **Parity tests**: Ensure different implementations produce the same results for the same inputs


When creating a new UXBridge implementation, run these tests to ensure compatibility.

## Conclusion

The UXBridge architecture is a powerful abstraction that enables DevSynth to provide a consistent user experience across different interfaces. By understanding this architecture, you can extend DevSynth with new user interfaces or enhance existing ones while maintaining compatibility with the core application logic.
## Implementation Status

.
