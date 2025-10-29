---

author: DevSynth Team
date: '2025-07-31'
last_reviewed: "2025-07-31"
status: published
tags:
- development
- cli
- ux
- progress
title: Progress Indicators Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Progress Indicators Guide
</div>

# Progress Indicators Guide

This guide explains how to use progress indicators for long-running operations in DevSynth commands and interfaces.

## Overview

Progress indicators provide visual feedback to users during long-running operations, helping them understand:

- That the operation is still running and not frozen
- How much of the operation has been completed
- How much time remains until completion
- What specific step or phase is currently being processed

DevSynth provides a comprehensive set of utilities for creating and managing progress indicators in a consistent way across all interfaces (CLI, WebUI, API).

## Basic Usage

### Simple Progress Indicator

The simplest way to use a progress indicator is with the `progress_indicator` context manager:

```python
from devsynth.interface.progress_utils import progress_indicator

def my_command(self):
    # Create a progress indicator for a long-running operation
    with progress_indicator(self, "Processing files", total=100) as progress:
        # Perform the operation, updating progress as you go
        for i in range(100):
            # Do some work
            process_file(i)

            # Update the progress indicator
            progress.update(advance=1)
```

The progress indicator will automatically be completed when the context manager exits, even if an exception occurs.

### Tracking Progress Through Lists

For operations that process lists of items, you can use the `track_progress` function:

```python
from devsynth.interface.progress_utils import track_progress

def process_files(self, files):
    # Create a tracked list that updates progress as items are accessed
    tracked_files = track_progress(self, files, "Processing files")

    # Process each file - progress will be updated automatically
    for file in tracked_files:
        process_file(file)
```

### Function Decorator

You can also use the `with_progress` decorator to add progress indicators to functions:

```python
from devsynth.interface.progress_utils import with_progress

@with_progress(bridge, "Processing files", total=100)
def process_files(files, progress=None):
    # The progress indicator is automatically passed as a keyword argument
    for i, file in enumerate(files):
        process_file(file)
        progress.update(advance=1)
```

## Advanced Usage

### Progress Manager

For more complex operations with multiple phases or nested operations, you can use the `ProgressManager` class:

```python
from devsynth.interface.progress_utils import create_progress_manager

def complex_operation(self):
    # Create a progress manager
    manager = create_progress_manager(self)

    # Create a progress indicator for the overall operation
    with manager.progress("Complex operation", total=3, key="main") as main_progress:
        # Phase 1
        main_progress.update(description="Phase 1: Data collection")
        with manager.progress("Collecting data", total=100, key="phase1") as phase1_progress:
            for i in range(100):
                collect_data(i)
                phase1_progress.update(advance=1)

        # Update the main progress
        main_progress.update(advance=1, description="Phase 2: Data processing")

        # Phase 2
        with manager.progress("Processing data", total=100, key="phase2") as phase2_progress:
            for i in range(100):
                process_data(i)
                phase2_progress.update(advance=1)

        # Update the main progress
        main_progress.update(advance=1, description="Phase 3: Data analysis")

        # Phase 3
        with manager.progress("Analyzing data", total=100, key="phase3") as phase3_progress:
            for i in range(100):
                analyze_data(i)
                phase3_progress.update(advance=1)

        # Update the main progress
        main_progress.update(advance=1, description="Operation complete")
```

The `ProgressManager` keeps track of all active progress indicators and ensures they are properly completed, even if an exception occurs.

### Progress Tracker

For operations where the total number of steps is unknown or may change, you can use the `ProgressTracker` class:

```python
from devsynth.interface.progress_utils import progress_indicator, ProgressTracker

def process_data_stream(self, stream):
    # Create a progress indicator
    with progress_indicator(self, "Processing data stream") as indicator:
        # Create a progress tracker with unknown total
        tracker = ProgressTracker(indicator, total=None)

        # Process the stream, updating progress as you go
        with tracker:
            for chunk in stream:
                process_chunk(chunk)
                tracker.update(advance=1)
```

The `ProgressTracker` will estimate the total number of steps based on the current progress and elapsed time, providing a reasonable progress percentage even when the total is unknown.

## Implementation Details

### UXBridge Integration

Progress indicators are implemented through the `UXBridge` interface, which provides a `create_progress` method that returns a `ProgressIndicator` instance. Each interface (CLI, WebUI, API) provides its own implementation of `ProgressIndicator` that is appropriate for that interface.

The progress utilities in `devsynth.interface.progress_utils` build on this foundation to provide a more convenient and consistent interface for using progress indicators.

### CLI Progress Indicators

In the CLI, progress indicators are implemented using the Rich library's Progress component, which provides a visually appealing progress bar with spinner, text, percentage, and time remaining.

Example CLI progress indicator:

```text
⠹ Processing files [████████████████████████████████████████] 100% Complete   0:00:00
```

### WebUI Progress Indicators

In the WebUI, progress indicators are implemented using NiceGUI's progress bar component, which provides a simple progress bar with percentage.

### API Progress Indicators

In the API, progress indicators update the status of the operation in the response, allowing clients to track progress through API calls.

## Best Practices

### When to Use Progress Indicators

Use progress indicators for operations that:

- Take more than a second to complete
- Have multiple steps or phases
- Process large amounts of data
- Involve network or file I/O
- May appear to be frozen or unresponsive without feedback

### Providing Meaningful Descriptions

Make sure to provide meaningful descriptions for progress indicators:

- Use clear, concise language
- Include the current phase or step
- Update the description as the operation progresses
- Include relevant context (e.g., file names, counts)

Example:

```python
# Initial description
progress.update(description="Processing files")

# Update with more specific information
progress.update(description=f"Processing file {i+1}/{total}: {filename}")

# Update with completion information
progress.update(description=f"Processed {total} files successfully")
```

### Updating Status Messages

In addition to updating the progress percentage, you can also update the status message to provide more detailed information:

```python
# Update with status message
progress.update(advance=1, status="Validating data...")

# Update with more specific status
progress.update(advance=1, status=f"Processing record {i+1}")

# Update with completion status
progress.update(advance=1, status="Complete")
```

### Handling Errors

Make sure to properly handle errors and complete progress indicators even when exceptions occur:

```python
try:
    with progress_indicator(self, "Processing files") as progress:
        for i in range(100):
            try:
                process_file(i)
                progress.update(advance=1)
            except FileProcessingError as e:
                # Log the error but continue processing
                logger.error(f"Error processing file {i}: {e}")
                progress.update(advance=1, status=f"Error: {e}")
except Exception as e:
    # Handle fatal errors
    logger.error(f"Fatal error: {e}")
    # The progress indicator will be automatically completed by the context manager
```

### Testing with Progress Indicators

When writing tests for code that uses progress indicators, you can use the `_DummyProgress` implementation provided by `UXBridge`:

```python
def test_my_function():
    # Create a mock bridge
    bridge = MagicMock(spec=UXBridge)

    # Set up the mock to return a dummy progress indicator
    dummy_progress = bridge.create_progress.return_value

    # Call the function being tested
    my_function(bridge)

    # Verify that the progress indicator was created and updated
    bridge.create_progress.assert_called_once_with("Expected description", total=100)
    dummy_progress.update.assert_called()
    dummy_progress.complete.assert_called_once()
```

## Conclusion

Using progress indicators consistently across all DevSynth commands and interfaces provides a better user experience by giving clear feedback during long-running operations. The utilities in `devsynth.interface.progress_utils` make it easy to add progress indicators to your code with minimal effort.
