---

author: DevSynth Team
date: '2025-06-01'
last_reviewed: "2025-08-22"
status: published
tags:

- testing
- development
- best practices
- quality assurance

title: DevSynth Testing Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Testing Guide
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Testing Guide
</div>

# DevSynth Testing Guide

## Executive Summary

This guide documents the testing standards, practices, and infrastructure for the DevSynth project. It covers the project's testing philosophy, directory structure, test types (BDD, unit, integration), test isolation practices, and guidelines for writing and running tests. It serves as the definitive reference for both human contributors and agentic LLMs working on the project's test suite.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Directory Structure](#test-directory-structure)
- [Test Types](#test-types)
- [Test Isolation & Cleanliness](#test-isolation--cleanliness)
- [Provider System Testing](#provider-system-testing)
- [ChromaDB Memory Store Testing](#ChromaDB-memory-store-testing)
- [Writing New Tests](#writing-new-tests)
- [Running Tests](#running-tests)
- [Requirements Traceability](#requirements-traceability)
- [Continuous Integration](#continuous-integration)
- [Test Coverage](#test-coverage)


## Testing Philosophy

DevSynth follows a comprehensive testing approach that combines multiple testing strategies:

- **Behavior-Driven Development (BDD)**: Using Gherkin syntax to define features and scenarios that validate system behavior from a user perspective.
- **Unit Testing**: Testing individual components in isolation to verify their correctness.
- **Integration Testing**: Testing the interaction between multiple components.
- **Property-Based Testing**: Using strategies like hypothesis testing to verify properties of functions across a range of inputs.


Our testing philosophy emphasizes:

1. **Test Isolation**: Tests should not interfere with each other and should run independently.
2. **Test Cleanliness**: Tests should clean up after themselves and not leave artifacts in the workspace.
3. **Test Coverage**: Critical components should have comprehensive test coverage.
4. **Test Readability**: Tests should be clear and serve as documentation for the code they test.
5. **Provider Abstraction**: Tests should work with either OpenAI or LM Studio through our provider abstraction layer.


## Test Directory Structure

```text
tests/
├── conftest.py              # Global test fixtures and configuration
├── README.md                # Testing overview and instructions
├── behavior/                # Behavior-driven (BDD) tests
│   ├── conftest.py          # BDD-specific test fixtures
│   ├── steps/               # Step definitions for BDD scenarios
│   ├── *.feature            # Feature files in Gherkin syntax
│   └── test_*.py            # Test implementations for features
├── integration/             # Integration tests
│   └── test_*.py            # Integration test implementations
└── unit/                    # Unit tests
    └── test_*.py            # Unit test implementations
```

## Test Types

### Behavior-Driven Tests

Behavior-driven tests use Gherkin syntax (Feature/Scenario/Given/When/Then) to define system behaviors. These tests ensure the system works correctly from a user perspective.

Example feature file (`tests/behavior/chromadb_integration.feature`):

```gherkin
Feature: ChromaDB Integration
  As a developer
  I want to use ChromaDB as a memory store
  So that I can leverage vector database capabilities for semantic search

  Scenario: Initialize ChromaDB memory store
    Given the DevSynth CLI is installed
    When I configure the memory store type as "ChromaDB"
    Then a ChromaDB memory store should be initialized
```

BDD tests are implemented in Python files that use the `pytest-bdd` framework to connect Gherkin steps to Python functions.

### Unit Tests

Unit tests verify the correctness of individual components in isolation. They typically mock external dependencies to focus on the component under test.

### Integration Tests

Integration tests verify that multiple components work together correctly. These tests use real (or realistic) implementations of dependencies instead of mocks.

## Test Isolation & Cleanliness

DevSynth tests are designed to be isolated and clean:

- All tests use temporary directories for artifact storage (e.g., `.devsynth` directories, logs).
- Environment variables are patched during tests to prevent pollution of the real environment.
- Tests clean up after themselves, even if they fail.


The main test fixtures for isolation and cleanliness are:

- `tmp_project_dir`: Creates a temporary directory for test artifacts.
- `patch_env_and_cleanup`: Patches environment variables and ensures cleanup.


Example of test isolation (from `tests/behavior/conftest.py`):

```python
@pytest.fixture(autouse=True)
def patch_env_and_cleanup(tmp_project_dir):
    """
    Patch environment variables for LLM providers and ensure all logs/artifacts
    are isolated and cleaned up.
    """
    # Save old environment and set test environment
    old_env = dict(os.environ)
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["LM_STUDIO_ENDPOINT"] = "http://127.0.0.1:1234"
    os.environ["DEVSYNTH_PROJECT_DIR"] = tmp_project_dir

    # Redirect logs to temp dir
    logs_dir = os.path.join(tmp_project_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    old_cwd = os.getcwd()
    os.chdir(tmp_project_dir)

    yield

    # Cleanup: restore env and cwd, remove logs
    os.environ.clear()
    os.environ.update(old_env)
    os.chdir(old_cwd)

    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)

    # Remove any stray .devsynth or logs in cwd
    for artifact in [".devsynth", "logs"]:
        path = os.path.join(old_cwd, artifact)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
```

## Provider System Testing

DevSynth tests the provider system (OpenAI, LM Studio) with a combination of unit tests and integration tests:

- **Unit Tests**: Mock the provider APIs to test the provider system's logic.
- **Integration Tests**: Optionally connect to real LLM services to test actual API integration.


The provider system tests validate:

1. Provider selection logic (choosing between OpenAI and LM Studio)
2. Fallback mechanisms (trying alternative providers if one fails)
3. Environment variable configuration
4. Error handling and retries

LM Studio provider tests are skipped unless the `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE`
environment variable is set to a truthy value.

Test fixtures for provider system testing include:

- `llm_provider`: Returns a configured provider instance.
- `llm_complete`: Provides a function to generate LLM completions.


Example of provider system testing fixtures (from `tests/behavior/conftest.py`):

```python
@pytest.fixture
def llm_provider():
    """
    Get a provider for LLM completion that works with either OpenAI or LM Studio.
    """
    provider = get_provider(fallback=True)
    return provider

@pytest.fixture
def llm_complete():
    """
    Fixture providing a function to get completions from the LLM.
    """
    def _complete(prompt, system_prompt=None, temperature=0.7, max_tokens=2000):
        return complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            fallback=True  # Enable fallback to try all available providers
        )

    return _complete
```

## ChromaDB Memory Store Testing

The ChromaDB memory store is tested with both standard and enhanced features:

- **Basic Integration**: Testing store, retrieve, and search operations.
- **Provider Integration**: Testing ChromaDB with provider-based embeddings.
- **Advanced Features**: Testing caching, versioning, and optimized embedding storage.


The ChromaDB tests use fixtures for isolation and provider integration:

- `temp_chromadb_path`: Creates a temporary ChromaDB data directory.
- `memory_store`: Creates a ChromaDB memory store configured to use the provider system.
- `memory_port`: Creates a memory port with the ChromaDB memory store.


## Writing New Tests

### Guidelines for New Tests

1. **Isolation**: Tests should be isolated from each other and the local environment.
   - Use temporary directories via the `tmp_project_dir` fixture.
   - Patch environment variables.
   - Clean up all artifacts.

2. **Provider Abstraction**: Tests should work with either OpenAI or LM Studio.
   - Use the `llm_provider` or `llm_complete` fixtures for LLM operations.
   - Ensure tests can run with any provider.

3. **Completeness**: Tests should cover both happy paths and error scenarios.
   - Test error handling and recovery.
   - Validate behaviors with various inputs.

4. **Traceability**: Tests should be traceable to requirements.
   - Name tests to clearly indicate the feature/requirement they validate.
   - Include the requirement ID in the test's docstring using the format `ReqID: <ID>`.


### Adding a New BDD Test

1. Create a new feature file in `tests/behavior/` with Gherkin syntax.
2. Add step definitions in `tests/behavior/steps/` if needed.
3. Create a test runner file in `tests/behavior/test_*.py`.


### Adding a New Integration Test

1. Create a new test file in `tests/integration/test_*.py`.
2. Use provider system and memory store fixtures as needed.
3. Test the interaction between components.


### Adding a New Unit Test

1. Create a new test file in `tests/unit/test_*.py`.
2. Mock external dependencies to isolate the component under test.
3. Test component behavior with various inputs and edge cases.


## Running Tests

### Optional Extras Installation Matrix (local)

Install the project with the extras configuration that matches your local workflow. These presets align with docs/tasks.md task 11 and are suitable for fast local iteration:

- Minimal dev (quickest install; core development only):
  
  ```bash
  poetry install --with dev --extras minimal
  ```

- Tests baseline (sufficient for most tests, including retrieval + API paths referenced by the suite):
  
  ```bash
  poetry install --with dev --extras tests retrieval chromadb api
  ```

- Full feature (non-GPU):
  
  ```bash
  poetry install --with dev,docs --all-extras
  ```

These commands are additive with environment flags described below; prefer these presets to avoid missing optional dependencies when running the suite.

Before executing tests, install DevSynth with its development extras so that all test dependencies are available. Running the **full** suite requires the `minimal`, `retrieval`, `memory`, `llm`, `api`, `webui`, `lmstudio`, and `chromadb` extras. Environment provisioning is handled automatically in Codex environments. For manual setups run:

```bash
poetry install --with dev --extras tests retrieval chromadb api
```


# Verify that pytest can start without import errors

poetry run pytest -q

# pip commands are for installing from PyPI only

Always run tests with `poetry run devsynth run-tests --speed=<cat>`. Use `--maxfail <n>` to exit after a set number of failures. If `pytest` reports missing packages, run `poetry install` to restore them.

The `devsynth run-tests` command disables optional provider tests by default so
missing services won't stall the suite. It sets
`DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false` unless you override it, so LM
Studio tests are skipped unless explicitly enabled:

```bash
poetry run devsynth run-tests --speed=fast  # LM Studio tests skipped

export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true  # opt in to LM Studio tests
poetry run devsynth run-tests --speed=fast
```

When a speed marker matches no tests the command still succeeds and reports
"no tests ran", avoiding `pytest-xdist` assertion errors during parallel
execution.

Run each speed category separately to surface any parallel execution issues:

```bash
poetry run devsynth run-tests --speed=fast
poetry run devsynth run-tests --speed=medium
poetry run devsynth run-tests --speed=slow
```

The test runner automatically disables coverage collection and the `pytest-benchmark` plugin when running in parallel to avoid `pytest-xdist` assertion errors.

Skip resource-heavy tests during routine development by running only fast tests:

```bash
poetry run devsynth run-tests --speed=fast
```

Mark such tests with `@pytest.mark.memory_intensive`. For optional services, use resource markers such as `@pytest.mark.requires_resource("lmstudio")` and set `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=false` to skip them when unavailable.

### Mocking LM Studio and other optional services

When the `lmstudio` package or its server is unavailable, tests should
gracefully skip or mock the dependency. Guard direct imports with
`pytest.importorskip("lmstudio")` to avoid import errors. For unit tests,
stub network interactions using `unittest.mock` or libraries like
`responses` so that code paths remain deterministic. Integration tests that
genuinely exercise LM Studio should be marked with
`@pytest.mark.requires_resource("lmstudio")` and executed only when
`DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true`.

The repository provides a lightweight HTTP stub in
`tests/fixtures/lmstudio_service/` that mimics the LM Studio API. Tests can
use the `lmstudio_service` fixture to patch the `lmstudio` client and route
requests to the stub server, enabling deterministic runs when the real
service is unavailable.

### Quick Reference: Markers and Resource Flags

- Markers:
  - requires_resource(name): mark tests that need an external resource; e.g., @pytest.mark.requires_resource("lmstudio")
  - property: mark Hypothesis-based property tests in tests/property/
- Environment flags (default off for external services in CI/dev):
  - DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE: true/false to opt in/out of LM Studio tests
  - DEVSYNTH_RESOURCE_CLI_AVAILABLE: true/false for CLI-dependent tests
  - DEVSYNTH_RESOURCE_WEBUI_AVAILABLE: true/false for WebUI-dependent tests
  - DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE: true/false to force skip/presence
  - DEVSYNTH_PROPERTY_TESTING: true/false to enable property tests

### Speed Marker Discipline (mandatory)

- Exactly one speed marker per test function is required: @pytest.mark.fast, @pytest.mark.medium, or @pytest.mark.slow.
- Do not rely on module-level pytestmark for speed. Apply speed markers at the function level.
- Validate locally before committing:
  - poetry run python scripts/verify_test_markers.py --changed
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json

Examples:

Correct (function-level speed marker):

```python
import pytest

@pytest.mark.fast
def test_addition_is_commutative():
    assert 1 + 2 == 2 + 1
```

Incorrect (module-level speed marker only; will be flagged):

```python
import pytest

pytestmark = pytest.mark.fast  # Not recognized for speed discipline

def test_addition_is_commutative():
    assert 1 + 2 == 2 + 1
```

Correcting the incorrect example:

```python
import pytest

@pytest.mark.fast
def test_addition_is_commutative():
    assert 1 + 2 == 2 + 1
```

Property tests still require a speed marker in addition to @pytest.mark.property.

### Flakiness mitigation (quick tips)

- Prefer running fast tests locally during iteration: `poetry run devsynth run-tests --speed=fast`.
- Use `--no-parallel` or the `@pytest.mark.isolation` marker for tests that exercise heavy backends (e.g., DuckDB/Kuzu/FAISS) or shared global state.
- Timeouts: smoke mode sets a conservative per-test timeout; for explicit fast-only runs, the CLI defaults to a slightly looser timeout. Override via `DEVSYNTH_TEST_TIMEOUT_SECONDS` if a slow machine triggers spurious timeouts.
- External resources: mark with `@pytest.mark.requires_resource("<name>")` and gate via `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE`. Keep these `false` by default for deterministic CI.
- Network: network is disabled by default in test runs. Stub outbound calls rather than relying on the network.
- Determinism: avoid reliance on wall-clock time and random order dependencies; seed RNGs when used.

If a test remains flaky:
- Capture a minimal repro (inputs, seed, environment flags) in the test’s docstring.
- Add a short comment in the test explaining the mitigation (e.g., isolation, increased timeout) and link to the driving issue.

### Extras Matrix (install what you need)

- minimal: baseline runtime for CLI and core features
  - poetry install --extras minimal
- retrieval: Kuzu + FAISS for vector retrieval
  - poetry install --extras retrieval
- chromadb: ChromaDB store and tokenizer helpers
  - poetry install --extras chromadb
- memory: full memory stack (tinydb, duckdb, lmdb, kuzu, faiss, chromadb, numpy)
  - poetry install --extras memory
- llm: HTTP client/token tools for LLM execution
  - poetry install --extras llm
- api: FastAPI server + Prometheus client
  - poetry install --extras api
- webui: Streamlit-based WebUI
  - poetry install --extras webui
- lmstudio: LM Studio Python client integration
  - poetry install --extras lmstudio
- gui: Dear PyGui desktop interface
  - poetry install --extras gui
- gpu: PyTorch + CUDA libs (Linux x86_64) for local models
  - poetry install --extras gpu
- offline: Transformers-only offline provider support
  - poetry install --extras offline
- tests: convenience group for common test deps when not using groups
  - poetry install --extras tests

Tip: for the full developer environment use poetry install --with dev,docs and consider poetry sync --all-extras --all-groups in CI images.

### Troubleshooting

- Pytest hangs or xdist restarts:
  - Ensure you are using the CLI wrapper: poetry run devsynth run-tests --speed=fast
  - Our pytest_configure caps worker restarts; avoid combining coverage + xdist unless necessary.
- Network calls during tests:
  - Network is disabled by default; use responses or unittest.mock to stub HTTP.
  - Enable specific providers only when needed via DEVSYNTH_RESOURCE_* flags.
- Missing optional dependency (e.g., chromadb):
  - Install the matching extra (poetry install --extras chromadb) or set DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=false to skip.
- Property tests not running:
  - Set DEVSYNTH_PROPERTY_TESTING=true or enable via devsynth config formalVerification.propertyTesting true
- CLI import errors:
  - Always run inside Poetry venv. Use poetry install and poetry run devsynth help to verify entrypoints.

## Running All Tests

```bash

poetry run pytest

```text

### Using `devsynth run-pipeline`

The `devsynth run-pipeline` command wraps `pytest` and can execute the
entire suite or selected groups of tests. It also supports generating HTML
reports with `pytest-html`.

```bash

# Run the full suite (unit tests)
devsynth run-pipeline --target unit-tests

# Run integration tests
devsynth run-pipeline --target integration-tests

# Produce an HTML report in `test_reports/`
devsynth run-pipeline --target unit-tests --report

```text

Combine options (for example, integration tests with a report) as needed.

For utilities that fix flaky tests and categorize runtime, refer to [Test Stabilization Tools](test_stabilization_tools.md).

### Running Specific Test Types

```bash

# Run BDD tests

poetry run pytest tests/behavior/

# Run WebUI onboarding and API stub scenarios

poetry run pytest tests/behavior/test_webui_onboarding_flow.py
poetry run pytest tests/behavior/test_requirements_wizard_navigation.py
poetry run pytest tests/behavior/test_api_stub_usage.py

# Run integration tests

poetry run pytest tests/integration/

# Run unit tests

poetry run pytest tests/unit/

```text

## Running a Specific Test File

```bash

poetry run pytest tests/behavior/test_chromadb_integration.py

```text

### Running Tests with Provider Selection

```bash

# Use OpenAI provider

DEVSYNTH_PROVIDER=openai poetry run pytest

# Use LM Studio provider

DEVSYNTH_PROVIDER=lmstudio poetry run pytest

```text

## Review Workflow

All test changes should undergo a brief review cycle before merging:

1. Format and lint the affected files:

   ```bash
   poetry run pre-commit run --files <file1> [<file2> ...]
   ```text

2. Verify the project test layout:

   ```bash
   poetry run python tests/verify_test_organization.py
   ```text

3. Check marker coverage and collection errors:

   ```bash
   poetry run python scripts/verify_test_markers.py --changed
   ```text

   The script invalidates caches for recently modified tests and reuses
   previous results to keep execution under a minute. A successful run ends
   with a summary similar to:

   ```text
   Verification Summary:
     Total files: 42
     Files with issues: 0
     Skipped files: 0
   ```

   If pytest raises an import or syntax error during collection, the offending
   file is listed under **Collection errors**.

4. Execute the relevant test suites, typically:

   ```bash
   poetry run devsynth run-tests --speed=<cat>
   ```text

5. Request peer review and ensure reviewers confirm meaningful assertions and
   adequate coverage. See
   [cross_functional_review_process.md](cross_functional_review_process.md)
   for expectations.

### Generated Tests

Automatically produced tests require extra scrutiny before they become part of
the suite:

1. Scaffold missing integration coverage with
   `devsynth.testing.generation.scaffold_integration_tests` or
   `write_scaffolded_tests` to create placeholder modules under
   `tests/integration/generated/`.
2. Replace placeholder assertions and remove any `pytest.mark.skip` markers once
   real behavior is verified.
3. Apply edge-case prompt templates from `templates/test_generation/` to ensure
   boundary values and error conditions are exercised.
4. Re-run marker normalization scripts on the new files before executing
   `poetry run pre-commit run --files` and the relevant test suites.

## Enabling Resource-Dependent Tests

Some tests require external services such as LM Studio or the DevSynth CLI. By
default `tests/conftest.py` disables these tests by setting environment
variables like `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE` and
`DEVSYNTH_RESOURCE_CLI_AVAILABLE` to `false`. To run the full suite with all
resources enabled:

```bash
# Install LM Studio optional dependency and start the server
poetry install --extras lmstudio
# (start LM Studio in API mode before running tests)

# Provide an OpenAI API key

export OPENAI_API_KEY=sk-your-key

# Enable LM Studio tests and specify the endpoint

export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
export LM_STUDIO_ENDPOINT=http://localhost:1234

# Ensure CLI commands are available

export DEVSYNTH_RESOURCE_CLI_AVAILABLE=true

# Run the entire test suite

poetry run pytest

```text

Make sure LM Studio is running in API mode on the endpoint above and the
`devsynth` CLI is installed in your path. When these variables are set, the
`poetry run pytest` command will execute all tests, including those normally
skipped when resources are unavailable.

## Enabling Property-Based Tests

Property-based tests live in `tests/property/` and use [Hypothesis](https://hypothesis.readthedocs.io/) to generate inputs.
They are disabled by default. Enable them by setting `formalVerification.propertyTesting` in your configuration or via the
`DEVSYNTH_PROPERTY_TESTING` environment variable:

```bash

devsynth config formalVerification.propertyTesting true
export DEVSYNTH_PROPERTY_TESTING=true  # optional override
poetry run pytest tests/property/

```

When the flag is `false`, tests marked with `@pytest.mark.property` are automatically skipped.

## Requirements Traceability

Every published specification in `docs/specifications/` must link to at least
one BDD feature file under `tests/behavior/features/`. The
`scripts/verify_requirements_traceability.py` script scans the requirements
traceability matrix and verifies that specification documents reference existing
feature files. The CI workflow runs this script and fails if a spec lacks a
feature reference or links to a missing file.

Run the check locally with:

```bash
poetry run python scripts/verify_requirements_traceability.py
```

### Cross-references for Traceability

To maintain end-to-end traceability between requirements, issues, and tests, this guide and related documents cross-reference the following artifacts:

- Issues: 
  - [issues/devsynth-run-tests-hangs.md](../../issues/devsynth-run-tests-hangs.md) — runner stability and provider short-circuiting.
  - [issues/release-readiness-v0-1-0-alpha-1.md](../../issues/release-readiness-v0-1-0-alpha-1.md) — release preparation checklist context.
  - [issues/Finalize-WSDE-EDRR-workflow-logic.md](../../issues/Finalize-WSDE-EDRR-workflow-logic.md) — workflow logic alignment for BDD coverage.
  - [issues/Complete-Sprint-EDRR-integration.md](../../issues/Complete-Sprint-EDRR-integration.md) — integration tasks mapped to behavior features.
- Specifications index: [docs/specifications/](../specifications/index.md) — authoritative specs linked by behavior features under `tests/behavior/features/`.
- Task tracker: [docs/tasks.md](../tasks.md) — prioritized tasks; update checkboxes as items are completed.

When you add or modify tests:
- Link the relevant specification at the top of the test file (see existing feature files for examples).
- Reference the driving issue in the test docstring or comments where appropriate.
- Ensure `scripts/verify_requirements_traceability.py` passes locally and in CI.

## Continuous Integration

DevSynth uses GitHub Actions for continuous integration testing. The CI pipeline:

1. Runs all tests on PR and push to main.
2. Verifies test isolation and cleanliness.
3. Checks test coverage.
4. Runs linting and type checking.


## Test Coverage

DevSynth aims for high test coverage, with a focus on covering:

1. Core memory and provider components.
2. API endpoints and CLI commands.
3. Error handling paths.
4. Configuration handling.


Test coverage is tracked and reported in CI runs.

---

_Last updated: August 23, 2025_
