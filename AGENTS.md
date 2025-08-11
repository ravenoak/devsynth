# AGENTS.md

This repository implements agent services under `src/devsynth/` and supporting scripts in `scripts/`. Follow the steps below when contributing.

DevSynth values clarity, collaboration, and dependable automation. Keep these principles in mind and see [`docs/policies/documentation_policies.md`](docs/policies/documentation_policies.md) for comprehensive documentation standards.

## Environment Expectations

- Run **all** commands through `poetry run` to ensure the correct virtual environment is used.
- Pytest markers such as `memory_intensive` gate resource-heavy tests; skip them unless specifically required.
- `scripts/codex_setup.sh` sets up your environment pior to being handed off to you; update it as appropriate and according to best-practices.
- Update this file, your instructions and initial context, as appropriate and according to best-practices.
- Documents in `docs/inspirational_docs/` are for inspiration only and must not be directly referenced; use these documents for inspiration.
- Documents in `docs/external_research_papers/` are copies of academic papers and can be referenced using best-practices.

## Quick Start

1. Install dependencies with development and test extras:

   ```bash
   poetry install --with dev --extras tests retrieval chromadb api
   ```

2. Lint changed files before committing:

   ```bash
   poetry run pre-commit run --files <changed>
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
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests
poetry run python tests/verify_test_organization.py
```

## Automation

- Most DevSynth CLI commands accept `--non-interactive` and `--defaults` to bypass prompts.

## Further Reading

See `docs/` and `CONTRIBUTING.md` for detailed policies, architecture, and contribution guidelines.
