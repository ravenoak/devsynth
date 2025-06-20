# DevSynth Test Framework

This directory contains tests for the DevSynth project, organized into different types:

- **Unit Tests**: Tests for individual components in isolation (`tests/unit/`)
- **Integration Tests**: Tests for interactions between components (`tests/integration/`)
- **Behavior Tests**: Tests for user-facing features using BDD (`tests/behavior/`)

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

python -m pytest
```

### Environment Variables for Tests

Most tests run with mocked providers and do not require any external services. The `global_test_isolation` fixture automatically sets `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false` so LM Studio dependent tests are skipped. To enable them, provide the endpoint and set the variable to `true`:

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

Other variables such as `DEVSYNTH_PROJECT_DIR` and `DEVSYNTH_NO_FILE_LOGGING`
are automatically configured during the tests.

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
python -m pytest
```

### Environment Setup

Before running tests, you **must** install DevSynth with the development extras:

```bash
pip install -e '.[dev]'
# or
poetry install
poetry sync --all-extras --all-groups
```

For a minimal install you can use:

```bash
pip install -e '.[minimal,dev]'
```

Optional backends such as **ChromaDB**, **FAISS**, or **LMDB** require extra packages:

```bash
pip install 'devsynth[retrieval]'
```

To run tests for a specific type:

```bash
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/behavior/
```

To run tests with verbose output:

```bash
python -m pytest -v
```

To see which tests would be skipped due to missing resources:

```bash
python -m pytest --collect-only -v
```
