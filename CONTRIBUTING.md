---
title: "Contributing to DevSynth"
date: "2025-05-30"
version: "0.1.0"
tags:
  - "devsynth"
  - "contributing"
  - "development"
  - "guidelines"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-04"
---

# Contributing to DevSynth

Thank you for your interest in contributing to DevSynth! This document provides a quick overview of the contribution process. For detailed guidelines, please refer to the [comprehensive contributing guide](docs/developer_guides/contributing.md).

## Quick Start

1. **Fork and clone** the repository
2. **Set up** your development environment with Poetry
3. **Create a branch** for your changes
4. **Write tests** before implementing functionality (TDD/BDD approach)
5. **Implement** your changes following our coding standards
6. **Submit** a pull request with a clear description

## Key Guidelines

- Follow the **test-first development approach** (TDD/BDD)
- Adhere to our [coding standards](docs/developer_guides/code_style.md)
- Update documentation for any changes
- Ensure all tests pass before submitting a pull request

## Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/devsynth.git
cd devsynth

# Install dependencies
poetry install --all-extras --with dev,docs

# Activate virtual environment
poetry shell

# Install pre-commit hooks
pre-commit install

# Run all hooks on the current codebase
pre-commit run --all-files

# Run the alignment check manually
pre-commit run devsynth-align --all-files
```

The `devsynth-align` hook runs `devsynth align --quiet` and will block commits
if alignment issues are detected.

For examples of additional hooks, including link checking and formatting, see [pre-commit hook samples](docs/developer_guides/pre_commit_samples.md).

## Testing

```bash
# Ensure the project is installed in editable mode
poetry install --all-extras --with dev,docs

# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=term-missing
```

## Documentation

Good documentation is essential. Please update relevant documentation for any changes and ensure your code includes proper docstrings.

## Pull Request Process

1. Ensure your fork is up to date with the main repository
2. Run tests and code formatters locally
3. Push your changes and create a pull request using the [pull request template](.github/pull_request_template.md)
4. Respond to review feedback

## Release Process

Maintainers preparing a tagged release should build distributable artifacts and
run a quick smoke test before tagging:

```bash
task release:prep
git tag v0.1.0-alpha.1
git push origin v0.1.0-alpha.1
```

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please be respectful, inclusive, and collaborative.

## Detailed Guidelines

For comprehensive information on contributing to DevSynth, including detailed coding standards, architecture guidelines, and testing requirements, please refer to our [detailed contributing guide](docs/developer_guides/contributing.md).

---

_For questions, please open an issue or reach out to the maintainers._
