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

See also: [Resources Matrix](../resources_matrix.md) for a concise mapping of extras to DEVSYNTH_RESOURCE_* flags and quick enablement examples.

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

#### Provider defaults and offline-first behavior

By default, the devsynth run-tests CLI enforces offline-first execution and a safe stub provider to avoid accidental remote calls:
- DEVSYNTH_OFFLINE=true (unless already set)
- DEVSYNTH_PROVIDER=stub (unless already set)

These defaults can be overridden explicitly in your environment if you need to exercise real providers locally, but keep them off in CI unless a job explicitly enables backends.

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

### Smoke Mode (reduced plugin surface)

Smoke mode is designed for the fastest, most hermetic signal when diagnosing failures or validating a PR quickly. It disables third-party pytest plugins by setting `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and applies conservative timeouts.

When to use:
- Quick sanity on a branch to surface deterministic failures early.
- Reproducing flakes with fewer moving parts (plugins disabled).
- CI fast path (see docs/tasks.md Task 54) when plugin interactions are not under test.

How to run:
```bash
# Fast + smoke + no-parallel + stop early (maxfail=1)
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# Generate an HTML report even in smoke mode
poetry run devsynth run-tests --smoke --speed=fast --report
```

### Segmentation of slow tests (batching)

Running slow tests in isolation and in batches should produce consistent results. For long-running suites, prefer batching to reduce rerun costs and improve observability of partial progress.

Recommendations:
- Use segmentation for medium and slow suites when they exceed a few minutes locally or in CI.
- Default batch size: 50 tests per segment works well for our suite. Tune to 25–100 depending on stability and runtime characteristics.
- Keep xdist disabled for initial triage on flakes; re-enable once stable.

Examples:
```bash
# Segment slow tests into default-sized batches (50)
poetry run devsynth run-tests --target all-tests --speed slow --segment

# Segment both medium and slow, with smaller batches of 25
poetry run devsynth run-tests --target all-tests --speed medium --speed slow --segment --segment-size 25

# Combine with an HTML report for each segment (artifacts under test_reports/)
poetry run devsynth run-tests --target all-tests --speed slow --segment --report
```

Notes:
- When using --segment, the runner first performs a collection step (cached by default; see collection cache TTL guidance below). Each batch executes with the same marker and resource gating.
- Prefer segment sizes that complete within 3–8 minutes per batch to maximize signal without prolonging feedback cycles.
- If a batch shows flakiness, re-run that segment with --no-parallel and consider adding @pytest.mark.isolation to offending tests or refactoring shared state.

Observed limitations and notes:
- Plugins that provide fixtures or markers will not be available; tests must not depend on them when running in smoke.
- Coverage and benchmarking are implicitly disabled in smoke runs.
- If behavior differs between smoke and normal mode, investigate plugin side effects (ordering, auto-use fixtures, monkeypatching). Prefer making tests robust to both modes.

Troubleshooting:
- If collection fails only outside smoke mode, bisect enabled plugins to find the interfering one; open an issue with a minimal repro.
- If a test needs a plugin, avoid running it in smoke by marking or gating it appropriately.

### Inventory collection constraints and timeouts

The --inventory flag performs a collection-only pass and writes test_reports/test_inventory.json. In large repositories, unconstrained inventory may time out due to plugin load and global discovery costs. To keep inventory responsive:

- Scope inventory whenever possible:
  - poetry run devsynth run-tests --inventory --target unit-tests --speed=fast
  - poetry run devsynth run-tests --inventory --target integration-tests --speed=medium
- Prefer smoke mode to disable third-party plugins during inventory if you only need node IDs and marker summaries:
  - poetry run devsynth run-tests --inventory --smoke --no-parallel
- Control collection cache TTL to avoid repeated full discovery when iterating locally:
  - export DEVSYNTH_COLLECTION_CACHE_TTL_SECONDS=3600  # default; raise to reduce recache frequency
- Ensure speed markers are normalized (see scripts/verify_test_markers.py). Missing or module-level-only markers increase inventory time by forcing broader marker queries.
- If inventory still times out:
  - Reduce breadth (narrow target and speed),
  - Run in smoke mode, and
  - Increase the process timeout via your shell/CI runner if necessary. In CI, prefer targeted inventory per lane over global.

Acceptance for docs/tasks.md #22: These constraints and mitigations are now documented here and in the CLI reference; inventory commands are provided with scoped examples.

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
  - DEVSYNTH_OFFLINE: true/false; defaults to true under devsynth run-tests to prevent remote calls
  - DEVSYNTH_PROVIDER: provider name; defaults to stub under devsynth run-tests unless overridden
  - DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE: true/false to opt in/out of LM Studio tests
  - DEVSYNTH_RESOURCE_CLI_AVAILABLE: true/false for CLI-dependent tests
  - DEVSYNTH_RESOURCE_WEBUI_AVAILABLE: true/false for WebUI-dependent tests
  - DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE: true/false to force skip/presence
  - DEVSYNTH_PROPERTY_TESTING: true/false to enable property tests

### Quick recipes: enabling optional resources locally

The following examples show how to enable optional backends locally. Prefer Poetry for installs. After enabling, run the relevant tests via devsynth run-tests. See tests/README.md for the authoritative, extended list and context.

- TinyDB
  - Install: poetry add tinydb --group dev
  - Enable: export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
- DuckDB
  - Install: poetry add duckdb --group dev
  - Enable: export DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true
- LMDB
  - Install: poetry add lmdb --group dev
  - Enable: export DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true
- FAISS (CPU)
  - Install: poetry add faiss-cpu --group dev
  - Enable: export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true
- Kuzu
  - Install: poetry add kuzu --group dev
  - Enable: export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true
- ChromaDB
  - Install: poetry add chromadb tiktoken --group dev
  - Enable: export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
- RDFLib (if applicable)
  - Install: poetry add rdflib --group dev
  - Enable: export DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE=true
- LM Studio (local LLM)
  - Install extras (optional): poetry install --extras llm
  - Configure endpoint: export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
  - Enable tests: export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true

Examples of running subsets after enabling resources:

- poetry run devsynth run-tests --target unit-tests --speed=fast
- poetry run devsynth run-tests --target integration-tests --speed=fast

For more details and troubleshooting, refer to tests/README.md and .junie/guidelines.md.

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

### Logging during tests

- Default log level during tests is WARNING to keep output focused and avoid slowing down parallel runs.
- To enable DEBUG logs for targeted reproduction, use one of the following:
  - Environment variable (preferred for CLI):
    ```bash
    DEVSYNTH_LOG_LEVEL=DEBUG poetry run devsynth run-tests --speed=fast --no-parallel -k <node>
    ```
  - Pytest CLI logging (direct pytest):
    ```bash
    poetry run pytest -k <node> -o log_cli=true -o log_cli_level=DEBUG
    ```
  - Per-module logger override within a test using caplog:
    ```python
    def test_debug_trace(caplog):
        caplog.set_level("DEBUG", logger="devsynth")
        ...
    ```
- Avoid enabling DEBUG globally in CI; restrict to reproductions and local diagnosis to minimize noise.

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

## Test Failure Playbook

Use this Socratic, step-by-step checklist to isolate and resolve failures quickly. Capture thesis/antithesis/synthesis outcomes in docs/rationales/test_fixes.md for significant fixes.

1) What is the expected behavior?
- Identify the precise assertion or behavior the test intends to validate.
- Cross-check against docs/user_guides/cli_command_reference.md and relevant module docs.

2) What alternatives could explain the failure?
- Environment misconfig (extras missing, env flags false vs true).
- Plugin side effects (ordering, auto-use fixtures) vs smoke mode.
- Hidden shared state or global caches leaking between tests.
- Non-determinism (time, randomness, ordering, async race).

3) Which assumptions can we falsify quickly?
- Re-run in smoke mode: poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
- Disable parallel: add --no-parallel and observe changes.
- Force resource flags (enable/disable) to confirm guard behavior.
- Pin seeds and freeze time via deterministic fixtures.

4) What minimal reproduction isolates the cause?
- Run a single test file or node (use -k, -q) inside Poetry.
- Minimize dependencies by stubbing or skipping optional resources.
- Use tmp_path/tmp_project_dir and verify no writes to repo root.

5) Stabilize and fix
- Apply exactly one speed marker per test function.
- Add @pytest.mark.isolation for tests that need single-worker execution.
- Replace wall-clock/time.sleep reliance with mock_datetime or event synchronization.
- Normalize resource gating with @pytest.mark.requires_resource("<NAME>") and DEVSYNTH_RESOURCE_<NAME>_AVAILABLE.
- Strengthen disable_network coverage where gaps are found.

6) Document and cross-link
- Add a brief Dialectical Review entry: docs/rationales/test_fixes.md (thesis/antithesis/synthesis).
- Reference the driving issue and test file.
- If relevant, add a troubleshooting hint to _failure_tips in src/devsynth/testing/run_tests.py.

Quick commands
- Collect-only: poetry run pytest --collect-only -q
- Fast subset: poetry run devsynth run-tests --speed=fast --no-parallel --maxfail=1
- Smoke: poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
- HTML report: poetry run devsynth run-tests --report

See also: docs/developer_guides/diagnostics.md for a diagnostics command flow checklist and .junie/guidelines.md for the authoritative practices. Track intermittent issues in docs/testing/known_flakes.md.

## Running All Tests

```bash

poetry run pytest

```text

### Using the CLI (preferred)

Use the `devsynth run-tests` command as the primary entrypoint. It wraps pytest with the correct environment and plugins and can generate HTML reports.

```bash
# Run the full unit suite
poetry run devsynth run-tests --target unit-tests

# Run integration tests
poetry run devsynth run-tests --target integration-tests

# Produce an HTML report in `test_reports/`
poetry run devsynth run-tests --target unit-tests --report
```

Combine options (for example, integration tests with a report) as needed.

For utilities that fix flaky tests and categorize runtime, refer to [Test Stabilization Tools](test_stabilization_tools.md).

### Running Specific Test Types

Advanced: The following examples use direct pytest for targeted workflows. For routine development, prefer the CLI wrapper: `poetry run devsynth run-tests`.

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

DevSynth uses GitHub Actions for continuous integration testing. See the authoritative stabilization plan at [docs/plan.md](../plan.md) and the working checklist at [docs/tasks.md](../tasks.md) for the expected CI matrix and acceptance criteria.

The CI pipeline includes:

1. PR fast path: `poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel`.
2. Lint/style/typing/security: flake8, black --check, isort --check-only, mypy, bandit, safety.
3. Nightly medium matrix: `poetry install --with dev --extras "tests retrieval chromadb api"` then `poetry run devsynth run-tests --target all-tests --speed=medium`.
4. Pre-release full suite: `poetry install --with dev,docs --all-extras` then `poetry run devsynth run-tests --target all-tests --speed=slow --report`.
5. Smoke diagnostics: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`.

Live-provider jobs are opt-in only and must be explicitly enabled via environment flags in the job configuration; they are disabled by default in CI:
- OpenAI live checks require `DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true` and a valid `OPENAI_API_KEY`.
- LM Studio live checks require `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true` and a reachable `LM_STUDIO_ENDPOINT`.
- By default, `DEVSYNTH_PROVIDER=stub` and `DEVSYNTH_OFFLINE=true` are set for test runs to prevent unintended network egress.


## Test Coverage

DevSynth aims for high test coverage, with a focus on covering:

1. Core memory and provider components.
2. API endpoints and CLI commands.
3. Error handling paths.
4. Configuration handling.


Test coverage is tracked and reported in CI runs.

---

_Last updated: August 23, 2025_


## Global Isolation Fixtures (autouse)

DevSynth enforces hermetic test execution via autouse fixtures in tests/conftest.py, aligned with .junie/guidelines.md and docs/plan.md:

- global_test_isolation (autouse):
  - Saves/restores the entire environment (os.environ) per test.
  - Saves/restores the working directory; sets ORIGINAL_CWD for diagnostics.
  - Redirects HOME and XDG paths to a tmp directory; patches Path.home() accordingly.
  - Establishes an ephemeral .devsynth tree (memory, logs, checkpoints, workflows) under tmp.
  - Switches CWD into a temporary project dir for each test.
  - Disables file logging; patches logging setup and path creation helpers defensively.
  - Performs best-effort cleanup of stray artifacts in the real CWD after test completion.

- reset_global_state (helper):
  - Resets project-level singletons/caches to avoid cross-test leakage.

- disable_network (autouse):
  - Blocks socket.connect and common client calls (urllib/httpx) to ensure no outbound network in tests. Compatible with responses for requests.

- enforce_test_timeout (autouse):
  - Applies a per-test timeout when DEVSYNTH_TEST_TIMEOUT_SECONDS is set; the CLI sets conservative defaults for smoke/fast runs.

Acceptance for docs/tasks.md #43: These fixtures reset global state, env, and CWD per test. If you discover a path that still writes to the repo root, open an issue and add a minimal repro; the cleanup in global_test_isolation will mitigate in the interim.

See also:
- docs/analysis/flaky_case_log.md (dialectical notes driving these fixtures)
- tests/conftest.py (authoritative implementation)



## Quick checklist: Opt into optional backends locally

Most optional backends are disabled by default via resource flags. To exercise them locally:

1) Pick extras matching the backend and install with Poetry:
   - Examples:
     - TinyDB: poetry install --with dev --extras memory
     - ChromaDB: poetry install --with dev --extras chromadb
     - FAISS/Kuzu: poetry install --with dev --extras retrieval
2) Enable the resource flag(s):
   - export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
   - export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
   - export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true
   - export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true
3) Run tests in a conservative mode first:
   - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
4) Scale out as stable:
   - poetry run devsynth run-tests --target integration-tests --speed=medium --segment --segment-size 50

Notes:
- Keep DEVSYNTH_OFFLINE=true unless intentionally exercising remote providers.
- See docs/developer_guides/resources_matrix.md for a complete mapping extras ↔ flags and additional examples.
- For quick troubleshooting steps, see docs/developer_guides/doctor_checklist.md.


## Quick command recipes (canonical)

Use Poetry to ensure plugins are available.

- Fast local smoke (all fast, reduced plugin surface):
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel
- Unit fast lane:
  - poetry run devsynth run-tests --target unit-tests --speed=fast --no-parallel
- Behavior fast lane:
  - poetry run devsynth run-tests --target behavior-tests --speed=fast --no-parallel
- Integration fast lane:
  - poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel
- Generate HTML report under test_reports/:
  - poetry run devsynth run-tests --report
- Verify speed markers and generate report:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Enable LM Studio mock for local integration tests:
  - export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  - poetry run pytest -q -o addopts="" tests/integration/llm/test_lmstudio_streaming.py

## Property-based tests (opt-in enablement)

Property tests are disabled by default.

- Enable collection/run:
  - export DEVSYNTH_PROPERTY_TESTING=true
  - poetry run pytest tests/property/
- Conventions:
  - Add @pytest.mark.property in addition to exactly one speed marker (@pytest.mark.fast|medium|slow).
  - Keep runs hermetic; avoid live network calls and rely on stubs/offline defaults.
