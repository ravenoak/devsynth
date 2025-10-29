---

author: DevSynth Team
date: '2025-07-08'
last_reviewed: "2025-08-02"
status: published
tags:
- getting-started
- quick-start
- tutorial
title: DevSynth Quick Start Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Getting Started</a> &gt; DevSynth Quick Start Guide
</div>

# DevSynth Quick Start Guide

This guide provides a step-by-step tutorial to help you get started with DevSynth quickly.

> **Note**: This guide uses domain-specific terminology. For definitions of unfamiliar terms, please refer to the [DevSynth Glossary](../glossary.md).

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.12 or higher
- Poetry (for dependency management)

## Installation

### Install from PyPI

```bash
poetry add devsynth
```

### Install with pipx *(end-user install)*

```bash
pipx install devsynth
```

### Install from Source (recommended for development)

```bash

# Clone the repository

git clone https://github.com/ravenoak/devsynth.git
cd devsynth

# Install with Poetry

poetry install --with dev,docs
poetry sync --all-extras --all-groups

# Older instructions may use `pip install -e '.[dev]'`. Prefer the Poetry

# workflow above for a fully managed virtual environment. Pip commands are only

# required for installing from PyPI or via `pipx`.

# Activate the virtual environment

poetry shell
```

## Run with Docker Compose

To start DevSynth and its dependencies using Docker Compose:

```bash
docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d
```

This launches the DevSynth API, ChromaDB, and the optional Prometheus and Grafana stack.

### Launch the WebUI

After installation you can optionally use the NiceGUI-based WebUI instead of the CLI. Start it with:

```bash
devsynth webui
```

The interface mirrors the CLI workflows and provides pages for onboarding, requirements, analysis, synthesis, and configuration.
It runs at http://localhost:8080 by default.

## Using the Dev Container

DevSynth ships with a `.devcontainer` directory that sets up an isolated development environment. You can open the project directly in **VS Code** or **PyCharm Professional** using this configuration.

1. Make sure Docker is running on your machine.
2. In **VS Code**, run **"Dev Containers: Open Folder in Container…"** and select the repository folder.
   In **PyCharm**, use the Remote Development > Docker option and point to `.devcontainer/devcontainer.json`.
3. Wait for the container to build. Dependencies are installed automatically with Poetry.
4. If you need the full stack (API, ChromaDB, and monitoring), run:

```bash
docker compose up
```

This launches all services defined in `docker-compose.yml` and `docker-compose.monitoring.yml` inside the container.

## Creating Your First DevSynth Project

### Step 1: Initialize a New Project

```bash

# Create a new DevSynth project

devsynth init --path ./my-first-project
cd my-first-project
```

This command creates a new project directory and then launches an interactive
wizard when the `--wizard` flag is used. The wizard prompts for the project
root, language, optional goals, and where to store memory. The collected answers
are written to `.devsynth/project.yaml` by default or stored under
`[tool.devsynth]` in `pyproject.toml` if you choose. After initialization you are
asked which optional features to enable. The selected flags are saved in the
configuration file. You
can use the [templates/project.yaml](../../templates/project.yaml) file as a
minimal example configuration.

## Step 2: Define Your Requirements

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
devsynth inspect-config
devsynth validate-manifest
```

## Viewing and Modifying Generated Artifacts

After completing the steps above, your project directory will contain:

- `requirements.md`: Your original requirements
- `specs.md`: Generated specifications
- `tests/`: Directory containing generated tests
- `src/`: Directory containing generated implementation code

You can review and modify any of these files as needed. If you make changes to your requirements, you can re-run the DevSynth commands to update the specifications, tests, and code.

## Use Case: Web API Development

### Step 1: Define API Requirements

Create a file named `api_requirements.md` with the following content:

```markdown

# API Requirements

## Endpoints

- The API shall provide a GET endpoint for retrieving user information
- The API shall provide a POST endpoint for creating new users
- The API shall provide a PUT endpoint for updating user information
- The API shall provide a DELETE endpoint for removing users

## Authentication

- The API shall require JWT authentication for all endpoints
- The API shall provide a login endpoint that returns a JWT token
- The API shall validate JWT tokens for expiration and signature

## Data Validation

- The API shall validate all input data against a schema
- The API shall return appropriate error messages for invalid input
- The API shall sanitize input to prevent injection attacks
```

### Step 2: Generate API Specifications and Code

```bash

# Generate specifications

devsynth spec --requirements-file api_requirements.md

# Generate tests and code

devsynth test
devsynth code
```

## Step 3: Run and Test the API

```bash

# Run the API server

devsynth serve

# In another terminal, test the API

curl http://localhost:8000/api/users
```

## Use Case: Data Analysis Tool

### Step 1: Define Data Analysis Requirements

Create a file named `data_analysis_requirements.md` with the following content:

```markdown

# Data Analysis Tool Requirements

## Data Import

- The system shall import data from CSV files
- The system shall import data from Excel files
- The system shall import data from JSON files
- The system shall validate imported data for consistency

## Data Processing

- The system shall calculate basic statistics (mean, median, mode)
- The system shall identify outliers in the data
- The system shall support data filtering based on criteria
- The system shall support data grouping and aggregation

## Data Visualization

- The system shall generate bar charts from data
- The system shall generate line charts from data
- The system shall generate scatter plots from data
- The system shall export visualizations as PNG and PDF
```

### Step 2: Generate Data Analysis Tool

```bash

# Generate specifications

devsynth spec --requirements-file data_analysis_requirements.md

# Generate tests and code

devsynth test
devsynth code
```

## Step 3: Use the Data Analysis Tool

```bash

# Run the data analysis tool

python -m src.main --input data.csv --output analysis_results
```

## Use Case: Automated Testing Framework

### Step 1: Define Testing Framework Requirements

Create a file named `testing_framework_requirements.md` with the following content:

```markdown

# Testing Framework Requirements

## Test Discovery

- The system shall automatically discover test files in a directory
- The system shall support custom test file patterns
- The system shall support inclusion and exclusion filters

## Test Execution

- The system shall execute tests in parallel when possible
- The system shall support test timeouts
- The system shall capture stdout and stderr during test execution
- The system shall support test fixtures and dependencies

## Reporting

- The system shall generate HTML test reports
- The system shall generate XML test reports for CI integration
- The system shall calculate test coverage metrics
- The system shall identify flaky tests based on historical data
```

### Step 2: Generate Testing Framework

```bash

# Generate specifications

devsynth spec --requirements-file testing_framework_requirements.md

# Generate tests and code

devsynth test
devsynth code
```

## Step 3: Use the Testing Framework

```bash

# Run the testing framework

python -m src.main --test-dir ./tests --report-format html
```

## Next Steps

Now that you've created your first DevSynth project, you can:

- Explore more complex requirements
- Customize the development process using configuration options
- Learn about advanced features in the [User Guide](../user_guides/user_guide.md)
- Understand the architecture in the [Architecture Overview](../architecture/overview.md)

## Troubleshooting

If you encounter any issues:

1. Ensure you have the correct Python version (3.12+)
2. Verify that Poetry is installed correctly
3. Check that all dependencies are installed
4. Review the error messages for specific issues

For more detailed information, refer to the [User Guide](../user_guides/user_guide.md) or open an issue on the [GitHub repository](https://github.com/ravenoak/devsynth/issues).

## Related Documents

- [Installation Guide](installation.md) - Detailed installation instructions
- [Basic Usage Guide](basic_usage.md) - Introduction to basic DevSynth usage
- [User Guide](../user_guides/user_guide.md) - Comprehensive guide for users
- [Dear PyGui Guide](../user_guides/dearpygui.md) - Dear PyGui desktop interface
- [Architecture Overview](../architecture/overview.md) - Overview of DevSynth's architecture
