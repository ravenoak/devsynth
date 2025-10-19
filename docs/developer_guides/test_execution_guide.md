---

author: DevSynth Team
date: '2025-07-31'
last_reviewed: "2025-07-31"
status: published
tags:
- testing
- development
- performance
title: Test Execution Guide
version: "0.1.0-alpha.1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Test Execution Guide
</div>

# DevSynth Test Execution Guide

This guide provides practical strategies for efficiently running and managing tests in the DevSynth project. It covers various approaches for test execution, performance optimization, and test metrics reporting.

## Test Suite Overview

The DevSynth project has a comprehensive test suite with approximately 1,728 tests across multiple categories:

- **Unit Tests**: Tests for individual components in isolation
- **Integration Tests**: Tests for interactions between components
- **Behavior Tests**: BDD-style tests for user-facing features
- **Performance Tests**: Tests for performance characteristics
- **Property Tests**: Property-based tests for verifying invariants

Tests are also categorized by execution time:

- **Fast**: Tests that execute in less than 1 second
- **Medium**: Tests that execute between 1-5 seconds
- **Slow**: Tests that execute in more than 5 seconds

## Test Execution Scripts

### Running Tests with Parallelization

The `devsynth run-pipeline` command provides a flexible way to run tests with parallelization:

```bash
# Run all tests with default parallelization (4 processes)
devsynth run-pipeline

# Run unit tests with 8 parallel processes
devsynth run-pipeline -p 8 -c unit

# Run fast tests only
devsynth run-pipeline -c fast

# Run tests with specific markers
devsynth run-pipeline -m "not requires_llm_provider"

# Run tests with coverage reporting
devsynth run-pipeline --coverage
```

#### Available Options

- `-p, --parallel NUM`: Number of parallel processes (default: 4)
- `-c, --category CATEGORY`: Test category to run (default: all)
- `-m, --markers MARKERS`: Additional pytest markers
- `-v, --verbose`: Enable verbose output
- `--coverage`: Generate coverage report

#### Available Categories

- `all`: All tests (non-isolation tests in parallel, isolation tests sequentially)
- `unit`: Unit tests only
- `integration`: Integration tests only
- `behavior`: Behavior tests only
- `performance`: Performance tests only (run sequentially)
- `property`: Property tests only
- `fast`: Tests marked as fast (execution time < 1s)
- `medium`: Tests marked as medium speed (execution time 1-5s)
- `slow`: Tests marked as slow (execution time > 5s)

### Test Metrics Reporting

The `devsynth test-metrics` command generates comprehensive reports on the test suite status:

```bash
# Generate a basic test metrics report
devsynth test-metrics

# Generate an HTML report
devsynth test-metrics --html

# Skip coverage calculation for faster execution
devsynth test-metrics --skip-coverage

# Analyze only unit tests
devsynth test-metrics --category unit

# Analyze only fast tests
devsynth test-metrics --speed fast

# Run tests to identify failures
devsynth test-metrics --run-tests
```

#### Available Options

- `-o, --output FILENAME`: Output file for the report (default: test_metrics_report.json)
- `--run-tests`: Run tests to identify failures (otherwise just counts tests)
- `--html`: Generate an HTML report in addition to JSON
- `--skip-coverage`: Skip coverage calculation (faster)
- `--category CATEGORY`: Only analyze tests in the specified category
- `--speed SPEED`: Only analyze tests with the specified speed marker

### Fixing Behavior Test Collection

If you encounter issues with behavior test collection, use the `scripts/fix_behavior_tests.py` script:

```bash
# Preview changes without modifying files
python scripts/fix_behavior_tests.py --dry-run

# Fix behavior test collection issues
python scripts/fix_behavior_tests.py
```

This script addresses several issues with behavior test collection:
1. Duplicate feature files in different locations
2. Inconsistent scenario loading approaches
3. Missing scenario imports in step definition files

## Efficient Test Execution Strategies

### During Active Development

During active development, you should focus on running fast, relevant tests:

1. **Run specific tests**: When working on a specific component, run only the tests for that component:
   ```bash
   python -m pytest path/to/test_file.py::test_function
   ```

2. **Run fast tests**: Run only fast tests to get quick feedback:
   ```bash
   devsynth run-pipeline -c fast
   ```

3. **Skip slow dependencies**: Skip tests that require slow dependencies:
   ```bash
   devsynth run-pipeline -m "not requires_llm_provider"
   ```

### Before Committing Changes

Before committing changes, you should run a more comprehensive test suite:

1. **Run all tests for the modified component**:
   ```bash
   devsynth run-pipeline -c unit -m "component_name"
   ```

2. **Run integration tests** that involve the modified component:
   ```bash
   devsynth run-pipeline -c integration -m "component_name"
   ```

3. **Run behavior tests** for user-facing features:
   ```bash
   devsynth run-pipeline -c behavior
   ```

### In Continuous Integration

In CI environments, you should run the full test suite with parallelization:

1. **Run all tests**:
   ```bash
   devsynth run-pipeline -p 8
   ```

2. **Generate test metrics report**:
   ```bash
   devsynth test-metrics --html --run-tests
   ```

## Test Performance Optimization

### Test Categorization

Tests should be categorized by execution time using the appropriate markers:

```python
import pytest

@pytest.mark.fast
def test_simple_function():
    # Test implementation
    assert 1 + 1 == 2

@pytest.mark.slow
@pytest.mark.requires_llm_provider
def test_complex_function():
    # Test implementation that requires an LLM provider
    assert complex_function() == expected_result
```

You can use the `scripts/categorize_tests.py` script to automatically categorize tests based on execution time:

```bash
# Analyze tests and generate timing report
python scripts/categorize_tests.py

# Preview changes without modifying files
python scripts/categorize_tests.py --dry-run

# Update test files with appropriate markers
python scripts/categorize_tests.py --update
```

### Test Isolation

Tests that modify global state or have side effects should be marked with the `isolation` marker:

```python
@pytest.mark.isolation
def test_function_with_side_effects():
    # Test implementation that modifies global state
    pass
```

These tests will be run sequentially to avoid interference.

### Mocking External Dependencies

Tests should mock external dependencies to avoid network calls and other slow operations:

```python
@pytest.mark.fast
def test_function_with_mocked_dependency(mocker):
    # Mock the dependency
    mocker.patch('module.dependency', return_value='mocked_result')

    # Test implementation
    assert function_under_test() == 'expected_result'
```

## Troubleshooting

### Common Issues

#### Tests Taking Too Long

If tests are taking too long to run:

1. Use parallelization: `devsynth run-pipeline -p 8`
2. Run only fast tests: `devsynth run-pipeline -c fast`
3. Run only specific tests: `python -m pytest path/to/test_file.py`
4. Skip coverage calculation: `devsynth test-metrics --skip-coverage`

#### Behavior Tests Not Being Collected

If behavior tests aren't being collected:

1. Run the fix script: `python scripts/fix_behavior_tests.py`
2. Check that feature files are in the correct location (`tests/behavior/features/`)
3. Verify that step definitions import the scenarios correctly
4. Run with verbose output: `python -m pytest tests/behavior/ -v`

#### Tests Failing Due to Resource Issues

If tests are failing due to resource issues:

1. Check if tests need the isolation marker: `python scripts/categorize_tests.py`
2. Run isolation tests separately: `python -m pytest -m isolation`
3. Skip tests requiring specific resources: `python -m pytest -m "not requires_llm_provider"`

## Best Practices

1. **Keep tests focused**: Each test should test one specific behavior
2. **Minimize dependencies**: Reduce dependencies on external resources when possible
3. **Use appropriate fixtures**: Use pytest fixtures for setup and teardown
4. **Add appropriate markers**: Mark tests with appropriate speed and resource markers
5. **Run relevant tests**: Run tests related to the code you're changing
6. **Monitor test metrics**: Regularly generate test metrics reports to track progress

## Conclusion

By following these test execution strategies, you can efficiently run and manage tests in the DevSynth project. The combination of test parallelization, categorization, and selective execution allows you to run the right tests at the right time, improving productivity and code quality.
