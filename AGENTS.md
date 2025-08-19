# AGENTS.md

This repository implements agent services under `src/devsynth/` and supporting scripts in `scripts/`. Follow the steps below when contributing.

DevSynth values clarity, collaboration, and dependable automation. All work follows a **specification-first BDD workflow** and adheres to the [Dialectical Audit Policy](docs/policies/dialectical_audit.md). Begin each task with the Socratic checklist:

- What is the problem?
- What proofs confirm the solution?

When introducing new features, revisit these questions and follow the specification-first BDD workflow: draft a specification in `docs/specifications/` and a failing BDD feature under `tests/behavior/features/` before implementation.

Directory-specific instructions live in scoped AGENTS guidelines within directories like `src/` and `docs/`.

## Environment

- Ensure Python 3.12 is active per `.python-version`. Verify with:

  ```bash
  python --version
  poetry env info --path
  ```

  If Poetry uses a different interpreter, recreate the virtual environment:

  ```bash
  poetry env use 3.12 && poetry install --with dev --extras tests retrieval chromadb api
  ```

- Run the environment provisioning script before development:

  ```bash
  bash scripts/install_dev.sh
  ```
- It installs pre-commit hooks, caches optional extras from `pyproject.toml`, and runs verification commands to ensure project consistency.
- Run **all** commands through `poetry run` to use the correct virtual environment.
- Install dependencies with development and test extras:

  ```bash
  poetry install --with dev --extras tests retrieval chromadb api
  ```

- Lint changed files before committing:

  ```bash
  poetry run pre-commit run --files <changed>
  ```

- Verify dependencies offline:

  ```bash
  PIP_NO_INDEX=1 poetry run pip check
  ```

- Update this file, your instructions, and initial context as needed.

## Testing

- `tests/conftest.py` provides an autouse `global_test_isolation` fixture that resets environment variables, the working directory, and logging configuration. Because modules import before this fixture runs, **do not set environment variables at import time**—use `monkeypatch.setenv()` or set them inside the test body.
- Common environment variables:
  - `DEVSYNTH_ACCESS_TOKEN` – token used for authenticated API calls. Set it in a test with `monkeypatch` or export it before running the suite.
  - `DEVSYNTH_NO_FILE_LOGGING` – disabling file logging when set to `1` (the default under `global_test_isolation`). Override to `0` to allow log files.
  - `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` – gates tests that rely on optional resources such as `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE`. Set to `true` or `false` to force-enable or disable a resource.
- When optional services like LM Studio are unavailable, guard imports with `pytest.importorskip("lmstudio")` and use mocks or HTTP stubs to simulate responses so unit tests remain deterministic.
- `tests/conftest_extensions.py` categorizes tests with `fast`, `medium`, and `slow` markers. Unmarked tests default to `medium`; include exactly one speed marker and combine with context markers like `memory_intensive` when needed. Run tests with:

  ```bash
  poetry run devsynth run-tests --speed=<cat>
  ```

- Before opening a pull request, run:

  ```bash
  poetry run pre-commit run --files <changed>
  poetry run devsynth run-tests --speed=<cat>
  poetry run python tests/verify_test_organization.py
  poetry run python scripts/verify_test_markers.py
  poetry run python scripts/verify_requirements_traceability.py
  poetry run python scripts/verify_version_sync.py
  ```

- Resolve `dialectical_audit.log` before submitting a PR. Release preparation steps are outlined in `docs/release/0.1.0-alpha.1.md`.

## Issue Tracking

- Use the in-repo issue tracker under `issues/` (see [issues/README.md](issues/README.md)).
- The first line of each ticket must be `# <title>`.
- Create new tickets by copying `issues/TEMPLATE.md` and renaming it using a slug of its title.
- Include `Priority` and `Dependencies` fields along with the standard sections.
- When a ticket is resolved, move its file to `issues/archived/<slug>.md` and leave it immutable. Archived tickets retain the legacy format `# Issue <number>: <title>`.

## Specification-First Workflow

- Always draft a specification for any new functionality in `docs/specifications/` (see the [specification index](docs/specifications/index.md)) **before** implementation.
- Always add a failing BDD feature under `tests/behavior/features/` prior to writing code.
- Use the Socratic checklist above when preparing specs and tests.

## Release

See `docs/release/0.1.0-alpha.1.md` for the full process. Summary:

1. Run `poetry run task release:prep` to build artifacts.
2. Generate and resolve `dialectical_audit.log` (`poetry run python scripts/dialectical_audit.py` or trigger the GitHub workflow`) per the [Dialectical Audit Policy](docs/policies/dialectical_audit.md).
3. Conduct a dialectical review with another contributor.
4. Tag and push the release: `git tag -a <version>`.

## Automation

- Most DevSynth CLI commands accept `--non-interactive` and `--defaults` to bypass prompts.

## Further Reading

See `docs/` and `CONTRIBUTING.md` for detailed policies, architecture, and contribution guidelines.
