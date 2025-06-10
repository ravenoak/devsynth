---
title: "Concise DevSynth Walkthrough"
date: "2025-06-15"
version: "1.0.0"
tags:
  - "getting-started"
  - "quick-start"
  - "tutorial"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-15"
---

# Concise DevSynth Walkthrough

This walkthrough provides a short overview of the DevSynth workflow.
For additional details, see the [Quick Start Guide](quick_start_guide.md).

## 1. Initialize a Project

Create a new project directory named `demo`:

```bash
# Create and enter the project directory
devsynth init --path demo
cd demo
```

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
devsynth spec

# Generate tests
devsynth test

# Generate implementation code
devsynth code
```

## 4. Run the Tests

Execute the generated tests with either `pytest` or the DevSynth runner:

```bash
# Using pytest
pytest

# Or using DevSynth
devsynth run
```

If the tests pass, your generated code is working. If you encounter issues, see the [Troubleshooting Guide](troubleshooting.md).

---

For a complete walkthrough with more context, consult the [Quick Start Guide](quick_start_guide.md).
