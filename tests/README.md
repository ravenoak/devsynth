# DevSynth Test Framework

This directory contains tests for the DevSynth project, organized into different types. Always run test and lint commands through `poetry run` to ensure the correct environment is used, and include the requirement ID in each test's docstring (e.g., `ReqID: FR-09`) for traceability:

- **Unit Tests**: Tests for individual components in isolation (`tests/unit/`)
- **Integration Tests**: Tests for interactions between components (`tests/integration/`)
- **Behavior Tests**: Tests for user-facing features using BDD (`tests/behavior/`)
- **Standalone Tests**: Special-purpose tests that don't fit the other categories (`tests/standalone/`)

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

## Test Speed Categories

Tests are grouped by runtime using pytest markers:

- `@pytest.mark.fast` – completes in under **1 second**
- `@pytest.mark.medium` – completes in under **5 seconds**
- `@pytest.mark.slow` – takes **5 seconds or more**

`tests/conftest_extensions.py` automatically applies these markers and adds a
`--speed` option so you can filter tests by runtime:

```bash
poetry run pytest --speed=fast
```

You can also use helper commands:

```bash
poetry run devsynth run-tests --fast --medium
```

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

To run tests for a specific type:

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
```

For additional utilities like flaky-test fixes and incremental categorization, see [Test Stabilization Tools](../docs/developer_guides/test_stabilization_tools.md).

## Referencing Requirements in Tests

All tests should include the requirement ID they verify in the test's docstring. This links the test back to the relevant entry in `docs/requirements_traceability.md`.

Example:

```python
def test_workflow_progress_tracking():
    """Validate workflow status retrieval. ReqID: FR-09"""
    ...
```

Including the requirement ID ensures traceability between tests and requirements.
