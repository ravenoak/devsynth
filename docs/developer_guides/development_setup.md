---
author: DevSynth Team
date: "2025-08-25"
status: active
---
# Development Setup and Common Workflows

This guide outlines a reproducible developer setup and the most common workflows. It aligns with project guidelines and the stabilization priorities in docs/plan.md.

## Prerequisites
- Python 3.12.x (pyproject pins <3.13,>=3.12)
- Poetry 1.8+
- Optional: pre-commit for local hygiene hooks

## Environment Setup
- Full dev+docs with all extras (recommended):
  - poetry install --with dev,docs --all-extras
  - poetry shell

- Minimal contributor setup (no heavy extras):
  - poetry install --with dev --extras minimal

- Targeted test baseline without GPU/LLM heft:
  - poetry install --with dev --extras "tests retrieval chromadb api"

## Quick Sanity
- Collection only:
  - poetry run pytest --collect-only -q
- Doctor command:
  - poetry run devsynth doctor

## Running Tests (primary entrypoint)
- Fast unit tests:
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel
- With HTML report under test_reports/:
  - poetry run devsynth run-tests --report
- Smoke mode (reduced plugin surface):
  - poetry run devsynth run-tests --smoke --speed=fast

## Speed Marker Discipline
- Exactly one speed marker per test function is required: @pytest.mark.fast | @pytest.mark.medium | @pytest.mark.slow
- Validate markers:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json

## Resource-Gated Tests
- Skip by default unless resources are available; control via env flags.
- Defaults in CI: offline-first and DEVSYNTH_PROVIDER=stub.

## Linting and Style
- Black and isort (Black profile):
  - poetry run black --check .
  - poetry run isort --check-only .
- Flake8, Bandit, Safety:
  - poetry run flake8 src/ tests/
  - poetry run bandit -r src/devsynth -x tests
  - poetry run safety check --full-report

## Typing
- Strict mypy by default with targeted overrides. Run:
  - poetry run mypy src/devsynth

## Pre-commit Hooks
- Install:
  - pre-commit install
- Update hooks periodically:
  - pre-commit autoupdate
- Hooks configured:
  - trailing whitespace and EOF fixers
  - YAML/TOML/JSON checks
  - black, isort, flake8, mypy
  - pyupgrade (targets Python 3.12+)

## Common Workflows
- Format and lint before pushing:
  - poetry run black . && poetry run isort . && poetry run flake8 src/ tests/
- Run unit tests locally:
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel
- Regenerate test marker report:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json

## Notes
- Tests are isolated and offline-first by default. Avoid network calls unless explicitly enabled.
- Platform support: Linux/macOS are primary; on Windows use WSL2 (Ubuntu) and run commands inside the WSL shell. Native Windows shells are not supported for developer scripts.
- Keep docs/tasks.md updated when completing related improvements.
