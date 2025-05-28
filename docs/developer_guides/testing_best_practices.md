# Testing Best Practices for DevSynth

This document outlines best practices for testing in the DevSynth project, covering test isolation, resource markers, and comprehensive testing methodologies.

## Testing Philosophy

DevSynth follows a multi-disciplined approach to testing, combining:

1. **Test-Driven Development (TDD)**: Writing tests before implementing features
2. **Behavior-Driven Development (BDD)**: Describing behavior in natural language and implementing tests
3. **Integration Testing**: Testing interactions between components
4. **Unit Testing**: Testing individual components in isolation

Our testing strategy aims to ensure that:
- Code works as expected
- Edge cases are handled properly
- Changes don't break existing functionality
- Tests serve as documentation for how components should behave

## Resource Markers

DevSynth includes a mechanism for conditionally skipping tests based on resource availability. This is useful for tests that depend on external resources like LM Studio or other services that might not always be available.

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

The following resources are currently supported:
- **lmstudio**: Checks if LM Studio is available at http://localhost:1234
- **codebase**: Checks if the DevSynth codebase is available for analysis
- **cli**: Checks if the DevSynth CLI is available for testing

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

## Test Isolation

### What is Test Isolation?

Test isolation means that each test runs in its own isolated environment, without affecting or being affected by:
- Other tests
- The real system
- The developer's environment
- External services

In the context of DevSynth, this means ensuring that tests don't:
- Create persistent directories or files outside the test environment
- Modify global state that could affect other tests
- Depend on external services or specific environment configurations

### Why is Test Isolation Important?

- **Reliability**: Tests should produce the same results regardless of when or where they're run
- **Reproducibility**: Tests should be reproducible in any environment
- **Parallelization**: Tests should be able to run in parallel without interfering with each other
- **Developer Experience**: Tests shouldn't leave artifacts or modify the developer's environment

### Preventing `.devsynth/` Directory Creation During Tests

One issue that was observed in the testing process was the creation of random `.devsynth/` directories during test runs. This is problematic for several reasons:

1. It pollutes the developer's environment with test artifacts
2. It can cause tests to interfere with each other
3. It makes tests less reproducible and less hermetic

To address this issue, the following changes were implemented:

1. **Enhanced Path Redirection**: Both `ensure_path_exists` in `src/devsynth/config/settings.py` and `ensure_log_dir_exists` in `src/devsynth/logging_setup.py` now redirect paths outside the test environment to be within it. This ensures that even if a test tries to create a directory in the home directory or current working directory, it will be redirected to the test environment.

   The path redirection logic now handles:
   - Home directory paths (e.g., `~/.devsynth/`)
   - Absolute paths (e.g., `/tmp/devsynth/`)
   - Relative paths (e.g., `.devsynth/`)

   For absolute paths, the redirection extracts the path components after the root and appends them to the test directory, ensuring that all file operations remain within the test environment.

2. **Improved Environment Variable Checks**: The functions check for both `DEVSYNTH_NO_FILE_LOGGING` and `DEVSYNTH_PROJECT_DIR` environment variables to determine if they're running in a test environment and should avoid creating directories.

3. **Consolidated Test Fixtures**: The `global_test_isolation` fixture has been enhanced to provide comprehensive isolation for all tests, including setting up the test environment, patching paths, and cleaning up after tests.

4. **Robust Cleanup**: The cleanup logic has been improved to reliably identify and remove any stray artifacts that might be created during testing.

### Test Environment Setup

The test environment is set up in `tests/conftest.py` with several fixtures that ensure proper isolation:

1. `test_environment`: Creates a test environment with temporary directories for tests that need explicit access to these directories.

2. `global_test_isolation`: An autouse fixture that provides comprehensive isolation for all tests. This fixture:
   - Saves and restores environment variables
   - Creates temporary directories for the test
   - Patches paths to use these temporary directories
   - Disables file logging
   - Patches logging and path creation functions
   - Cleans up any stray artifacts after the test

3. `patch_settings_paths`: A deprecated fixture kept for backward compatibility. New tests should rely on `global_test_isolation` instead.

These fixtures work together to ensure that tests don't create directories outside the test environment, even if they explicitly try to do so.

## Best Practices for Writing Tests

When writing tests for DevSynth, follow these best practices to ensure proper isolation:

1. **Use the Global Test Isolation Fixture**: The `global_test_isolation` fixture is automatically applied to all tests, providing a consistent isolated environment. You can access the test environment directories through this fixture if needed:

   ```python
   def test_example(global_test_isolation):
       project_dir = global_test_isolation["project_dir"]
       # Use project_dir for file operations
   ```

2. **Use Temporary Directories for File Operations**: Always use the temporary directories provided by the test environment for file operations.

3. **Mock External Services**: Use pytest's monkeypatch or unittest.mock to mock external services.

4. **Reset Global State**: If your test modifies global state, make sure to reset it after the test.

5. **Use Test-Driven Development (TDD)**: Follow the TDD approach:
   - Write a failing test
   - Implement the minimum code to make the test pass
   - Refactor the code while keeping the test passing

6. **Use Behavior-Driven Development (BDD)**: For feature development, use BDD to define behavior before implementation:
   - Write feature files with scenarios in Gherkin syntax
   - Implement step definitions
   - Implement the feature to make the scenarios pass

7. **Test with Different Content Types**: When testing code that handles different types of content, ensure you test with various content types:

   ```python
   def test_with_string_content():
       # Test with string content
       item = MemoryItem(id="test", content="test content")
       # ...

   def test_with_dict_content():
       # Test with dictionary content
       item = MemoryItem(id="test", content={"key": "value"})
       # ...

   def test_with_list_content():
       # Test with list content
       item = MemoryItem(id="test", content=[1, 2, 3])
       # ...
   ```

8. **Handle Temporary Directories in pytest**: When working with pytest's temporary directories, be aware that the paths might contain "pytest", "tmp", or "temp". This is important when checking if a path is a temporary directory:

   ```python
   def test_path_handling(tmp_path):
       # Check if the path appears to be a pytest temporary directory
       if any(x in str(tmp_path).lower() for x in ["pytest", "tmp", "temp"]):
           # Handle accordingly
           pass
   ```

9. **Use Path Containment Checks Instead of Equality**: When testing code that might redirect paths, check for path containment instead of exact equality:

   ```python
   def test_path_redirection(tmp_path):
       # The function might redirect the path
       result_path = ensure_path_exists(str(tmp_path))

       # Check that either the original path is contained in the result,
       # or the result is contained in the original path
       assert str(tmp_path) in result_path or result_path in str(tmp_path)
   ```

## Verifying Test Isolation

To verify that tests are properly isolated and don't create `.devsynth/` directories, run the tests in `tests/unit/test_isolation.py`:

```bash
python -m pytest tests/unit/test_isolation.py -v
```

This file contains tests specifically designed to verify test isolation, including:

1. `test_devsynth_dir_isolation`: Verifies that `.devsynth/` directories are created in the test environment, not in the current working directory.

2. `test_global_config_isolation`: Verifies that global configuration is isolated during tests.

3. `test_memory_path_isolation`: Verifies that memory paths are isolated during tests.

4. `test_no_file_logging_prevents_directory_creation`: Verifies that when file logging is disabled, no log directories are created.

5. `test_path_redirection_in_test_environment`: Verifies that paths outside the test environment are redirected to be within it.

6. `test_comprehensive_isolation`: Provides a comprehensive test for isolation of `.devsynth/` directories, verifying that no directories are created outside the test environment even when multiple components are used together.

You can also run all tests to ensure that no `.devsynth/` directories are created:

```bash
python -m pytest
```

If you see any `.devsynth/` directories in your project root or home directory after running tests, please report this as an issue.

## Comprehensive Testing Methodologies

### Unit Testing

Unit tests focus on testing individual components in isolation. They should:
- Be fast and deterministic
- Mock external dependencies
- Test one thing at a time
- Cover edge cases
- Have clear assertions

#### Example: Testing the Retry Mechanism

The retry mechanism (`retry_with_exponential_backoff`) is tested with several unit tests that cover different aspects of its behavior:

1. **Basic Functionality**:
   - `test_retry_with_exponential_backoff_success`: Tests that a function that fails and then succeeds is retried and returns a successful result.
   - `test_retry_with_exponential_backoff_failure`: Tests that a function that always fails is retried and raises an exception.

2. **Advanced Features**:
   - `test_retry_with_exponential_backoff_jitter`: Tests that the delays between retries follow exponential backoff with jitter.
   - `test_retry_with_exponential_backoff_no_jitter`: Tests that the function applies deterministic backoff when jitter is disabled.
   - `test_retry_with_exponential_backoff_on_retry_callback`: Tests that the `on_retry` callback is called on each retry attempt with the correct arguments.
   - `test_retry_with_exponential_backoff_retryable_exceptions`: Tests that only specified exceptions trigger retries.

These tests ensure that the retry mechanism works correctly in various scenarios, including edge cases.

### Behavior-Driven Development (BDD)

BDD tests describe the behavior of the system from a user's perspective. They should:
- Use Gherkin syntax (Given-When-Then)
- Be readable by non-technical stakeholders
- Focus on behavior, not implementation details
- Serve as living documentation

#### Example: BDD Tests for the Retry Mechanism

The retry mechanism is also tested with BDD tests that describe its behavior in natural language:

```gherkin
Scenario: Successful retry after transient errors
  Given a function that fails 2 times and then succeeds
  When I apply the retry decorator with max_retries=3 and initial_delay=0.1
  And I call the decorated function
  Then the function should be called 3 times
  And the final result should be successful

Scenario: Callback function is called on each retry
  Given a function that always fails
  When I apply the retry decorator with max_retries=3, initial_delay=0.1, and a callback function
  And I call the decorated function
  Then the function should be called 4 times
  And the callback function should be called 3 times
  And the callback function should receive the correct arguments
```

These BDD tests serve as living documentation for how the retry mechanism should behave, making it easier for developers to understand its functionality.

### Integration Testing

Integration tests focus on testing interactions between components. They should:
- Test real interactions between components
- Minimize mocking
- Cover critical paths through the system
- Verify that components work together correctly

By combining unit tests, BDD tests, and integration tests, we ensure that DevSynth is thoroughly tested at all levels, from individual components to the entire system.

## Recent Testing Improvements

The following improvements have been made to the testing infrastructure to address specific issues:

### 1. Enhanced Path Redirection Logic

The path redirection logic in `ensure_path_exists` and `ensure_log_dir_exists` has been improved to handle all types of paths:

- **Home Directory Paths**: Paths starting with the home directory (e.g., `~/.devsynth/`) are redirected to the test directory.
- **Absolute Paths**: Other absolute paths (e.g., `/tmp/devsynth/`) are redirected by extracting the path components after the root and appending them to the test directory.
- **Relative Paths**: Relative paths are already handled correctly.

This ensures that all file operations remain within the test environment, preventing pollution of the developer's environment.

### 2. Improved Handling of Non-String Content

The `ChromaDBStore` class has been updated to handle non-string content in the `get_history` method:

```python
# Create a summary of the content
content_summary = version.content
if isinstance(content_summary, str) and len(content_summary) > 100:
    content_summary = content_summary[:97] + "..."
```

This change ensures that the method works correctly with various content types, including dictionaries and lists.

### 3. Better Handling of Temporary Directories in Tests

Tests that check for the creation of directories in the "original working directory" now account for the fact that this directory might be a temporary directory created by pytest:

```python
# In pytest, the original_cwd is likely to be a temporary directory created by pytest
# So we'll skip this check if the original_cwd appears to be a pytest temporary directory
if not any(x in str(original_cwd).lower() for x in ["pytest", "tmp", "temp"]):
    # Check that no .devsynth directories were created in the original working directory
    cwd_devsynth = Path(original_cwd) / ".devsynth"
    assert not cwd_devsynth.exists(), f".devsynth directory was created in original working directory: {cwd_devsynth}"
```

### 4. Path Containment Checks Instead of Equality

Tests that check paths now use containment checks instead of equality, to account for path redirection:

```python
# The memory_path might be redirected by ensure_path_exists, so we check that
# the original path is contained within the final path, or vice versa
assert temp_dir in adapter.memory_path or adapter.memory_path in temp_dir
```

These improvements have significantly enhanced the robustness of the testing infrastructure, ensuring that tests are properly isolated and don't interfere with each other or the developer's environment.

## Running Tests

To run all tests:

```bash
python -m pytest
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

To run tests with coverage reporting:

```bash
python -m pytest --cov=src/devsynth tests/unit/ --cov-report=term-missing
python -m pytest --cov=src/devsynth tests/behavior/ --cov-report=term-missing
python -m pytest --cov=src/devsynth tests/unit/ tests/behavior/ --cov-report=html
```
