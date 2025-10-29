---

author: DevSynth Team
date: '2024-06-01'
last_reviewed: "2025-07-10"
status: published
tags:
- getting-started
- basic-usage
- tutorial
title: DevSynth Basic Usage Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Getting Started</a> &gt; DevSynth Basic Usage Guide
</div>

# DevSynth Basic Usage Guide

This guide provides essential information about the basic usage of DevSynth, including initializing a project, defining requirements, and generating code.

## Environment Requirements

Ensure you are using **Python 3.12 or higher**. Poetry is recommended for managing dependencies during development.

## Overview

DevSynth follows a structured workflow that takes you from requirements to working code. This guide covers the fundamental commands you'll use in a typical DevSynth project.

If you prefer a graphical interface, start the WebUI with `devsynth webui`. The WebUI provides pages that correspond to the CLI commands described below.

## Enable Shell Completion

DevSynth can generate shell completion scripts to speed up command entry:

```bash
devsynth completion --install
```

Run the above command to install completion for your current shell or pass `--shell zsh` to target a specific shell. Omit `--install` to print the script instead of saving it.

Alternatively, Typer's built-in option can be used:

```bash
devsynth --install-completion
```

## Initialize a Project

Start by creating a new DevSynth project:

```bash

# Create a new project directory

devsynth init --path ./my-project

# Navigate to the project directory

cd my-project
```

This command creates a new project directory with the necessary structure for DevSynth to work with. When executed inside an existing project, it now launches an interactive wizard that reads any `pyproject.toml` or `project.yaml` it finds.

Both the CLI and WebUI display a progress bar for each step and provide clearer warnings if initialization is aborted.

## Define Requirements

Create a file named `requirements.md` in your project directory with your project requirements:

```markdown

# Project Requirements

## Calculator Functionality

- The system shall provide addition of two numbers
- The system shall provide subtraction of two numbers
- The system shall provide multiplication of two numbers
- The system shall provide division of two numbers
```

Requirements should be clear, specific, and focused on what the system should do rather than how it should do it.

## Generate Specifications, Tests, and Code

Once you have defined your requirements, you can generate specifications, tests, and code:

```bash

# Generate specifications from requirements

devsynth inspect --requirements-file requirements.md

# Generate tests from specifications

devsynth run-pipeline

# Generate implementation code from tests

devsynth refactor
```

Each command builds on the output of the previous command, following a test-driven development approach.

## Run the Project

Finally, run the generated code to verify it works as expected:

```bash

# Run the generated code

devsynth run-pipeline
```

This command executes the generated code and provides feedback on its operation.

## Next Steps

For more detailed information about DevSynth's capabilities and advanced usage scenarios, see the [User Guide](../user_guides/user_guide.md).

## Related Documents

- [Quick Start Guide](quick_start_guide.md) - A step-by-step tutorial for getting started with DevSynth
- [Installation Guide](installation.md) - Detailed installation instructions
- [User Guide](../user_guides/user_guide.md) - Comprehensive guide for users
## Implementation Status

.
