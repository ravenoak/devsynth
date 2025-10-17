# DevSynth Test Framework

This directory contains tests for the DevSynth project, organized into different types. Always run test and lint commands through `poetry run` to ensure the correct environment is used, and include the requirement ID in each test's docstring (e.g., `ReqID: FR-09`) for traceability:

## API Key and Testing Constraints

### LLM Provider Testing Requirements

**Anthropic API**: Currently waiting on valid API key for testing. Tests requiring Anthropic API are expected to fail until key is available.

**OpenAI API**: Valid API keys available. Use only cheap, inexpensive models (e.g., gpt-3.5-turbo, gpt-4o-mini) and only when absolutely necessary for testing core functionality.

**OpenRouter API**: Valid API keys available with free-tier access. Use OpenRouter free-tier for:
- All OpenRouter-specific tests
- General tests requiring live LLM functionality
- Prefer OpenRouter over OpenAI for cost efficiency

**LM Studio**: Tests run on same host as application tests. Resources are limited - use large timeouts (60+ seconds) and consider resource constraints when designing tests.

### Environment Variables for LLM Testing

Set the following environment variables for LLM provider testing:

```bash
# OpenRouter (preferred for testing)
export OPENROUTER_API_KEY="your-openrouter-key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# OpenAI (use sparingly, only cheap models)
export OPENAI_API_KEY="your-openai-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"

# LM Studio (local testing)
export LM_STUDIO_ENDPOINT="http://127.0.0.1:1234"
export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE="true"
```

- **Unit Tests**: Tests for individual components in isolation (`tests/unit/`)
- **Integration Tests**: Tests for interactions between components (`tests/integration/`)
- **Behavior Tests**: Tests for user-facing features using BDD (`tests/behavior/`)
- **Standalone Tests**: Special-purpose tests that don't fit the other categories (`tests/standalone/`)
- **Sentinel Test**: `tests/test_speed_dummy.py` is a trivial fast test that exists
  to validate tooling; do not remove it.

### See also
- [Improvement Plan](../docs/plan.md)
- [Improvement Tasks Checklist](../docs/tasks.md)
- [CLI Command Reference](../docs/user_guides/cli_command_reference.md)

## Test Organization

### Directory Structure

The test directory follows a standardized structure:

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Global pytest configuration
├── conftest_extensions.py      # Extensions to pytest configuration
├── README.md                   # This documentation file
├── behavior/                   # Behavior-driven tests (BDD)
│   ├── __init__.py
│   ├── features/               # Feature files (.feature)
│   │   ├── __init__.py
│   │   └── <feature_area>/     # Feature files grouped by area
│   │       ├── __init__.py
│   │       └── <feature>.feature
│   ├── steps/                  # Step definitions for features
│   │   ├── __init__.py
│   │   └── test_<feature>_steps.py
│   └── custom_steps/           # Custom step definitions (legacy)
│       └── __init__.py
├── fixtures/                   # Shared test fixtures
│   └── __init__.py
├── integration/                # Integration tests
│   ├── __init__.py
│   └── <feature_area>/         # Integration tests grouped by area
│       ├── __init__.py
│       └── test_<feature>.py
├── standalone/                 # Special-purpose tests
│   └── __init__.py
└── unit/                       # Unit tests
    ├── __init__.py
    └── <module_path>/          # Unit tests follow source structure
        ├── __init__.py
        └── test_<module>.py
```

### Standard Patterns

The following patterns are used for test file placement:

1. **Unit Tests**: `tests/unit/<module_path>/test_<module_name>.py`
   - Unit tests follow the same directory structure as the source code
   - Examples:
     - `src/devsynth/domain/models/wsde_core.py` → `tests/unit/domain/models/test_wsde_core.py`
     - `src/devsynth/domain/models/wsde_facade.py` → `tests/unit/domain/models/test_wsde_facade.py`

2. **Integration Tests**: `tests/integration/<feature_area>/test_<feature_name>.py`
   - Integration tests are grouped by feature area
   - Example: `tests/integration/edrr/test_wsde_edrr_integration.py`

3. **Behavior Tests**:
   - Feature files: `tests/behavior/features/<feature_area>/<feature_name>.feature`
   - Step definitions: `tests/behavior/steps/test_<feature_name>_steps.py`
   - Example: `tests/behavior/features/examples/simple_addition.feature` and `tests/behavior/steps/test_simple_addition_steps.py`

### Purpose of __init__.py Files

Each test directory contains an `__init__.py` file that serves two purposes:

1. Makes the directory a proper Python package for import resolution
2. Contains a docstring that describes the purpose of the tests in that directory

Example:
```python
"""
Unit tests for interface components including CLI, API, and web UI.
"""
```

To execute the entire suite run:

```bash
poetry run devsynth run-tests --speed=all
```

Running `pytest` directly may fail because required plugins (for example
`pytest-bdd`) are installed only in the Poetry virtual environment.

During development, run only fast tests (memory-intensive tests are skipped automatically):

```bash
poetry run devsynth run-tests --speed=fast
```

Tests that require significant memory must be marked with `@pytest.mark.memory_intensive`. Optional external services are gated with resource markers such as `@pytest.mark.requires_resource("lmstudio")` and will be skipped automatically when the corresponding resource is unavailable.

## Local resource enablement (extras + env)

To run optional backends locally, install extras and set resource flags explicitly. These are disabled by default in CI and in the run-tests CLI unless overridden.

- Retrieval backends (FAISS/ChromaDB used by tests):

  ```bash
  poetry install --with dev --extras "tests retrieval chromadb"
  poetry run devsynth run-tests --speed=fast -m "not requires_resource('openai')"
  ```

- FAISS vector store unit tests (requires the retrieval extra and explicit opt-in):

  ```bash
  poetry install --with dev --extras "tests retrieval"
  export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=1
  poetry run pytest tests/unit/application/memory/test_faiss_store.py --maxfail=1 --disable-warnings
  ```

  The environment flag mirrors the resource marker `@pytest.mark.requires_resource("faiss")`.
  When unset or `false`, FAISS tests are skipped automatically. The retrieval
  extra installs the lightweight `faiss-cpu` wheel used by the memory backend.

- ChromaDB memory store tests:

  ```bash
  poetry install --extras chromadb
  export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=1
  ```

### Section 7 helper tasks (sanity, inventory, and marker discipline)

For quick evidence collection and parity with docs/plan.md §7 and docs/tasks.md acceptance artifacts, use the provided Taskfile targets. These commands are smoke-friendly and offline-first by default.

- With Task installed:

  ```bash
  task tests:sanity-and-inventory    # runs scripts/run_sanity_and_inventory.sh
  task tests:marker-discipline       # runs scripts/run_marker_discipline.sh
  ```

- Without Task (direct scripts):

  ```bash
  bash scripts/run_sanity_and_inventory.sh
  bash scripts/run_marker_discipline.sh
  ```

Artifacts are written under test_reports/:
- collect_only_output.txt (pytest --collect-only output)
- smoke_plugin_notice.txt (PASS/FAIL via scripts/verify_smoke_notice.py)
- test_markers_report.json (from marker discipline)
- Any inventory output produced by the run-tests CLI when applicable

These outputs are referenced by docs/tasks.md §1.6 and §2.1–§2.6 and are collected by CI workflows.

To run optional backends locally, install extras and set resource flags explicitly. These are disabled by default in CI and in the run-tests CLI unless overridden.

- Retrieval backends (FAISS/ChromaDB used by tests):

  ```bash
  poetry install --with dev --extras "tests retrieval chromadb"
  poetry run devsynth run-tests --speed=fast -m "not requires_resource('openai')"
  ```

- Memory + LLM with LM Studio:

  ```bash
  poetry install --with dev --extras "tests llm"
  export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
  export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234
  export DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS=10
  export DEVSYNTH_LMSTUDIO_RETRIES=1
  # Prefer --marker to avoid shell/pytest -m quoting pitfalls
  poetry run devsynth run-tests --target integration-tests --speed=fast --no-parallel --maxfail=1 --marker "requires_resource('lmstudio') and not slow"
  ```

- OpenAI provider (nightly/gated local):

  ```bash
  poetry install --with dev --extras llm
  export DEVSYNTH_PROVIDER=openai
  export OPENAI_API_KEY=your-key
  export OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
  poetry run devsynth run-tests --speed=fast -m "requires_resource('openai') and not slow"
  ```

- Provider-system adapters (unit coverage for HTTP clients):

  ```bash
  export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true   # enable OpenAI adapter paths
  export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true # enable LM Studio adapter paths
  poetry run pytest -m "requires_resource('openai') or requires_resource('lmstudio')"
  ```

  Tests that exercise the real `requests`/`httpx` branches in
  `devsynth.adapters.provider_system` carry these markers and remain skipped until
  the corresponding flag(s) are set.

Notes:
- Resource markers: @pytest.mark.requires_resource("<name>") map to DEVSYNTH_RESOURCE_<NAME>_AVAILABLE flags.
- Extras ↔ flags mapping: see docs/developer_guides/testing.md (Quick Reference: Extras ↔ Resource flags). For example, 'retrieval' → FAISS/KUZU flags; 'chromadb' → CHROMADB flag; 'memory' → TINYDB/DUCKDB/LMDB/KUZU/FAISS/CHROMADB flags; 'lmstudio' → LMSTUDIO flag; 'webui' → WEBUI flag.
- The run-tests CLI defaults to offline and stub provider; override env vars explicitly when enabling real services.

## Test Speed Categories

Tests are grouped by runtime using pytest markers:

- `@pytest.mark.fast` – completes in under **1 second**
- `@pytest.mark.medium` – completes in under **5 seconds**
- `@pytest.mark.slow` – takes **5 seconds or more**

Each test **must include exactly one** of these markers. The
`tests/conftest_extensions.py` plugin enforces this requirement and provides a
`--speed` option so you can filter tests by runtime. Apply runtime markers
directly above each test function; module-level `pytestmark` assignments are
not recognized and will cause verification failures:

```bash
poetry run pytest --speed=fast
```

You can also use helper commands:

```bash
poetry run devsynth run-tests --fast --medium
```

## Property-based Tests (opt-in)

Property tests using Hypothesis are disabled by default to keep fast, stable CI runs. Enable them explicitly by setting the environment variable before running tests:

```bash
export DEVSYNTH_PROPERTY_TESTING=true
poetry run pytest tests/property/
```

Conventions:
- Mark all property tests with `@pytest.mark.property` in addition to a speed marker (`@pytest.mark.fast|medium|slow`).
- Property tests may also live in unit/ directories; they should still include the `property` marker.
- The tests/property/conftest.py ensures these tests are only collected when `DEVSYNTH_PROPERTY_TESTING` is truthy (1/true/yes/on).

## Conditional Test Execution

The test framework includes a mechanism for conditionally skipping tests based on resource availability. This is useful for tests that depend on external resources like LM Studio or other services that might not always be available.

### Using Resource Markers

To mark a test as requiring a specific resource, use the `requires_resource` marker:

```python
import pytest

@pytest.mark.requires_resource("lmstudio")
def test_that_needs_lmstudio():
    # This test will be skipped if LM Studio is not available
    ...
```

For BDD tests, you can define a marker and apply it to scenario functions:

```python
import pytest
from pytest_bdd import scenario

# Define the marker
lmstudio_available = pytest.mark.requires_resource("lmstudio")

# Apply it to a scenario
@lmstudio_available
@scenario('feature_file.feature', 'Scenario name')
def test_scenario():
    pass
```

### Available Resources

The following resources are currently supported. Set the corresponding
environment variable to `true` to enable tests that depend on the resource:

- **lmstudio** – `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE`
- **openai** – no environment variable (tests run by default)
- **codebase** – `DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE`
- **cli** – `DEVSYNTH_RESOURCE_CLI_AVAILABLE`

### Tests Using Resource Markers

The following tests rely on each resource marker:

- `lmstudio`: `tests/integration/test_lmstudio_provider.py`
- `openai`: `tests/integration/test_openai_provider.py`
- `codebase`: `tests/integration/test_self_analyzer.py`
- `cli`: `tests/behavior/test_cli_commands.py`

### Controlling Resource Availability

Resource availability is determined by:

1. Specific checker functions that verify if a resource is actually available
2. Environment variables that can override the checker functions

To disable a resource via environment variables:

```bash
# Disable LM Studio tests
export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false

# Disable codebase analysis tests
export DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=false

# Disable CLI tests
export DEVSYNTH_RESOURCE_CLI_AVAILABLE=false
```

If you want to run tests that depend on these resources, set the corresponding variable to `true` and ensure the service is running. For example:

```bash
# Enable LM Studio tests
export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
export LM_STUDIO_ENDPOINT=http://localhost:1234
# Start LM Studio in API mode (example)
# lmstudio --api --port 1234

# Enable codebase analysis tests
export DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE=true

# Enable CLI tests
export DEVSYNTH_RESOURCE_CLI_AVAILABLE=true

# Enable OpenAI integration
export OPENAI_API_KEY=sk-your-key

poetry run pytest
```
Running plain `pytest` may fail because required plugins are installed only in the Poetry-managed environment.

### Environment Variables for Tests

The autouse `global_test_isolation` fixture in `tests/conftest.py` restores the
environment and working directory for each test. Because it runs after modules
import, **do not set environment variables at import time**. Instead, export
them before invoking the test suite or set them within a test using
`monkeypatch.setenv()`.

Common environment variables:

- `DEVSYNTH_ACCESS_TOKEN` – token for authenticated API calls. Override by
  exporting it or using `monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "token")`.
- `DEVSYNTH_NO_FILE_LOGGING` – prevents creation of log files when set to `1`.
  The isolation fixture sets this to `1` by default; set to `0` to enable
  logging.
- `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` – controls optional resource-dependent
  tests such as `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE`. Set to `true` or `false`
  to force-enable or disable a resource.

Most tests run with mocked providers and do not require external services. To
enable LM Studio tests, provide an endpoint and set the variable to `true`:

```bash
export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true
export LM_STUDIO_ENDPOINT=http://localhost:1234
```

`tests/conftest.py` sets helpful defaults so tests run in isolation:

- `OPENAI_API_KEY` is set to `test-openai-key`.
- `LM_STUDIO_ENDPOINT` defaults to `http://127.0.0.1:1234`.
- `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE` defaults to `false`.
- `DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE` and `DEVSYNTH_RESOURCE_CLI_AVAILABLE`
  default to `true`.

Other variables such as `DEVSYNTH_PROJECT_DIR` are automatically configured
during tests.

### Adding New Resources

To add a new resource:

1. Define a checker function in `tests/conftest.py`:

```python
def is_my_resource_available() -> bool:
    """Check if my resource is available."""
    # Check environment variable override
    if os.environ.get("DEVSYNTH_RESOURCE_MY_RESOURCE_AVAILABLE", "true").lower() == "false":
        return False

    # Actual availability check
    try:
        # Check if the resource is available
        return True
    except Exception:
        return False
```

2. Add the checker to the `checker_map` in `is_resource_available`:

```python
checker_map = {
    "lmstudio": is_lmstudio_available,
    "codebase": is_codebase_available,
    "cli": is_cli_available,
    "my_resource": is_my_resource_available,
}
```

3. Use the marker in your tests:

```python
@pytest.mark.requires_resource("my_resource")
def test_that_needs_my_resource():
    ...
```

## Quickstart and Troubleshooting

Quickstart (recommended minimal setup for contributors):

```bash
# Install with dev group and targeted extras to avoid heavy GPU/LLM deps
poetry install --with dev --extras "tests retrieval chromadb api"
# Sanity: collection-only to verify environment
poetry run pytest --collect-only -q
# Fast smoke lane to reduce plugin surface and avoid xdist
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
```

Helper scripts for Section 7 (sanity, inventory, marker reports):

- Standardize sanity and inventory runs and write logs/artifacts under test_reports/:
  ```bash
  bash scripts/run_sanity_and_inventory.sh
  # or explicitly set smoke via env
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 bash scripts/run_sanity_and_inventory.sh
  ```
- Generate the marker verification report and run the changed-only check:
  ```bash
  bash scripts/run_marker_discipline.sh
  # Produces: test_reports/test_markers_report.json
  ```

Common issues and recovery steps:
- Plugin autoload conflicts or unexplained hangs:
  - Re-run in smoke mode (sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1) as above.
  - Inspect environment and plugin list:
    ```bash
    bash scripts/diagnostics.sh
    ```
- Missing extras or ModuleNotFoundError for plugins like pytest-bdd:
  - Ensure you installed with the minimal test baseline extras (see commands above).
- Tests making network calls or hanging on providers:
  - Ensure offline defaults are in effect (the CLI sets DEVSYNTH_PROVIDER=stub and DEVSYNTH_OFFLINE=true for test lanes unless overridden).
  - Do not enable resource flags unless you intend to use the corresponding backend.

The diagnostics script prints an environment snapshot, the pytest plugin list (respecting smoke mode via PYTEST_DISABLE_PLUGIN_AUTOLOAD=1), and a quick discovery snapshot to help pinpoint issues.

## Running Tests

To run all tests:

```bash
poetry run pytest
```
Invoking plain `pytest` outside of the Poetry environment may fail because some required plugins are installed only in that virtual environment.

### Environment Setup

Refer to [../docs/developer_guides/development_setup.md](../docs/developer_guides/development_setup.md) for instructions on configuring your environment.

Before running tests, you **must** install DevSynth with the development extras:

```bash
poetry install --with dev,docs --all-extras
poetry shell
```

For a lightweight setup that skips GPU/LLM libraries use:

```bash
poetry install --with dev --extras tests retrieval chromadb api
```

Optional backends such as **FAISS** or **LMDB** may require additional extras:

```bash
poetry install --extras retrieval
# or install from PyPI
pip install 'devsynth[retrieval]'
```

### Resource Flags

Store-specific memory tests and optional LLM providers are gated by environment
flags and resource markers. Set a flag to `false` to skip tests when a resource
is unavailable:

- `DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE`
- `DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE`
- `DEVSYNTH_RESOURCE_FAISS_AVAILABLE`
- `DEVSYNTH_RESOURCE_KUZU_AVAILABLE`
- `DEVSYNTH_RESOURCE_LMDB_AVAILABLE`
- `DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE`
- `DEVSYNTH_RESOURCE_TINYDB_AVAILABLE`
- `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE`

Each corresponding test module uses `@pytest.mark.requires_resource("<backend>")`
to declare its dependency.

#### Enabling specific resources locally

For local runs, enable a resource by installing the required extra/dependency and
setting the corresponding environment flag to `true` before running tests.

- TinyDB
  - Install: `poetry add tinydb --group dev` or `pip install tinydb`
  - Enable: `export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true`
- DuckDB
  - Install: `poetry add duckdb --group dev` or `pip install duckdb`
  - Enable: `export DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true`
- LMDB
  - Install: `poetry add lmdb --group dev` or `pip install lmdb`
  - Enable: `export DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true`
- FAISS (CPU)
  - Install: `poetry add faiss-cpu --group dev` or `pip install faiss-cpu`
  - Enable: `export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true`
- Kuzu
  - Install: `poetry add kuzu --group dev` or `pip install kuzu`
  - Enable: `export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true`
- ChromaDB
  - Install: `poetry add chromadb tiktoken --group dev` or `pip install "chromadb>=0.5" tiktoken`
  - Enable: `export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true`
- RDFLib (if used by RDF adapters)
  - Install: `poetry add rdflib --group dev` or `pip install rdflib`
  - Enable: `export DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE=true`
- LM Studio (local LLM)
  - Install extras (optional): `poetry install --extras llm`
  - Configure: `export LM_STUDIO_ENDPOINT=http://127.0.0.1:1234`
  - Enable: `export DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=true`

After enabling resources, run the desired subset or the full suite:

```bash
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/behavior/
```

To run tests with verbose output:

```bash
poetry run pytest -v
```

To see which tests would be skipped due to missing resources:

```bash
poetry run pytest --collect-only -v
```

### Using `devsynth run-tests`

The `devsynth run-tests` CLI wraps `pytest` and expects all
required plugins to be installed via Poetry.
Invoke the command from the Poetry environment to run the full suite or selected groups:

```bash
poetry run devsynth run-tests                     # run all tests
poetry run devsynth run-tests --target unit-tests  # run only unit tests
poetry run devsynth run-tests --report             # generate HTML report under test_reports/
poetry run devsynth run-tests --maxfail 1          # stop after the first failure
```

For additional utilities like flaky-test fixes and incremental categorization, see [Test Stabilization Tools](../docs/developer_guides/test_stabilization_tools.md).

## Referencing Requirements in Tests

All tests should include the requirement ID they verify in the test's docstring. This links the test back to the relevant entry in `docs/requirements_traceability.md`.

You can verify compliance locally:

```bash
poetry run python scripts/verify_reqid_references.py --json test_reqid_report.json
```

Example:

```python
def test_workflow_progress_tracking():
    """Validate workflow status retrieval. ReqID: FR-09"""
    ...
```

## Test Marker Report and Contributor Workflow

### HOWTO: Move module-level speed markers to function level

If you find `pytestmark = pytest.mark.fast` (or medium/slow) at the top of a test module, migrate these markers to function level. The verifier and repository policy require exactly one speed marker per test function; module-level speed markers are not recognized.

Steps:
- Remove the module-level assignment line containing the speed marker.
- Add exactly one of `@pytest.mark.fast | @pytest.mark.medium | @pytest.mark.slow` immediately above each test function definition in that file.
- If a test already has a speed marker, do not add another; ensure there is exactly one.
- Re-run the verifier on changed files to confirm compliance:
  ```bash
  poetry run python scripts/verify_test_markers.py --changed
  ```

Example before:
```python
import pytest

pytestmark = pytest.mark.fast

def test_adds_numbers():
    assert 1 + 1 == 2
```

Example after:
```python
import pytest

@pytest.mark.fast
def test_adds_numbers():
    assert 1 + 1 == 2
```

Notes:
- Do not use module-level speed markers. They are intentionally not recognized in this repository to avoid ambiguity.
- Keep one and only one speed marker per test function. Use the verifier script to validate.

Generate an updated marker report after modifying tests:

```bash
poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
```

Contributor workflow for speed markers (aligns with docs/plan.md and project guidelines):
- Before committing changed tests:
  - Run the fixer to add missing markers conservatively:
    ```bash
    poetry run python scripts/fix_missing_markers.py --paths tests/
    ```
  - Normalize duplicates to exactly one speed marker per test:
    ```bash
    poetry run python scripts/fix_duplicate_markers.py --paths tests/
    ```
  - Re-verify only changed files to keep iterations fast:
    ```bash
    poetry run python scripts/verify_test_markers.py --changed
    ```
- The pre-commit hook also runs the verifier on changed test files and will block commits on violations. Use:
  ```bash
  poetry run pre-commit run --files <changed test files>
  ```
  to reproduce the hook locally.

Policy reminders:
- Exactly one of `@pytest.mark.fast | @pytest.mark.medium | @pytest.mark.slow` must be present on each test function.
- Module-level `pytestmark` with speed markers is not allowed; apply markers at the function level.

For large suites, pass `--changed` to verify only tests modified since the last
commit and speed up runs:

```bash
poetry run python scripts/verify_test_markers.py --changed
```

Including the requirement ID ensures traceability between tests and requirements.


## Default-to-stability shortcuts

When triaging failures or validating a fresh environment, prefer the stable, low‑surface commands below. They align with project guidelines and docs/plan.md and are safe to copy‑paste.

- Smoke mode (reduces plugin surface; disables xdist and third‑party plugins):

  ```bash
  poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1
  ```

- Segmentation for medium/slow suites (batch execution to avoid long tails):

  ```bash
  poetry run devsynth run-tests --segment --segment-size 50 --no-parallel
  ```

- Inventory scoping (fast collection-only to discover targets and node IDs):

  ```bash
  poetry run devsynth run-tests --inventory --target unit-tests --speed=fast
  ```

See also:
- docs/developer_guides/testing.md (Smoke Mode, Inventory, Segmentation)
- docs/user_guides/cli_command_reference.md (full CLI options)
