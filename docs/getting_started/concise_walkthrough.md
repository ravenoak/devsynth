---
author: DevSynth Team
date: '2025-06-15'
last_reviewed: "2025-07-10"
status: published
tags:

- getting-started
- quick-start
- tutorial

title: Concise DevSynth Walkthrough
version: 0.1.0
---

# Concise DevSynth Walkthrough

This walkthrough provides a short overview of the DevSynth workflow.
For additional details, see the [Quick Start Guide](quick_start_guide.md).

## Environment Requirements

DevSynth requires **Python 3.11 or higher**. Poetry is recommended for managing dependencies.

If you prefer a GUI, you can run `devsynth webui` and follow the same steps using the WebUI pages.

## 1. Initialize a Project

Create a new project directory named `demo`:

```bash

# Create and enter the project directory

devsynth init --path demo
cd demo
```

`devsynth init` now walks you through an interactive setup if it detects existing project files.

The command generates a `.devsynth/project.yaml` file. For reference, you can look at the example configuration in [`templates/project.yaml`](../../templates/project.yaml).

## 2. Add Requirements

Create a `requirements.md` file with a few simple requirements. Example:

```markdown

# Project Requirements

- The system shall add two numbers.
- The system shall subtract two numbers.

```

## 3. Generate Specs, Tests, and Code

Run the DevSynth commands in sequence:

```bash

# Generate specifications

devsynth inspect

# Generate tests

devsynth run-pipeline

# Generate implementation code

devsynth refactor
```

## 4. Run the Tests

Execute the generated tests with either `pytest` or the DevSynth runner:

```bash

# Using pytest

pytest

# Or using DevSynth

devsynth run-pipeline
```

If the tests pass, your generated code is working. If you encounter issues, see the [Troubleshooting Guide](troubleshooting.md).

---

For a complete walkthrough with more context, consult the [Quick Start Guide](quick_start_guide.md).
