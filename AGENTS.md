# AGENTS.md

This repository implements agent services under `src/devsynth/` and supporting scripts in `scripts/`. Follow the steps below when contributing.

## Quick Start

1. Install dependencies:

   ```bash
   poetry install
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

## Automation

- Most CLI commands accept `--non-interactive` or `--defaults` to bypass prompts.
- Ensure new tests follow project conventions:

  ```bash
  poetry run python tests/verify_test_organization.py
  ```

## Further Reading

See `docs/` and `CONTRIBUTING.md` for detailed policies, architecture, and contribution guidelines.
