---
author: DevSynth Team
date: '2025-06-01'
last_reviewed: "2025-07-10"
status: published
tags:

- development
- setup
- onboarding
- guide
- getting-started

title: DevSynth Development Setup and Onboarding Guide
version: 0.1.0---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Development Setup and Onboarding Guide
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Development Setup and Onboarding Guide
</div>

# DevSynth Development Setup and Onboarding Guide

Welcome to the DevSynth project! This comprehensive guide will help you set up your development environment and get familiar with the project's structure, workflows, and key concepts.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Development Environment Setup](#development-environment-setup)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Running Tests](#running-tests)
7. [Common Development Tasks](#common-development-tasks)
8. [Communication and Getting Help](#communication-and-getting-help)
9. [Next Steps](#next-steps)


## Project Overview

DevSynth is an agentic software engineering platform that uses Large Language Models (LLMs), memory systems, and dialectical reasoning to automate software development. The project follows a hexagonal architecture with clear separation of concerns and emphasizes traceability, extensibility, and resilience.

### Key Features

- **EDRR Framework**: Evaluate-Design-Refine-Reflect cycle for iterative development
- **Multi-Agent Collaboration**: WSDE (WSDE) model for non-hierarchical Agent collaboration
- **Advanced Memory Architecture**: Multi-backend system supporting vector, graph, and document storage
- **Self-Analysis Capabilities**: Tools for analyzing and understanding codebases
- **Test-Driven Development**: Comprehensive testing infrastructure with BDD/TDD approach


For a more detailed overview of the architecture, see the [Architecture Overview](../architecture/overview.md).

## Prerequisites

Before setting up the development environment, ensure you have the following installed:

- **Python 3.12++**: Required for running the project
- **Poetry**: Used for dependency management
- **Git**: Required for version control
- **Docker** (optional): For containerized development and testing


## Development Environment Setup

Follow the steps below to configure a working development environment. This process installs dependencies and sets up local tooling without relying on any automated setup scripts.

### 1. Clone the Repository

```bash
git clone https://github.com/ravenoak/devsynth.git
cd devsynth
```

### 2. Install Dependencies

```bash
# Install development dependencies with the minimal runtime extras
poetry install --with dev --extras minimal

# Enable GPU support if needed
# poetry install --extras gpu

# Activate the virtual environment
poetry shell
```

These commands install all required packages and activate the Poetry-managed
virtual environment. Once complete, proceed to configure environment variables.

## 3. Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```text

# Provider Configuration

DEVSYNTH_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Optional: For local LLM usage

# LM_STUDIO_ENDPOINT=http://127.0.0.1:1234

# For web searches (optional)

SERPER_API_KEY=your_serper_api_key
```

## 4. Install Pre-commit Hooks

```bash
pre-commit install
```

The pre-commit hooks will run automatically when you commit changes. They include:

- Code formatting (Black, isort)
- Linting (flake8)
- Type checking (mypy)
- Test-first development check


### 5. Verify Setup

Ensure your setup is working correctly by running the tests:

```bash
poetry run pytest
```
Running plain `pytest` outside of Poetry may fail because required plugins are installed only in the Poetry-managed virtual environment.


### Configuration Version Locking

DevSynth locks the configuration format to a specific version. The `version` key
in `.devsynth/project.yaml` (or `[tool.devsynth]` in `pyproject.toml`) must
match the version expected by the current DevSynth release. When `load_config`
reads a file with a mismatched version, it logs a warning so you can regenerate
the configuration with `devsynth init`.

## Project Structure

DevSynth follows a hexagonal architecture pattern with the following key directories:

- `src/devsynth/domain/`: Core domain models and interfaces
  - `models/`: Domain entities and value objects
  - `interfaces/`: Abstract interfaces defining domain behavior

- `src/devsynth/application/`: Application logic and use cases
  - `agents/`: Agent implementations
  - `EDRR/`: EDRR implementation
  - `memory/`: Memory system implementation
  - `prompts/`: Prompt templates and management
  - `utils/`: Utility functions and helpers

- `src/devsynth/adapters/`: External adapters (CLI, LLM, etc.)
  - `cli/`: Command-line interface
  - `llm/`: Provider adapters
  - `memory/`: Memory storage adapters
  - `orchestration/`: Agent orchestration adapters

- `src/devsynth/ports/`: Interface definitions for adapters

- `docs/`: Project documentation
  - `getting_started/`: Guides for new users
  - `user_guides/`: End-user documentation
  - `developer_guides/`: Documentation for contributors
  - `architecture/`: System design documentation
  - `specifications/`: Project specifications

- `tests/`: Test suite
  - `unit/`: Unit tests
  - `integration/`: Integration tests
  - `behavior/`: Behavior-driven tests


## Development Workflow

### Branching Strategy

1. Create a new branch for your feature or bugfix:

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-description
   ```

2. Make your changes, following the [Code Style Guide](code_style.md)

3. Write tests for your changes following the [Testing Guide](testing.md)

4. Commit your changes with descriptive commit messages:

   ```bash
   git commit -m "feat: Add new capability to X component"
   # or
   git commit -m "fix: Resolve issue with Y functionality"
   ```

5. Push your branch to GitHub:

   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request on GitHub


### Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Request review from at least one team member
4. Address any feedback from reviewers
5. Once approved, your changes will be merged


For more details, see the [Contributing Guide](contributing.md).

## Running Tests

DevSynth uses pytest for unit testing and pytest-bdd for behavior-driven tests.
Always invoke the test runner with `poetry run pytest` so that plugins from the
Poetry environment are available. The easiest way to guarantee all test plugins
are present is to install DevSynth with the development dependencies and every
optional extra:

```bash
poetry install --with dev --all-extras
```

If you prefer to enable groups individually, run:

```bash
poetry install --all-extras --all-groups
```

The unit tests run in a hermetic environment managed by the test suite.  All
ingestion and WSDE tests run by default without needing to set additional
environment variables.

### Troubleshooting Missing Extras

If `poetry run pytest` fails with `ModuleNotFoundError` for packages such as
`pytest_bdd`, verify that all extras were installed:

```bash
poetry install --with dev --all-extras
```

Running this command ensures that the test suite has access to every optional
dependency.

### Running Unit Tests

```bash

# Run all unit tests

poetry run pytest tests/unit/

# Run a specific test file

poetry run pytest tests/unit/test_workflow.py

# Run tests with verbose output

poetry run pytest tests/unit/ -v
```

## Running Behavior Tests

```bash

# Run all behavior tests

poetry run pytest tests/behavior/

# Run a specific behavior test

poetry run pytest tests/behavior/test_simple_example_steps.py
```

## Common Development Tasks

### Adding a New Dependency

```bash

# Add a production dependency

poetry add package-name

# Add a development dependency

poetry add --dev package-name
```

## Running the CLI

```bash

# Activate the virtual environment if not already active

poetry shell

# Run the CLI

python -m devsynth.cli command [options]
```

## Generating Documentation

```bash

# Build the documentation

mkdocs build

# Serve the documentation locally

mkdocs serve
```

## Communication and Getting Help

- **Team Meetings**: Weekly sync meetings on Thursdays at 10:00 AM PST
- **Chat Channels**: Join our Discord server for real-time communication
- **Issue Tracker**: Use GitHub Issues for bug reports and feature requests


### Key Contacts

- **Project Lead**: [Name] - [Email]
- **Technical Lead**: [Name] - [Email]
- **Documentation Lead**: [Name] - [Email]


## Next Steps

1. Familiarize yourself with the [Architecture Overview](../architecture/overview.md)
2. Read the [Contributing Guide](contributing.md) for detailed contribution guidelines
3. Check out the [Roadmap](../roadmap/development_plan.md) to see what's coming next
4. Pick an issue from the issue tracker labeled "good first issue"


---

*This document is a living guide and will be updated as the project evolves.*
## Implementation Status

.
