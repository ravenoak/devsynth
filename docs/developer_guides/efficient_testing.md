---
title: "Efficient Testing Guide"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Efficient Testing Guide

This guide provides information on how to efficiently run and manage tests in the DevSynth project. It covers the testing infrastructure, test categorization, performance optimization techniques, and best practices.

## Table of Contents

- [Testing Infrastructure Overview](#testing-infrastructure-overview)
- [Running Tests Efficiently](#running-tests-efficiently)
- [Test Categorization](#test-categorization)
- [Performance Optimization Techniques](#performance-optimization-techniques)
- [Test Metrics and Reporting](#test-metrics-and-reporting)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Testing Infrastructure Overview

DevSynth uses a comprehensive testing approach that combines multiple testing strategies:

- **Unit Testing**: Testing individual components in isolation
- **Integration Testing**: Testing the interaction between multiple components
- **Behavior-Driven Development (BDD)**: Using Gherkin syntax to define features and scenarios
- **Property-Based Testing**: Using hypothesis testing to verify properties of functions

The test directory structure is organized as follows:

```text
tests/
├── conftest.py              # Global test fixtures and configuration
├── behavior/                # Behavior-driven (BDD) tests
│   ├── features/            # Feature files in Gherkin syntax
│   └── steps/               # Step definitions for BDD scenarios
├── integration/             # Integration tests
├── property/                # Property-based tests
└── unit/                    # Unit tests
```

## Running Tests Efficiently

### Using the `devsynth run-pipeline` Command

The `devsynth run-pipeline` command provides a convenient way to run tests with various options for performance optimization:

```bash
# Run all tests
devsynth run-pipeline

# Run only unit tests
devsynth run-pipeline --unit

# Run only fast tests
devsynth run-pipeline --fast

# Run only unit tests that are fast
devsynth run-pipeline --unit --fast

# Run tests with segmentation for better performance
devsynth run-pipeline --segment

# Disable parallel execution
devsynth run-pipeline --no-parallel

# Generate HTML report
devsynth run-pipeline --report
```

### Command-line Options

The `devsynth run-pipeline` command supports the following options:

| Option | Description |
|--------|-------------|
| `--unit` | Run only unit tests |
| `--integration` | Run only integration tests |
| `--behavior` | Run only behavior tests |
| `--all` | Run all tests (default) |
| `--fast` | Run only fast tests (execution time < 1s) |
| `--medium` | Run only medium tests (execution time between 1s and 5s) |
| `--slow` | Run only slow tests (execution time > 5s) |
| `--report` | Generate HTML report |
| `--verbose` | Show verbose output |
| `--no-parallel` | Disable parallel test execution |
| `--segment` | Run tests in smaller batches to improve performance |
| `--segment-size SIZE` | Number of tests per batch when using --segment (default: 50) |

### Examples

Here are some common use cases:

```bash
# Run fast tests during development
devsynth run-pipeline --fast

# Run all unit tests with segmentation
devsynth run-pipeline --unit --segment

# Run behavior tests with verbose output
devsynth run-pipeline --behavior --verbose

# Run all tests and generate a report
devsynth run-pipeline --all --report
```

## Test Categorization

Tests are categorized by speed to allow for more efficient test execution:

- **Fast Tests**: Execution time < 1 second
- **Medium Tests**: Execution time between 1-5 seconds
- **Slow Tests**: Execution time > 5 seconds

For a comprehensive guide on test categorization, including the current status and schedule for categorizing remaining tests, see the [Test Categorization Guide](test_categorization_guide.md).

### Categorizing Tests

Tests can be categorized using the `categorize_tests.py` script:

```bash
# Analyze all tests and add appropriate markers
python scripts/categorize_tests.py --update

# Analyze only unit tests
python scripts/categorize_tests.py --directory tests/unit --update

# Show changes without modifying files
python scripts/categorize_tests.py --dry-run

# Use custom thresholds for categorization
python scripts/categorize_tests.py --fast-threshold 0.5 --medium-threshold 3.0 --update

# Run tests in batches for better performance
python scripts/categorize_tests.py --batch-size 50 --update
```

### Command-line Options

The `categorize_tests.py` script supports the following options:

| Option | Description |
|--------|-------------|
| `-d, --directory` | Directory containing tests to analyze (default: tests) |
| `-o, --output` | Output file for timing report (default: test_timing_report.json) |
| `--dry-run` | Show changes without modifying files |
| `--update` | Update test files with appropriate markers |
| `--batch-size` | Number of tests to run in each batch (default: 100) |
| `--skip-benchmarks` | Skip running benchmarks (use existing timing report) |
| `--fast-threshold` | Threshold for fast tests in seconds (default: 1.0) |
| `--medium-threshold` | Threshold for medium tests in seconds (default: 5.0) |
| `--category` | Only analyze tests in the specified category |

### Adding Speed Markers Manually

You can also add speed markers manually to your tests:

```python
import pytest

@pytest.mark.fast
def test_fast_operation():
    # This test should complete in less than 1 second
    assert 1 + 1 == 2

@pytest.mark.medium
def test_medium_operation():
    # This test should complete in 1-5 seconds
    assert 2 + 2 == 4

@pytest.mark.slow
def test_slow_operation():
    # This test might take more than 5 seconds
    assert 3 + 3 == 6
```

## Performance Optimization Techniques

### Parallel Test Execution

Tests can be run in parallel using pytest-xdist, which is enabled by default in the `devsynth run-pipeline` command. To disable parallel execution, use the `--no-parallel` option.

### Test Segmentation

For large test suites, running tests in smaller batches can improve performance and reduce memory usage. Use the `--segment` option to enable test segmentation:

```bash
devsynth run-pipeline --segment
```

You can control the batch size using the `--segment-size` option:

```bash
devsynth run-pipeline --segment --segment-size 20
```

### Balanced Test Distribution

For optimal performance when running tests in parallel, use the `run_balanced_tests.py` script, which intelligently distributes tests across processes based on their execution time:

```bash
python scripts/run_balanced_tests.py
```

This script uses a bin packing algorithm to create balanced segments, ensuring that each process has a similar workload. Options include:

```bash
# Run with a specific number of processes
python scripts/run_balanced_tests.py --processes 4

# Run only unit tests
python scripts/run_balanced_tests.py --category unit

# Generate an HTML report
python scripts/run_balanced_tests.py --report
```

### Running Modified Tests

#### Basic Incremental Testing

To run only tests affected by recent changes, use the `run_modified_tests.py` script:

```bash
python scripts/run_modified_tests.py
```

This script identifies modified files using git diff, determines which tests might be affected by those changes, and runs only those tests. Options include:

```bash
# Compare against a specific commit
python scripts/run_modified_tests.py --base HEAD~5

# Run all tests for modified files, not just affected tests
python scripts/run_modified_tests.py --all-tests

# Run in parallel
python scripts/run_modified_tests.py --parallel
```

#### Enhanced Incremental Testing

For more advanced incremental testing with improved accuracy and performance, use the enhanced version:

```bash
python scripts/run_modified_tests_enhanced.py
```

The enhanced version provides several improvements:
- Integration with test_utils_extended.py for more accurate test collection and marker verification
- Test prioritization based on failure history
- Support for balanced distribution of tests across processes
- Ability to limit the number of tests to run
- Recording of test results for future prioritization

Options include:

```bash
# Prioritize tests based on failure history
python scripts/run_modified_tests_enhanced.py --prioritize

# Use balanced distribution for parallel execution
python scripts/run_modified_tests_enhanced.py --balanced

# Run only fast tests
python scripts/run_modified_tests_enhanced.py --fast

# Limit the number of tests to run
python scripts/run_modified_tests_enhanced.py --max-tests 100
```

#### Preset-based Incremental Testing

For common incremental testing scenarios, use the preset-based runner:

```bash
python scripts/run_incremental_tests_enhanced.py
```

This script provides several presets for different testing scenarios:

- **recent**: Run tests for files modified in the last commit
- **sprint**: Run tests for files modified in the current sprint (last 5 commits)
- **feature**: Run tests for files modified in the current feature branch
- **interface**: Run interface tests for modified files
- **fast**: Run only fast tests for modified files (quick feedback)
- **all**: Run all tests for modified files

Options include:

```bash
# Use a specific preset
python scripts/run_incremental_tests_enhanced.py --preset fast

# Override the base commit
python scripts/run_incremental_tests_enhanced.py --base HEAD~3

# Show what would be run without executing tests
python scripts/run_incremental_tests_enhanced.py --dry-run
```

### Test Prioritization

To run tests in order of their likelihood to fail, use the `prioritize_tests.py` script:

```bash
python scripts/prioritize_tests.py
```

This script tracks test failures and uses that information to prioritize tests, running tests that are more likely to fail first. Options include:

```bash
# Run only the top 100 most likely to fail tests
python scripts/prioritize_tests.py --top 100

# Run only unit tests
python scripts/prioritize_tests.py --category unit

# Reset the failure history
python scripts/prioritize_tests.py --reset
```

### Unified Test Execution Workflow

For a comprehensive solution that combines all the test execution features, use the unified test execution workflow:

```bash
python scripts/run_unified_tests.py
```

This script provides a unified interface for running tests with optimal performance, combining:
- Incremental testing (run only tests affected by recent changes)
- Balanced distribution (distribute tests evenly across processes)
- Test prioritization (run tests most likely to fail first)
- Test categorization (run tests based on speed markers)
- Test filtering (run tests matching specific patterns)

The script supports several execution modes:

- **incremental**: Run only tests affected by recent changes
- **balanced**: Run tests with balanced distribution across processes
- **all**: Run all tests
- **fast**: Run only fast tests for quick feedback
- **critical**: Run tests most likely to fail based on history

Options include:

```bash
# Select a specific execution mode
python scripts/run_unified_tests.py --mode fast

# Compare against a specific commit for incremental mode
python scripts/run_unified_tests.py --base HEAD~3

# Run only tests in a specific category
python scripts/run_unified_tests.py --category unit

# Run only tests with a specific speed marker
python scripts/run_unified_tests.py --speed fast

# Run only tests matching a specific pattern
python scripts/run_unified_tests.py --pattern "test_auth"

# Prioritize tests based on failure history
python scripts/run_unified_tests.py --prioritize

# Run tests in parallel
python scripts/run_unified_tests.py --parallel

# Generate an HTML report
python scripts/run_unified_tests.py --report

# Show what would be run without executing tests
python scripts/run_unified_tests.py --dry-run
```

The unified test execution workflow also displays test statistics, including marker coverage and frequently failing tests, to help you understand the state of your test suite.

### Caching

All test scripts use aggressive caching to avoid re-collecting and re-running tests unnecessarily. The cache is stored in the `.test_cache` directory.

To disable caching and always collect fresh data:

```bash
devsynth run-pipeline --no-cache
```

The `test_utils.py` module provides common caching functionality for all test scripts, including:

- Caching test collection results (valid for 1 hour)
- Caching test execution times (valid for 24 hours)
- Caching test failure history

### Improved Test Categorization

The `categorize_tests_improved.py` script provides better benchmarking and error handling for categorizing tests by speed:

```bash
python scripts/categorize_tests_improved.py
```

This script runs tests to measure their execution time, then adds appropriate markers (fast, medium, slow) based on the results. Options include:

```bash
# Update test files with appropriate markers
python scripts/categorize_tests_improved.py --update

# Show changes without modifying files
python scripts/categorize_tests_improved.py --dry-run

# Set custom thresholds for categorization
python scripts/categorize_tests_improved.py --fast-threshold 0.5 --medium-threshold 3.0
```

## Test Metrics and Reporting

The `devsynth test-metrics` command provides comprehensive metrics on the test suite:

```bash
# Generate a basic metrics report
devsynth test-metrics

# Generate an HTML report
devsynth test-metrics --html

# Run tests to identify failures
devsynth test-metrics --run-tests

# Skip coverage calculation for faster execution
devsynth test-metrics --skip-coverage

# Analyze only a specific category
devsynth test-metrics --category unit

# Analyze only tests with a specific speed marker
devsynth test-metrics --speed fast
```

### Command-line Options

The `devsynth test-metrics` command supports the following options:

| Option | Description |
|--------|-------------|
| `-o, --output` | Output file for the report (default: test_metrics_report.json) |
| `--run-tests` | Run tests to identify failures |
| `--html` | Generate an HTML report in addition to JSON |
| `--skip-coverage` | Skip coverage calculation (faster) |
| `--category` | Only analyze tests in the specified category |
| `--speed` | Only analyze tests with the specified speed marker |
| `--no-parallel` | Disable parallel test execution |
| `--no-cache` | Disable caching (always collect fresh data) |
| `--segment` | Run tests in smaller batches to improve performance |
| `--segment-size` | Number of tests per batch when using --segment (default: 50) |
| `--clear-cache` | Clear all cached data before running |

## Best Practices

### Writing Efficient Tests

1. **Keep tests focused**: Each test should test one specific behavior or functionality.
2. **Minimize setup and teardown**: Use fixtures to share setup and teardown code.
3. **Avoid unnecessary I/O**: Mock external dependencies to avoid network or file system operations.
4. **Use appropriate speed markers**: Categorize tests based on their execution time.
5. **Isolate tests**: Ensure tests don't depend on the state from other tests.

### Running Tests During Development

1. **Use the unified test execution workflow**: Use `run_unified_tests.py` with the `--mode fast` option for the most efficient testing experience.
2. **Run incremental tests**: Use `run_incremental_tests_enhanced.py --preset fast` to run only fast tests affected by recent changes.
3. **Run specific test types**: Use `--category unit`, `--category integration`, or `--category behavior` to run only specific test types.
4. **Use balanced distribution**: Enable the `--balanced` option when running tests in parallel to ensure optimal resource utilization.
5. **Prioritize tests**: Use the `--prioritize` option to run tests that are more likely to fail first.
6. **Limit test execution**: Use `--max-tests` to limit the number of tests run during development.
7. **Skip coverage calculation**: Use `--skip-coverage` to speed up test metrics generation.

### Continuous Integration

1. **Use the unified test execution workflow**: Configure CI pipelines to use `run_unified_tests.py` for optimal test execution.
2. **Run tests in stages**: Use different modes for different CI stages:
   - **Fast mode**: Run `run_unified_tests.py --mode fast` for quick feedback in early stages
   - **Critical mode**: Run `run_unified_tests.py --mode critical` to catch likely failures early
   - **Incremental mode**: Run `run_unified_tests.py --mode incremental` for PR validation
   - **All mode**: Run `run_unified_tests.py --mode all` for comprehensive testing before merging
3. **Use balanced distribution**: Enable the `--balanced` option to optimize resource utilization in CI environments.
4. **Generate reports**: Use `--report` to generate HTML reports for test results.
5. **Split the test suite**: Configure multiple CI jobs for different test categories:
   - Unit tests job: `run_unified_tests.py --category unit`
   - Integration tests job: `run_unified_tests.py --category integration`
   - Behavior tests job: `run_unified_tests.py --category behavior`
6. **Track test history**: Ensure test results are recorded to improve prioritization in future runs.

## Troubleshooting

### Common Issues

1. **Tests take too long to run**:
   - Use `--fast` to run only fast tests
   - Enable segmentation with `--segment`
   - Run only specific test types with `--unit`, `--integration`, or `--behavior`

2. **Memory issues**:
   - Use segmentation with `--segment` to run tests in smaller batches
   - Reduce the segment size with `--segment-size`

3. **Behavior test collection issues**:
   - Run the `fix_behavior_tests.py` script to standardize feature file locations
   - Ensure all step definition files import scenarios correctly

4. **Test categorization issues**:
   - Run the `categorize_tests.py` script with `--update` to apply speed markers
   - Check the timing report to see how tests are categorized

### Getting Help

If you encounter issues not covered in this guide, please:

1. Check the [Troubleshooting Guide](/docs/getting_started/troubleshooting.md) for common issues and solutions
2. Review the [FAQ](/docs/getting_started/faq.md) for answers to frequently asked questions
3. Open an issue on GitHub if you encounter a bug or have a feature request

---

_Last updated: August 1, 2025_
