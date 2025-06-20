---
title: "DevSynth Quick Start Guide"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "getting-started"
  - "quick-start"
  - "tutorial"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-15"
---

# DevSynth Quick Start Guide

This guide provides a step-by-step tutorial to help you get started with DevSynth quickly.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.11 or higher
- Poetry (for dependency management)

## Installation

### Install from PyPI

```bash
pip install devsynth
```
### Install with pipx

```bash
pipx install devsynth
```


### Install from Source

```bash
# Clone the repository
git clone https://github.com/ravenoak/devsynth.git
cd devsynth

# Install with development dependencies
pip install -e '.[dev]'

# Or use Poetry
poetry install
poetry sync --all-extras --all-groups


# Activate the virtual environment
poetry shell
```

### Run with Docker Compose

To start DevSynth and its dependencies using Docker Compose:

```bash
docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d
```

This launches the DevSynth API, ChromaDB, and the optional Prometheus and Grafana stack.

### Launch the WebUI

After installation you can optionally use the Streamlit-based WebUI instead of the CLI. Start it with:

```bash
devsynth webui
```

The interface mirrors the CLI workflows and provides pages for onboarding, requirements, analysis, synthesis, and configuration.

## Creating Your First DevSynth Project

### Step 1: Initialize a New Project

```bash
# Create a new DevSynth project
devsynth init --path ./my-first-project
cd my-first-project
```

This command creates a new project directory and then launches an interactive
wizard. The wizard prompts for the project root, source layout, language, and
any optional goals or constraint file. These answers are written to
`.devsynth/devsynth.yml` by default or stored under `[tool.devsynth]` in
`pyproject.toml` if you choose. After initialization you are asked which optional
features to enable. The selected flags are saved in the configuration file. You
can use the [templates/project.yaml](../../templates/project.yaml) file as a
minimal example configuration.

### Step 2: Define Your Requirements

Create a file named `requirements.md` in your project directory with your project requirements:

```markdown
# Project Requirements

## Calculator Functionality
- The system shall provide addition of two numbers
- The system shall provide subtraction of two numbers
- The system shall provide multiplication of two numbers
- The system shall provide division of two numbers
- The system shall handle division by zero gracefully

## User Interface
- The system shall provide a command-line interface
- The system shall display results with appropriate formatting
```

### Step 3: Generate Specifications

Run the following command to generate detailed specifications based on your requirements:

```bash
devsynth spec --requirements-file requirements.md
```

This will create a `specs.md` file in your project directory with detailed specifications derived from your requirements.

### Step 4: Generate Tests

Next, generate tests based on the specifications:

```bash
devsynth test
```

This command creates test files in the `tests` directory of your project.

### Step 5: Generate Implementation Code

Generate the implementation code that satisfies the tests:

```bash
devsynth code
```

This creates the implementation code in the `src` directory of your project.

### Step 6: Run the Generated Code

Finally, run the generated code to verify it works as expected:

```bash
devsynth run-pipeline
```

### Step 7: Manage Configuration

Keep your project configuration up to date and validate it:

```bash
devsynth analyze-config
devsynth validate-config
```

## Viewing and Modifying Generated Artifacts

After completing the steps above, your project directory will contain:

- `requirements.md`: Your original requirements
- `specs.md`: Generated specifications
- `tests/`: Directory containing generated tests
- `src/`: Directory containing generated implementation code

You can review and modify any of these files as needed. If you make changes to your requirements, you can re-run the DevSynth commands to update the specifications, tests, and code.

## Next Steps

Now that you've created your first DevSynth project, you can:

- Explore more complex requirements
- Customize the development process using configuration options
- Learn about advanced features in the [User Guide](../user_guides/user_guide.md)
- Understand the architecture in the [Architecture Overview](../architecture/overview.md)

## Troubleshooting

If you encounter any issues:

1. Ensure you have the correct Python version (3.11+)
2. Verify that Poetry is installed correctly
3. Check that all dependencies are installed
4. Review the error messages for specific issues

For more detailed information, refer to the [User Guide](../user_guides/user_guide.md) or open an issue on the [GitHub repository](https://github.com/ravenoak/devsynth/issues).

## Related Documents

- [Installation Guide](installation.md) - Detailed installation instructions
- [Basic Usage Guide](basic_usage.md) - Introduction to basic DevSynth usage
- [User Guide](../user_guides/user_guide.md) - Comprehensive guide for users
- [Architecture Overview](../architecture/overview.md) - Overview of DevSynth's architecture
