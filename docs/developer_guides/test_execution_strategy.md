---

author: DevSynth Team
date: '2025-07-31'
last_reviewed: "2025-07-31"
status: published
tags:
- testing
- development
- performance
title: Test Execution Strategy
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Test Execution Strategy
</div>

# Test Execution Strategy

This document outlines the test execution strategy for the DevSynth project, including how to run tests efficiently, categorize tests, and troubleshoot common issues.

## Overview

The DevSynth project has a comprehensive test suite with over 1,700 tests across multiple categories:

- **Unit Tests**: Tests for individual components in isolation
- **Integration Tests**: Tests for interactions between components
- **Behavior Tests**: BDD-style tests for user-facing features
- **Performance Tests**: Tests for performance characteristics
- **Property Tests**: Property-based tests for verifying invariants

To manage this large test suite efficiently, we've implemented a test execution strategy that includes:

1. **Test Parallelization**: Running tests in parallel to reduce execution time
2. **Test Categorization**: Categorizing tests by execution time and resource requirements
3. **Selective Execution**: Running specific subsets of tests based on development needs
4. **Isolation Handling**: Special handling for tests that require isolation

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

### Categorizing Tests

The `scripts/categorize_tests.py` script analyzes test execution times and adds appropriate markers:

```bash
# Analyze tests and generate timing report
python scripts/categorize_tests.py

# Preview changes without modifying files
python scripts/categorize_tests.py --dry-run

# Update test files with appropriate markers
python scripts/categorize_tests.py --update

# Analyze specific directory
python scripts/categorize_tests.py -d tests/unit
```

#### Available Options

- `-d, --directory DIR`: Directory containing tests to analyze (default: tests)
- `-o, --output FILE`: Output file for timing report (default: test_timing_report.json)
- `--dry-run`: Show changes without modifying files
- `--update`: Update test files with appropriate markers

## Test Categories and Markers

Tests in the DevSynth project are categorized using pytest markers:

### Speed Markers

- `@pytest.mark.fast`: Tests that execute in less than 1 second
- `@pytest.mark.medium`: Tests that execute between 1-5 seconds
- `@pytest.mark.slow`: Tests that execute in more than 5 seconds

### Resource Markers

- `@pytest.mark.isolation`: Tests that need to be run separately from other tests
- `@pytest.mark.requires_resource("resource_name")`: Tests requiring specific resources
- `@pytest.mark.requires_llm_provider`: Tests requiring an LLM provider

### Adding Markers to Tests

Markers can be added to tests manually:

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

Or automatically using the `categorize_tests.py` script.

## Best Practices

### Writing Efficient Tests

1. **Keep tests focused**: Each test should test one specific behavior
2. **Minimize dependencies**: Reduce dependencies on external resources when possible
3. **Use appropriate fixtures**: Use pytest fixtures for setup and teardown
4. **Mock external dependencies**: Use mocking to avoid network calls and other slow operations
5. **Add appropriate markers**: Mark tests with appropriate speed and resource markers

### Running Tests During Development

1. **Run fast tests frequently**: Use `devsynth run-pipeline -c fast` during active development
2. **Run specific tests**: Use `python -m pytest path/to/test_file.py::test_function` for specific tests
3. **Run related tests**: After making changes, run tests related to the changed code
4. **Run all tests before committing**: Use `devsynth run-pipeline` to run all tests before committing

### Pytest plugin discipline

Pytest 8 rejects duplicate plugin registrations, so keep all `pytest_plugins` exports in repository-root scope (for example, the top-level `conftest.py`) instead of scattering them across nested packages. When nested modules re-exported `pytest_bdd`, collection aborted with `ValueError: Plugin already registered` during fast+medium rehearsals.【F:logs/devsynth_run-tests_fast_medium_20251006T033632Z.log†L1-L84】 After hoisting the exports, both `pytest --collect-only -q` and the deselected safety net `pytest -k nothing --collect-only` finish cleanly, and their transcripts now act as regression commands for verifying plugin stability.【F:logs/pytest_collect_only_20251007.log†L1-L40】【F:logs/pytest_collect_only_20251006T043523Z.log†L1-L24】

## Troubleshooting

### Common Issues

#### Tests Taking Too Long

If tests are taking too long to run:

1. Use parallelization: `devsynth run-pipeline -p 8`
2. Run only fast tests: `devsynth run-pipeline -c fast`
3. Run only specific tests: `python -m pytest path/to/test_file.py`
4. Check for tests without speed markers: `python scripts/categorize_tests.py --dry-run`

#### Behavior Tests Not Being Collected

If behavior tests aren't being collected:

1. Check that feature files are in the correct location (`tests/behavior/features/`)
2. Verify that step definitions import the scenarios correctly:
   ```python
   from pytest_bdd import scenarios
   scenarios('../features/feature_name.feature')
   ```
3. Ensure step definitions match the steps in the feature file
4. Run with verbose output: `python -m pytest tests/behavior/ -v`

#### Tests Failing Due to Resource Issues

If tests are failing due to resource issues:

1. Check if tests need the isolation marker: `python scripts/categorize_tests.py`
2. Run isolation tests separately: `python -m pytest -m isolation`
3. Skip tests requiring specific resources: `python -m pytest -m "not requires_llm_provider"`

## Continuous Integration

The test execution strategy is integrated with our CI/CD pipeline:

1. **Fast Tests**: Run on every push and pull request
2. **All Tests**: Run on merge to main branch
3. **Performance Tests**: Run on a schedule (nightly)

The CI pipeline uses the same scripts and categorization as local development, ensuring consistency between environments.

## Future Improvements

Planned improvements to the test execution strategy:

1. **Test Sharding**: Distribute tests across multiple CI jobs
2. **Test Prioritization**: Run tests most likely to fail first
3. **Test Impact Analysis**: Only run tests affected by changes
4. **Test Flakiness Detection**: Identify and fix flaky tests

## Conclusion

By following this test execution strategy, we can efficiently run our large test suite, identify issues quickly, and maintain a high level of code quality. The combination of test parallelization, categorization, and selective execution allows developers to run the right tests at the right time, improving productivity and code quality.
