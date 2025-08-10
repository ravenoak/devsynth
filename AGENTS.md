# AGENTS.md

This repository implements agent services under `src/devsynth/` and supporting scripts in `scripts/`. Follow the steps below when contributing.

DevSynth values clarity, collaboration, and dependable automation. Keep these principles in mind and see [`docs/policies/documentation_policies.md`](docs/policies/documentation_policies.md) for comprehensive documentation standards.

## Environment Expectations

- Run **all** commands through `poetry run` to ensure the correct virtual environment is used.
- Pytest markers such as `memory_intensive` gate resource-heavy tests; skip them unless specifically required.

## Quick Start

1. Install dependencies (including test extras):

   ```bash
   poetry install --with dev --extras tests retrieval chromadb api
   ```

2. Lint changed files:

   ```bash
   poetry run pre-commit run --files path/to/file.py [path/to/other.py]
   ```

3. Run tests:

   ```bash
   poetry run pytest -m "not memory_intensive"
   ```

4. Verify dependencies:

   ```bash
   poetry run pip check
   ```

## Pre-PR Checks

Before opening a pull request, run:

```bash
poetry run python scripts/run_all_tests.py
poetry run python tests/verify_test_organization.py
```

## Automation

- Most CLI commands accept `--non-interactive` or `--defaults` to bypass prompts.

## Further Reading

See `docs/` and `CONTRIBUTING.md` for detailed policies, architecture, and contribution guidelines.
