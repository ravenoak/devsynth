---
title: "Contributing to DevSynth"
date: "2025-05-30"
version: "0.1.0-alpha.1"
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
2. **Provision** your development environment:

   ```bash
   bash scripts/install_dev.sh
   ```
3. **Create a branch** for your changes
4. **Review directory-specific guidelines** before making changes
5. **Draft a specification** in [docs/specifications/](docs/specifications/index.md) and add a failing BDD feature in `tests/behavior/features/` answering the Socratic checklist **before** writing code
6. **Implement** your changes following our coding standards
7. **Run tests** with `poetry run devsynth run-tests --speed=<cat>`
8. **Submit** a pull request with a clear description

## Key Guidelines

- Follow the **test-first development approach** (TDD/BDD)
- For new functionality, include a spec and failing BDD feature before implementation
- Adhere to our [coding standards](docs/developer_guides/code_style.md)
- Update documentation for any changes
- Ensure all tests pass before submitting a pull request
- Mark every test with exactly one of `@pytest.mark.fast`, `@pytest.mark.medium`, or `@pytest.mark.slow`; gate high-memory tests with `@pytest.mark.memory_intensive`.

## Specification and BDD Features

- Draft specifications in [`docs/specifications/`](docs/specifications/index.md) answering the Socratic checklist before coding.
- Capture expected behaviour with a failing BDD feature in `tests/behavior/features/` to drive implementation.
- Keep specs and features updated alongside code to maintain traceability.
- Link specifications to the code and tests they cover and run `poetry run python scripts/verify_requirements_traceability.py`.

## Socratic Checklist

When drafting specifications and tests, confirm:

- What is the problem?
- What proofs confirm the solution?

## Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/devsynth.git
cd devsynth

# Install dependencies
poetry install --all-extras --with dev,docs

# Activate virtual environment
poetry shell

# Install pre-commit hooks (includes a Conventional Commits linter)
pre-commit install
pre-commit install --hook-type commit-msg

# Run all hooks on the current codebase
pre-commit run --all-files

# Run the alignment check manually
pre-commit run devsynth-align --all-files

# Run a secrets scan (no baseline required for contributors)
pre-commit run detect-secrets --all-files
```

The `devsynth-align` hook runs `devsynth align --quiet` and will block commits
if alignment issues are detected.

For examples of additional hooks, including link checking and formatting, see [pre-commit hook samples](docs/developer_guides/pre_commit_samples.md).

## Testing

```bash
# Ensure the project is installed in editable mode
poetry install --all-extras --with dev,docs

# Preferred: run tests by speed
poetry run devsynth run-tests --speed=all

# Run only fast tests
poetry run devsynth run-tests --speed=fast

# Run with coverage
poetry run pytest --cov=src --cov-report=term-missing
```

### Optional extras: how to install and run focused tests

DevSynth supports optional feature sets via Poetry extras. Below are common extras and example commands to install and run their focused tests. These should be run locally; CI defaults avoid network, GUI, and heavy backends.

Install patterns:

```bash
# Minimal contributor setup (fastest):
poetry install --with dev --extras minimal

# Target a specific extra:
poetry install --with dev --extras memory
poetry install --with dev --extras llm
poetry install --with dev --extras retrieval
poetry install --with dev --extras chromadb
poetry install --with dev --extras api
poetry install --with dev --extras webui
poetry install --with dev --extras gui
poetry install --with dev --extras offline

# Full matrix for local verification:
poetry install --all-extras --all-groups
```

Running tests per extra (examples):

```bash
# Memory backends (skips missing backends gracefully)
poetry run pytest tests/integration/memory -m "not slow and not no_network"

# LLM provider system (uses stubs; no real network)
DEVSYNTH_PROVIDER=openai \
poetry run pytest tests/unit/application/test_provider_selection.py -m no_network

# API server (no real ports; uses TestClient)
poetry install --with dev --extras api
poetry run pytest tests/integration/api -m no_network

# WebUI (import smoke only; no side effects)
poetry install --with dev --extras webui
poetry run pytest tests/integration/webui -m no_network

# GUI (Dear PyGui) – skipped by default in CI
poetry install --with dev --extras gui
poetry run pytest -m gui -k mvuu --maxfail=1 --disable-warnings
```

Linting and formatting:

```bash
# Format
poetry run black .
poetry run isort .

# Lint
poetry run flake8

# Optional static typing (recommended for changed modules)
poetry run mypy src tests --config-file pyproject.toml
```

Notes:
- Default tests should not require real API keys; providers default to safe stubs.
- Use markers fast/medium/slow/gui/no_network consistently; register new markers in pytest.ini.
- Prefer deterministic seeds and stubbed I/O for CI stability.

### Benchmarks (optional)

Benchmarks are disabled by default. To run the performance benchmark for the in-memory search path, enable the environment flag and load the pytest-benchmark plugin explicitly:

```bash
DEVSYNTH_ENABLE_BENCHMARKS=true \
pytest -p benchmark tests/performance/test_memory_benchmark.py -q
```

## Documentation

Good documentation is essential. Please update relevant documentation for any changes and ensure your code includes proper docstrings.

## Conventional Commits

We enforce [Conventional Commits](https://www.conventionalcommits.org/) via a commit-msg hook. Valid examples:

- feat(cli): add --offline mode for providers
- fix(memory): handle TinyDB TypeError during insert
- docs(readme): clarify installation steps

To enable locally:

```bash
pre-commit install --hook-type commit-msg
```

The hook allows Merge commits and local WIP: prefixes.

## Pre-PR Checks

Before opening a pull request, run:

```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<cat>
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
poetry run python scripts/dialectical_audit.py
```

The CI pipeline runs the same dialectical audit and fails if any questions remain unresolved. The generated `dialectical_audit.log` is uploaded as a workflow artifact for review.

## Pull Request Process

1. Ensure your fork is up to date with the main repository
2. Run tests and code formatters locally
3. Push your changes and create a pull request using the [pull request template](.github/pull_request_template.md)
4. Respond to review feedback

## Release Process

Maintainers preparing a tagged release should build distributable artifacts, run a dialectical audit (see the [Dialectical Audit Policy](docs/policies/dialectical_audit.md)), and run a quick smoke test before tagging:

```bash
poetry run task release:prep
poetry run python scripts/dialectical_audit.py
git tag v0.1.0-alpha.1
git push origin v0.1.0-alpha.1
```

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please be respectful, inclusive, and collaborative.

## Detailed Guidelines

For comprehensive information on contributing to DevSynth, including detailed coding standards, architecture guidelines, and testing requirements, please refer to our [detailed contributing guide](docs/developer_guides/contributing.md).

---

_For questions, please open an issue or reach out to the maintainers._
