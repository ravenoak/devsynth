---
title: "Test Best Practices Guide"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Test Best Practices Guide

## Introduction

This guide outlines best practices for writing and maintaining tests in the DevSynth project. Following these practices will help ensure tests are reliable, maintainable, and provide good coverage of the codebase.

## General Principles

1. **Test Independence**: Each test should be independent and not rely on the state created by other tests.
2. **Deterministic Tests**: Tests should produce the same result every time they are run.
3. **Fast Tests**: Tests should run quickly to enable rapid feedback during development.
4. **Readable Tests**: Tests should be easy to understand and maintain.
5. **Comprehensive Tests**: Tests should cover all important functionality, including edge cases.

## Test Structure

### Test Organization

- Organize tests by type (unit, integration, behavior) and then by module/component.
- Use descriptive test names that clearly indicate what is being tested.
- Include the ReqID in the test docstring if the test is related to a specific requirement.

### Test Fixtures

- Use fixtures to set up test dependencies and clean up after tests.
- Prefer function-scoped fixtures for better isolation.
- Use parametrized tests to test multiple scenarios with the same test function.

### Test Markers

- Use markers to categorize tests by speed (fast, medium, slow) and resource requirements.
- Add markers to all tests to enable selective test execution.
- Follow the standard marker placement convention to avoid duplicate counting.

## Mocking and Patching

### Robust Mocking Approaches

When mocking components that involve iteration or complex behavior, use a more robust approach:

```python
# Avoid this approach (prone to iterator exhaustion)
answers = iter(["answer1", "answer2"])
monkeypatch.setattr("module.function", lambda *a, **k: next(answers))

# Use this approach instead (more robust)
answers = ["answer1", "answer2"]
answer_index = 0

def mock_function(*args, **kwargs):
    nonlocal answer_index
    if answer_index < len(answers):
        result = answers[answer_index]
        answer_index += 1
        return result
    return "default"  # Provide a default value if we run out of answers

monkeypatch.setattr("module.function", mock_function)
```

### Mock Classes

For complex interfaces, create dedicated mock classes:

```python
class RobustMockBridge(UXBridge):
    """Mock implementation of UXBridge with robust error handling."""

    def __init__(self, answers, confirms):
        self.answers = list(answers)
        self.confirms = list(confirms)
        self.messages = []
        self.answer_index = 0
        self.confirm_index = 0

    def ask_question(self, *args, **kwargs):
        if self.answer_index < len(self.answers):
            answer = self.answers[self.answer_index]
            self.answer_index += 1
            return answer
        return ""  # Default answer if we run out

    def confirm_choice(self, *args, **kwargs):
        if self.confirm_index < len(self.confirms):
            confirm = self.confirms[self.confirm_index]
            self.confirm_index += 1
            return confirm
        return False  # Default confirmation if we run out

    def display_result(self, message, **kwargs):
        self.messages.append(message)
```

## File System Operations

### Temporary Directories

- Use pytest's `tmp_path` fixture for file system operations.
- Ensure directories exist before attempting to write to them.
- Clean up temporary files and directories after tests.

```python
def test_file_operations(tmp_path):
    # Ensure directory exists
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir(exist_ok=True)

    # Perform file operations
    test_file = test_dir / "test_file.txt"
    test_file.write_text("test content")

    # Assert file exists and has expected content
    assert test_file.exists()
    assert test_file.read_text() == "test content"
```

## Asynchronous Testing

### Testing Async Functions

- Use `pytest.mark.asyncio` to test async functions.
- Use `asyncio.run()` for running async code in synchronous tests.

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result == expected_result

def test_async_function_from_sync():
    async def run_test():
        result = await my_async_function()
        assert result == expected_result

    asyncio.run(run_test())
```

## Error Handling

### Testing Error Cases

- Test both success and error cases.
- Use `pytest.raises` to test that exceptions are raised when expected.
- Verify the exception message when appropriate.

```python
def test_error_handling():
    with pytest.raises(ValueError) as excinfo:
        function_that_raises_error()
    assert "Expected error message" in str(excinfo.value)
```

## Test Data

### Test Data Management

- Use small, focused test data sets.
- Avoid hardcoding large data structures in test files.
- Use fixtures or factory functions to generate test data.

```python
@pytest.fixture
def sample_data():
    return {
        "id": "test-id",
        "name": "Test Name",
        "values": [1, 2, 3]
    }

def test_with_data(sample_data):
    result = process_data(sample_data)
    assert result["processed"] == True
```

## Common Pitfalls and Solutions

### Iterator Exhaustion

**Problem**: Using iterators in test mocks can lead to StopIteration errors if the code under test makes more calls than expected.

**Solution**: Use lists with indices instead of iterators, and provide default values for when indices go out of range.

### Inconsistent Test Environment

**Problem**: Tests may pass locally but fail in CI due to differences in the environment.

**Solution**: Use environment-agnostic approaches, such as temporary directories and mocking external dependencies.

### Slow Tests

**Problem**: Tests that are too slow can hinder development and CI/CD processes.

**Solution**:
- Mark tests with appropriate speed markers (fast, medium, slow).
- Use mocks for external dependencies.
- Optimize test setup and teardown.

### Flaky Tests

**Problem**: Tests that sometimes pass and sometimes fail without code changes.

**Solution**:
- Identify and eliminate sources of non-determinism.
- Add appropriate waits or retries for asynchronous operations.
- Ensure proper cleanup between tests.

## Test Debugging

### Debugging Failed Tests

1. Run the failing test in isolation with verbose output:
   ```text
   pytest path/to/test.py::test_name -v
   ```

2. Add print statements or use pytest's `-s` flag to see output:
   ```text
   pytest path/to/test.py::test_name -s
   ```

3. Use pytest's `--pdb` flag to drop into the debugger on failure:
   ```text
   pytest path/to/test.py::test_name --pdb
   ```

4. Check for test interdependencies by running tests in random order:
   ```text
   pytest path/to/test.py --random-order
   ```

## Conclusion

Following these best practices will help ensure that tests in the DevSynth project are reliable, maintainable, and effective at catching regressions. Remember that tests are a critical part of the codebase and should be treated with the same care and attention as production code.
