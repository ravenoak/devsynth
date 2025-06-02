---
title: "DevSynth Basic Usage Guide"
date: "2024-06-01"
version: "1.0.0"
tags:
  - "getting-started"
  - "basic-usage"
  - "tutorial"
status: "published"
author: "DevSynth Team"
last_reviewed: "2024-06-01"
---

# Basic Usage

This guide provides essential information about the basic usage of DevSynth, including initializing a project, defining requirements, and generating code.

## Overview

DevSynth follows a structured workflow that takes you from requirements to working code. This guide covers the fundamental commands you'll use in a typical DevSynth project.

## Initialize a Project

Start by creating a new DevSynth project:

```bash
# Create a new project directory
devsynth init --path ./my-project

# Navigate to the project directory
cd my-project
```

This command creates a new project directory with the necessary structure for DevSynth to work with.

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
devsynth spec --requirements-file requirements.md

# Generate tests from specifications
devsynth test

# Generate implementation code from tests
devsynth code
```

Each command builds on the output of the previous command, following a test-driven development approach.

## Run the Project

Finally, run the generated code to verify it works as expected:

```bash
# Run the generated code
devsynth run
```

This command executes the generated code and provides feedback on its operation.

## Next Steps

For more detailed information about DevSynth's capabilities and advanced usage scenarios, see the [User Guide](../user_guides/user_guide.md).

## Related Documents

- [Quick Start Guide](quick_start_guide.md) - A step-by-step tutorial for getting started with DevSynth
- [Installation Guide](installation.md) - Detailed installation instructions
- [User Guide](../user_guides/user_guide.md) - Comprehensive guide for users
