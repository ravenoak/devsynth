---

author: DevSynth Team
date: '2025-05-20'
last_reviewed: "2025-07-10"
status: published
tags:

- testing
- hermetic
- isolation
- best-practices
- developer-guide

title: Hermetic Testing Guide
version: "0.1.0-alpha.1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Hermetic Testing Guide
</div>

# Hermetic Testing Guide

## Introduction

This guide outlines DevSynth's approach to hermetic testing - creating tests that are fully isolated, reproducible, and free from side effects. Hermetic tests are reliable, consistent, and don't interfere with each other or the developer's environment.

## Core Principles

### 1. Isolation

Tests must be completely isolated from:

- The real filesystem
- External services and APIs
- Global state and environment variables
- Other tests


### 2. Determinism

Tests should be deterministic and reproducible:

- Fixed timestamps and random values
- Consistent ordering of operations
- No reliance on external state


### 3. Zero Side Effects

Tests must not:

- Create files outside of temporary directories
- Modify environment variables without restoring them
- Leave any artifacts in the developer's workspace
- Make real network calls


## Implementation Guide

### Filesystem Isolation

Always use temporary directories for any file operations:

```python

# GOOD: Using pytest's tmp_path fixture

def test_file_operations(tmp_path):
    test_file = tmp_path / "test.txt"
    with open(test_file, 'w') as f:
        f.write("test content")
    # Test logic...

# BAD: Using hard-coded paths

def test_file_operations_bad():
    with open("test.txt", 'w') as f:  # DON'T DO THIS
        f.write("test content")
    # Test logic...
```

## Environment Variable Isolation

Always save and restore environment variables:

```python

# GOOD: Using monkeypatch fixture

def test_env_vars(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_TEST_VAR", "test_value")
    # Test logic...
    # monkeypatch automatically restores environment after test

# BAD: Directly modifying os.environ

def test_env_vars_bad():
    os.environ["DEVSYNTH_TEST_VAR"] = "test_value"  # DON'T DO THIS
    # Test logic...
    # Environment is now polluted
```

## Global State Isolation

Reset any global state between tests:

```python

# GOOD: Using fixtures to reset global state

@pytest.fixture
def reset_globals():
    # Save original state
    original_state = module.GLOBAL_VAR
    yield
    # Restore original state
    module.GLOBAL_VAR = original_state

def test_with_global_state(reset_globals):
    # Test logic...
```

## External Service Mocking

Mock all external services:

```python

# GOOD: Using mock objects

def test_external_service(mocker):
    mock_service = mocker.patch("devsynth.adapters.some_service.Client")
    mock_service.return_value.get_data.return_value = {"test": "data"}
    # Test logic using the mocked service...

# BAD: Using real services

def test_external_service_bad():
    real_client = some_service.Client()  # DON'T DO THIS
    data = real_client.get_data()  # Makes real API call
    # Test logic...
```

Isolating tests from external services prevents network flakiness and unwanted
side effects. Always patch network clients and service adapters with mocks or
stub implementations. When your tests rely on LLM calls or memory store
operations, use the dedicated fixtures described below to avoid hitting real
APIs or persistent storage.

## Working Directory Isolation

Always change the working directory in a controlled way:

```python

# GOOD: Saving and restoring cwd

def test_with_cwd_change(tmp_path):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # Test logic...
    finally:
        os.chdir(original_cwd)

# BAD: Changing cwd without restoration

def test_with_cwd_change_bad(tmp_path):
    os.chdir(tmp_path)  # DON'T DO THIS without restoration
    # Test logic...
    # cwd is now changed for subsequent tests
```

## Using DevSynth's Test Fixtures

DevSynth provides several fixtures to facilitate hermetic testing:

### Global Test Environment

The `test_environment` fixture in `tests/conftest.py` provides a completely isolated environment for tests:

```python
def test_something_with_isolated_env(test_environment):
    # test_environment is automatically applied to all tests
    project_dir = test_environment["project_dir"]
    # Use the project_dir for file operations
    # All paths are temporary and will be cleaned up
```

### Mocked Time and UUIDs

Use the fixtures for deterministic values:

```python
def test_with_fixed_time(mock_datetime):
    # mock_datetime is fixed at 2025-01-01 12:00:00
    current_time = datetime.datetime.now()
    assert current_time.year == 2025

def test_with_fixed_uuid(mock_uuid):
    # mock_uuid always returns 12345678-1234-5678-1234-567812345678
    id = uuid.uuid4()
    assert str(id) == "12345678-1234-5678-1234-567812345678"
```

### Mocked LLM Providers

Use the provider mocks for tests that would otherwise call LLM APIs:

```python
def test_with_mocked_llm(mock_openai_provider):
    # This will use the mock provider instead of making real API calls
    result = some_function_that_calls_openai()
    assert "Test completion response" in result
```

Tests should never perform live LLM queries. The `mock_openai_provider` fixture
returns deterministic completions and keeps all network traffic inside the test
environment.

### Mocked Ports and Memory Stores

Use the lightweight port fixtures from `tests/fixtures/ports.py` to avoid real
service calls:

```python
from devsynth.domain.models.memory import MemoryType

def test_with_mocked_ports(llm_port, memory_port, onnx_port):
    assert "mock" in llm_port.generate("hi").lower()
    item_id = memory_port.store_memory("data", MemoryType.WORKING)
    assert memory_port.retrieve_memory(item_id)
    onnx_port.load_model("model.onnx")
    assert list(onnx_port.run({"x": [1]}))
```

These fixtures fully emulate the behaviors of the real services. The
`memory_port` fixture provides an in-memory store so tests never interact with
persistent databases or stateful backends.

## Best Practices

1. **Use `tmp_path` or `tempfile.TemporaryDirectory`** for all file operations
2. **Use `monkeypatch` for environment variables** instead of direct modification
3. **Mock all external services** including APIs, databases, and file systems
4. **Use `test_environment` fixture** for complete isolation
5. **Save and restore global state** using fixtures
6. **Verify test cleanup** by running tests repeatedly and checking for artifacts
7. **Use `capsys` or `caplog`** to capture and verify output rather than checking real log files
8. **Use `ensure_path_exists` from settings.py** for directory creation to respect test isolation


### Directory Creation and .devsynth/ Isolation

When implementing components that need to create directories (especially `.devsynth/` directories):

```python

# GOOD: Using ensure_path_exists which respects test isolation

from devsynth.config.settings import ensure_path_exists

def initialize_component(directory_path=None):
    if directory_path is None:
        # Use DEVSYNTH_PROJECT_DIR if set (for test isolation)
        project_dir = os.environ.get('DEVSYNTH_PROJECT_DIR')
        if project_dir:
            directory_path = os.path.join(project_dir, ".devsynth", "component_data")
        else:
            directory_path = os.path.join(os.getcwd(), ".devsynth", "component_data")

    # This respects test isolation by checking DEVSYNTH_NO_FILE_LOGGING
    ensure_path_exists(directory_path)
    return directory_path

# BAD: Directly creating directories without respecting test isolation

def initialize_component_bad(directory_path=".devsynth/component_data"):
    os.makedirs(directory_path, exist_ok=True)  # DON'T DO THIS
    return directory_path
```

The `ensure_path_exists` function checks for the `DEVSYNTH_NO_FILE_LOGGING` environment variable, which is set to "1" in test environments to prevent directory creation. It also respects the `DEVSYNTH_PROJECT_DIR` environment variable, which points to a temporary directory in test environments.

## Common Pitfalls

1. **Using `os.getcwd()`** without considering the test environment
2. **Direct file operations** without using temporary directories
3. **Using `__file__` relative paths** that might escape test isolation
4. **Global registries or singletons** that persist state between tests
5. **Time-dependent tests** without proper mocking of datetime


## CI and Verification

The DevSynth CI system enforces hermetic testing by:

1. Running tests in clean, isolated environments
2. Failing tests that attempt to access unauthorized paths
3. Verifying that no side effects remain after test execution
4. Running tests in random order to detect inter-test dependencies


## Contributing New Tests

When adding new tests:

1. Review existing fixtures in `tests/conftest.py`
2. Use appropriate isolation techniques based on this guide
3. Ensure tests pass when run in any order or repeated multiple times
4. Add new fixtures to `conftest.py` if needed for common isolation patterns


By following these guidelines, we ensure that DevSynth's test suite remains reliable, fast, and maintainable.
## Implementation Status

.
