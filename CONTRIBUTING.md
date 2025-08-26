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
4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   pre-commit autoupdate
   ```
5. **Review directory-specific guidelines** before making changes
6. **Draft a specification** in [docs/specifications/](docs/specifications/index.md) and add a failing BDD feature in `tests/behavior/features/` answering the Socratic checklist **before** writing code
7. **Implement** your changes following our coding standards
8. **Run tests** with `poetry run devsynth run-tests --speed=<cat>`
9. **Submit** a pull request with a clear description

## Key Guidelines

- Follow the **test-first development approach** (TDD/BDD)
- For new functionality, include a spec and failing BDD feature before implementation
- Adhere to our [coding standards](docs/developer_guides/code_style.md)
- Update documentation for any changes
- Ensure all tests pass before submitting a pull request
- Marker discipline: exactly one of `@pytest.mark.fast`, `@pytest.mark.medium`, or `@pytest.mark.slow` per test function. Validate with `scripts/verify_test_markers.py --changed`.
- Resource flags: keep external resources disabled by default; explicitly opt in via `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE`.
- Property tests: opt-in via `DEVSYNTH_PROPERTY_TESTING=true` and apply `@pytest.mark.property` plus a speed marker.

## Specification and BDD Features

- Draft specifications in [`docs/specifications/`](docs/specifications/index.md) answering the Socratic checklist before coding.
- Capture expected behaviour with a failing BDD feature in `tests/behavior/features/` to drive implementation.
- Keep specs and features updated alongside code to maintain traceability.
- Link specifications to the code and tests they cover and run `poetry run python scripts/verify_requirements_traceability.py`.

## Socratic Checklist

When drafting specifications and tests, confirm:

- What is the problem?
- What proofs confirm the solution?

Include a brief dialectical note (thesis → antithesis → synthesis) in your PR description when making significant changes, and record details in docs/rationales/test_fixes.md if the change affects tests or stability.

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

# Keep hooks up-to-date
pre-commit autoupdate

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
poetry install --with dev --extras "tests retrieval chromadb api"

# Preferred: run tests by speed via the CLI wrapper (ensures correct env/plugins)
poetry run devsynth run-tests --speed=fast

# Smoke mode (disables third‑party plugins; fastest sanity path)
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# Generate an HTML report under test_reports/
poetry run devsynth run-tests --report

# Run with coverage (direct pytest for targeted workflows)
poetry run pytest --cov=src --cov-report=term-missing
```

### Marker discipline (mandatory)
- Exactly one speed marker per test function: `@pytest.mark.fast | @pytest.mark.medium | @pytest.mark.slow`.
- Do not use module‑level `pytestmark` for speed categories.
- Validate before committing:
  ```bash
  poetry run python scripts/verify_test_markers.py --changed
  poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
  ```

### Property tests (opt‑in)
- Disabled by default. Enable explicitly:
  ```bash
  export DEVSYNTH_PROPERTY_TESTING=true
  poetry run pytest tests/property/
  ```
- Remember to also add `@pytest.mark.property` plus exactly one speed marker to each property test.

### Resource flags and extras
- Resource‑gated tests are skipped by default unless enabled via env flags. Common flags:
  - `DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=true`
  - `DEVSYNTH_RESOURCE_CLI_AVAILABLE=true`
  - `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false` (default; set true to opt‑in)
  - Backends: `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` for CHROMADB/DUCKDB/FAISS/KUZU/LMDB/RDFLIB/TINYDB
- Enable locally by installing the matching extra and exporting the flag, e.g.:
  ```bash
  poetry add tinydb --group dev
  export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
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

## Pre-commit maintenance and troubleshooting

Common hook failures and resolutions:
- Formatting (black/isort): run `poetry run black . && poetry run isort .` and re-commit.
- Flake8 lint: fix reported issues or run `poetry run flake8 src/ tests/` to reproduce locally.
- Mypy: run `poetry run mypy src/devsynth` and address type errors; for unavoidable relaxations, add TODO and timeframe to restore strictness.
- Conventional commits: adjust commit message to the format `type(scope): message` or amend with `git commit --amend`.
- Detect-secrets: rotate/remove secret and re-generate if false positive; add to `.secrets.baseline` only after review.

If hooks seem outdated or broken after a rebase, run `pre-commit autoupdate` and re-install with `pre-commit install --hook-type commit-msg`.

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
4. Link the PR to its corresponding issue(s)/ticket(s) using GitHub's "Linked issues" panel (required)
5. Respond to review feedback

## Ticket Governance (issues/)

Maintain ticket hygiene to keep the roadmap accurate and execution predictable:

- Ownership
  - Assign an owner (single responsible engineer) and optional co-owner(s).
  - Add a clear reviewer or review group.
- Labels
  - Type: type/bug, type/feat, type/docs, type/test, type/chore.
  - Priority: P0 (urgent) · P1 (soon) · P2 (normal) · P3 (nice-to-have).
  - Status: status/triage, status/in-progress, status/review, status/blocked, status/done.
  - Area/Component: area/cli, area/testing, area/providers, area/docs, etc.
- Acceptance criteria
  - Define concrete, testable outcomes (what “done” looks like). Link to tests or add new ones.
  - Reference requirement IDs where applicable (e.g., "ReqID: FR-09").
- Socratic and Dialectical notes
  - Add brief notes capturing assumptions and alternatives: thesis → antithesis → synthesis.
  - For significant test changes, also record details in docs/rationales/test_fixes.md.
- Linkage
  - Cross-link related tickets and PRs. PRs MUST reference their tickets and use GitHub’s Linked issues.
  - When addressing items from docs/tasks.md, reference the item number(s) in the PR description.
- Lifecycle
  - During triage, validate scope, owners, labels, and acceptance criteria.
  - Move to status/in-progress when work starts; to status/review on PR open; to status/done when merged.
  - Close or archive stale tickets (issues/archived) with a brief reason.

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
