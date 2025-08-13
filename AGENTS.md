# AGENTS.md

This repository implements agent services under `src/devsynth/` and supporting scripts in `scripts/`. Follow the steps below when contributing.

DevSynth values clarity, collaboration, and dependable automation. All work follows a **specification-first BDD workflow** and is subject to [dialectical audits](docs/policies/dialectical_audit.md). Begin each task with the Socratic checklist:

- What is the problem?
- What proofs confirm the solution?

See [`docs/policies/documentation_policies.md`](docs/policies/documentation_policies.md) for comprehensive documentation standards.

## Environment Expectations

- Run the environment provisioning script before beginning any development to provision the environment. Always refer to it generically as **the environment provisioning script** and update it according to best practices; do not mention its filename or path elsewhere in the repository.
- Run **all** commands through `poetry run` to ensure the correct virtual environment is used.
- Pytest markers such as `memory_intensive` gate resource-heavy tests; skip them unless specifically required.
- Optional extras in `pyproject.toml` are automatically cached by the environment provisioning script, keeping them synchronized with the project configuration while skipping heavy GPU packages.
- Update this file, your instructions and initial context, as appropriate and according to best practices.
- Documents in `docs/inspirational_docs/` are for inspiration only and must not be directly referenced; use these documents for inspiration.
- Documents in `docs/external_research_papers/` are copies of academic papers and can be referenced using best practices.

## Test Environment

- `tests/conftest.py` provides an autouse `global_test_isolation` fixture that resets
  environment variables, the working directory, and logging configuration to keep
  tests hermetic. Because modules import before this fixture runs, **do not set
  environment variables at import time**—use `monkeypatch.setenv()` or set them
  inside the test body instead.
- Common environment variables:
  - `DEVSYNTH_ACCESS_TOKEN` – token used for authenticated API calls. Set it in
    a test with `monkeypatch` or export it before running the suite.
  - `DEVSYNTH_NO_FILE_LOGGING` – disabling file logging when set to `1` (the
    default under `global_test_isolation`). Override to `0` to allow log files.
  - `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` – gates tests that rely on optional
    resources such as `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE`. Set to `true` or
    `false` to force-enable or disable a resource.
- When optional services like LM Studio are unavailable, guard imports with
  `pytest.importorskip("lmstudio")` and use mocks or HTTP stubs to simulate
  responses so unit tests remain deterministic.
- `tests/conftest_extensions.py` categorizes tests with `fast`, `medium`, and
  `slow` markers. Each test must include exactly one of these speed markers.
  Use the `--speed` option to select a category, e.g. `poetry run pytest --speed=fast -m fast`.
- Combine speed markers with context markers like `memory_intensive` when needed.

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
   poetry run devsynth run-tests --speed=fast
   ```

   Use `--speed=<cat>` to select the desired runtime category.

4. Verify dependencies offline:

   ```bash
   PIP_NO_INDEX=1 poetry run pip check
   ```

Before implementing changes, draft a specification and a failing test guided by the Socratic checklist:

- What is the problem?
- What proofs confirm the solution?

## Specification-First Workflow

- Always draft a specification for any new functionality in `docs/specifications/` (see the [specification index](docs/specifications/index.md)) **before** implementation.
- Always add a failing BDD feature under `tests/behavior/features/` prior to writing code.
- Use this Socratic checklist when preparing specs and tests:
  - What is the problem?
  - What proofs confirm the solution?

## Pre-PR Checks

Before opening a pull request, run:

```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<cat>
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
```

## Release Preparation

The `0.1.0-alpha.1` release process is documented in [docs/release/0.1.0-alpha.1.md](docs/release/0.1.0-alpha.1.md). Follow these steps:

1. Run `poetry run task release:prep` to generate release artifacts.
   - **Key Questions**
     - What files or version bumps did the command produce?
     - Did the command complete without errors?
2. Run `poetry run python scripts/dialectical_audit.py` to produce a dialectical audit log. See the [Dialectical Audit Policy](docs/policies/dialectical_audit.md).
   - **Key Questions**
     - What inconsistencies or open questions did the audit uncover?
     - Are these items resolved or tracked?
3. Conduct a dialectical review with at least one other contributor.
   - **Key Questions**
     - What assumptions underlie the release changes?
     - What counterarguments or alternative perspectives have been considered?
4. Tag the release with `git tag -a <version>` and push the tag.
   - **Key Questions**
     - Does the tag follow semantic versioning?
     - Have the tag and release notes been pushed to the remote?

## Automation

- Most DevSynth CLI commands accept `--non-interactive` and `--defaults` to bypass prompts.

## Further Reading

See `docs/` and `CONTRIBUTING.md` for detailed policies, architecture, and contribution guidelines.
