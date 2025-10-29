---
title: "Comprehensive Test Execution Guide"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "developer-guide"
  - "guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Comprehensive Test Execution Guide

This guide provides detailed instructions and best practices for efficiently executing tests in the DevSynth project. It covers test categorization, prioritization, filtering, and parallel execution to help you run tests more effectively.

## Table of Contents

- [Overview](#overview)
- [Test Infrastructure](#test-infrastructure)
- [Test Categorization](#test-categorization)
- [Test Prioritization](#test-prioritization)
- [Efficient Test Execution](#efficient-test-execution)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Reference](#reference)

## Overview

DevSynth has a large test suite with over 2,700 tests across various categories. Running all tests can be time-consuming, so we've implemented several tools and strategies to make test execution more efficient:

1. **Test Categorization**: Tests are categorized by speed (fast, medium, slow) to allow running only tests of a certain speed.
2. **Test Prioritization**: Tests are prioritized based on risk factors to focus on tests that are more likely to fail.
3. **Parallel Execution**: Tests can be run in parallel across multiple processes for faster execution.
4. **Incremental Testing**: Only tests affected by recent changes can be run to save time.
5. **Distributed Execution**: Tests can be distributed across multiple processes with load balancing.

## Test Infrastructure

The DevSynth test infrastructure consists of several components:

### Test Categories

- **Unit Tests**: Located in `tests/unit/`, these test individual components in isolation.
- **Integration Tests**: Located in `tests/integration/`, these test interactions between components.
- **Behavior Tests**: Located in `tests/behavior/`, these use Gherkin syntax to define features and scenarios.
- **Performance Tests**: Located in `tests/performance/`, these test performance characteristics.
- **Property Tests**: Located in `tests/property/`, these use hypothesis testing to verify properties.

### Speed Categories

Tests are categorized by speed to allow for more efficient test execution:

- **Fast Tests**: Execute in less than 1 second. Ideal for running frequently during development.
- **Medium Tests**: Execute between 1-5 seconds. Provide a good balance between coverage and execution time.
- **Slow Tests**: Execute in more than 5 seconds. Typically integration or behavior tests that involve multiple components.

### Test Scripts

The following scripts are available for test execution:

- **devsynth run-pipeline**: Runs tests by category and speed.
- **enhanced_test_categorization.py**: Categorizes tests by speed based on execution time.
- **prioritize_high_risk_tests.py**: Identifies and runs high-risk tests based on multiple factors.
- **reconcile_test_counts.py**: Reconciles test counts across different sources.
- **distributed_test_runner_enhanced.py**: Runs tests in parallel with load balancing.
- **fix_test_markers.py**: Fixes marker placement issues in test files.
- **common_test_collector.py**: Provides a unified interface for collecting tests.

## Test Categorization

### Understanding Test Speed Categories

Tests are categorized by speed to allow for more efficient test execution:

- **Fast Tests** (`@pytest.mark.fast`): Execute in less than 1 second.
- **Medium Tests** (`@pytest.mark.medium`): Execute between 1-5 seconds.
- **Slow Tests** (`@pytest.mark.slow`): Execute in more than 5 seconds.

### Categorizing Tests

You can categorize tests using the `enhanced_test_categorization.py` script:

```bash
# Categorize tests in a specific module
python scripts/enhanced_test_categorization.py --module tests/unit/application/cli --update

# Categorize tests with priority for high-priority modules
python scripts/enhanced_test_categorization.py --priority --update

# Limit the number of tests categorized in a single run
python scripts/enhanced_test_categorization.py --max-tests 50 --update

# Generate a categorization report
python scripts/enhanced_test_categorization.py --report --update

# Fix marker placement issues after categorization
python scripts/enhanced_test_categorization.py --fix-markers --update
```

### Checking Test Categorization Status

You can check the current categorization status using the `common_test_collector.py` script:

```bash
# Get test counts by category
python scripts/common_test_collector.py --count

# Get marker counts
python scripts/common_test_collector.py --marker-counts

# List tests with a specific marker
python scripts/common_test_collector.py --list-marked-tests --marker-type medium
```

### Reconciling Test Counts

If you notice discrepancies in test counts across different sources, you can use the `reconcile_test_counts.py` script:

```bash
# Analyze discrepancies without making changes
python scripts/reconcile_test_counts.py --analyze

# Update documentation files with accurate counts
python scripts/reconcile_test_counts.py --update-docs

# Update tracking files with accurate counts
python scripts/reconcile_test_counts.py --update-tracking

# Update both documentation and tracking files
python scripts/reconcile_test_counts.py --update-all
```

## Test Prioritization

### Understanding Risk Factors

The `prioritize_high_risk_tests.py` script identifies high-risk tests based on multiple factors:

1. **Historical Failure Rates**: Tests that failed recently are more likely to fail again.
2. **Code Complexity**: More complex tests are more likely to fail.
3. **Recent Changes**: Tests affected by recent code changes are more likely to fail.
4. **Dependencies**: Tests that depend on components with high failure rates are more likely to fail.

### Running High-Risk Tests

You can run high-risk tests using the `prioritize_high_risk_tests.py` script:

```bash
# Run high-risk tests in a specific module
python scripts/prioritize_high_risk_tests.py --module tests/unit/application/cli

# Run only the top 50 highest-risk tests
python scripts/prioritize_high_risk_tests.py --limit 50

# Run tests with a minimum risk score of 70
python scripts/prioritize_high_risk_tests.py --min-risk 70

# Update test history with new results
python scripts/prioritize_high_risk_tests.py --update-history

# Generate a detailed risk report
python scripts/prioritize_high_risk_tests.py --report

# Show tests that would be run without running them
python scripts/prioritize_high_risk_tests.py --dry-run
```

### Interpreting Risk Reports

The risk report generated by `prioritize_high_risk_tests.py` includes:

- **Overall Risk Score**: A score from 0-100 indicating the overall risk of a test.
- **Risk Factors**: Individual risk factors (failure history, code complexity, recent changes, dependencies).
- **Test Results**: Whether the test passed or failed and its execution time.
- **Summary Statistics**: Total tests, high/medium/low risk tests, pass rate.

## Efficient Test Execution

### Running Tests by Category and Speed

You can run tests by category and speed using the `devsynth run-pipeline` command:

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
```

### Parallel Test Execution

You can run tests in parallel using the `distributed_test_runner_enhanced.py` script:

```bash
# Run tests in parallel with 4 processes
python scripts/distributed_test_runner_enhanced.py --workers 4

# Run only unit tests in parallel
python scripts/distributed_test_runner_enhanced.py --category unit

# Run only fast tests in parallel
python scripts/distributed_test_runner_enhanced.py --speed fast

# Run tests with balanced load distribution
python scripts/distributed_test_runner_enhanced.py --balance-load

# Generate an HTML report
python scripts/distributed_test_runner_enhanced.py --html
```

### Running Modified Tests

You can run only tests affected by recent changes using the `run_modified_tests.py` script:

```bash
# Run tests affected by changes in the last commit
python scripts/run_modified_tests.py

# Run tests affected by changes in the last 5 commits
python scripts/run_modified_tests.py --since HEAD~5

# Run tests affected by changes in a specific file
python scripts/run_modified_tests.py --file src/devsynth/application/cli/commands/init_cmd.py
```

### Balanced Test Distribution

You can distribute tests across processes with balanced load using the `run_balanced_tests.py` script:

```bash
# Run tests with balanced load distribution across 4 processes
python scripts/run_balanced_tests.py --processes 4

# Run only unit tests with balanced load distribution
python scripts/run_balanced_tests.py --category unit

# Use historical execution times for load balancing
python scripts/run_balanced_tests.py --use-history
```

## Troubleshooting

### Common Issues

1. **Tests take too long to run**:
   - Use `--fast` to run only fast tests
   - Enable segmentation with `--segment`
   - Run only specific test types with `--unit`, `--integration`, or `--behavior`
   - Use the distributed test runner: `python scripts/distributed_test_runner_enhanced.py`

2. **Memory issues**:
   - Use segmentation with `--segment` to run tests in smaller batches
   - Reduce the segment size with `--segment-size`
   - Run tests in parallel with `--processes`

3. **Test categorization issues**:
   - Run the `enhanced_test_categorization.py` script with `--update` to apply speed markers
   - Use `--force` to recategorize tests regardless of previous categorization
   - Check for marker placement issues with `fix_test_markers.py --report`
   - Fix marker placement issues with `fix_test_markers.py --fix-all`

4. **Markers not being detected**:
   - Check for blank lines between markers and functions
   - Check for markers inside function bodies
   - Verify pytest is imported at the top of the file
   - Run `fix_test_markers.py --fix-all` to fix marker placement issues
   - Clear the cache with `common_test_collector.py --clear-cache`

5. **Inconsistent test counts**:
   - Use `common_test_collector.py --count --no-cache` for accurate counts
   - Check for duplicate test names across different files
   - Verify all test files are being collected
   - Run `reconcile_test_counts.py --analyze` to identify discrepancies

### Fixing Marker Placement Issues

If you encounter issues with marker placement, you can use the `fix_test_markers.py` script:

```bash
# Generate a report of marker issues
python scripts/fix_test_markers.py --report

# Fix misaligned markers in a specific module
python scripts/fix_test_markers.py --module tests/unit/interface

# Fix all marker issues (misaligned, duplicate, inconsistent)
python scripts/fix_test_markers.py --fix-all

# Show detailed information about changes
python scripts/fix_test_markers.py --verbose

# Show changes without modifying files
python scripts/fix_test_markers.py --dry-run
```

## Best Practices

### Writing Tests with Speed in Mind

1. **Keep tests focused**: Each test should test one specific behavior or functionality.
2. **Minimize setup and teardown**: Use fixtures to share setup and teardown code.
3. **Avoid unnecessary I/O**: Mock external dependencies to avoid network or file system operations.
4. **Use appropriate speed markers**: Categorize tests based on their execution time.
5. **Isolate tests**: Ensure tests don't depend on the state from other tests.

### Adding Speed Markers Manually

You can add speed markers manually to your tests:

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

### Optimizing Test Speed

1. **Use mocks**: Mock external dependencies to avoid network or file system operations.
2. **Optimize setup and teardown**: Use fixtures to share setup and teardown code.
3. **Use parameterized tests**: Use pytest's parameterize feature to run multiple test cases with a single test function.
4. **Avoid unnecessary assertions**: Only assert what's necessary for the test.
5. **Use appropriate isolation**: Use the `@pytest.mark.isolation` marker for tests that need to be run in isolation.

### Continuous Integration

For continuous integration, we recommend the following approach:

1. **Fast Tests**: Run on every commit to provide quick feedback.
2. **Medium Tests**: Run on pull requests to catch more issues before merging.
3. **Slow Tests**: Run nightly to ensure comprehensive coverage without slowing down development.
4. **High-Risk Tests**: Run on pull requests that modify critical components.

### Test Execution Strategy

For local development, we recommend the following approach:

1. **During Development**:
   - Run fast tests frequently to get quick feedback
   - Use `devsynth run-pipeline --fast`

2. **Before Committing**:
   - Run fast and medium tests to catch more issues
   - Use `devsynth run-pipeline --fast --medium`

3. **Before Pull Request**:
   - Run all tests to ensure comprehensive coverage
   - Use `devsynth run-pipeline`

4. **After Making Changes**:
   - Run tests affected by your changes
   - Use `python scripts/run_modified_tests.py`

5. **When Investigating Failures**:
   - Run high-risk tests to focus on likely failures
   - Use `python scripts/prioritize_high_risk_tests.py`

## Reference

### Script Reference

#### common_test_collector.py

```bash
# Get test counts
python scripts/common_test_collector.py --count

# Get marker counts
python scripts/common_test_collector.py --marker-counts

# List tests with a specific marker
python scripts/common_test_collector.py --list-marked-tests --marker-type medium

# Clear the cache
python scripts/common_test_collector.py --clear-cache

# Collect tests for a specific category
python scripts/common_test_collector.py --category unit
```

#### enhanced_test_categorization.py

```bash
# Categorize tests in a specific module
python scripts/enhanced_test_categorization.py --module tests/unit/application/cli --update

# Categorize tests with priority for high-priority modules
python scripts/enhanced_test_categorization.py --priority --update

# Limit the number of tests categorized in a single run
python scripts/enhanced_test_categorization.py --max-tests 50 --update

# Generate a categorization report
python scripts/enhanced_test_categorization.py --report --update

# Fix marker placement issues after categorization
python scripts/enhanced_test_categorization.py --fix-markers --update
```

#### prioritize_high_risk_tests.py

```bash
# Run high-risk tests in a specific module
python scripts/prioritize_high_risk_tests.py --module tests/unit/application/cli

# Run only the top 50 highest-risk tests
python scripts/prioritize_high_risk_tests.py --limit 50

# Run tests with a minimum risk score of 70
python scripts/prioritize_high_risk_tests.py --min-risk 70

# Update test history with new results
python scripts/prioritize_high_risk_tests.py --update-history

# Generate a detailed risk report
python scripts/prioritize_high_risk_tests.py --report

# Show tests that would be run without running them
python scripts/prioritize_high_risk_tests.py --dry-run
```

#### reconcile_test_counts.py

```bash
# Analyze discrepancies without making changes
python scripts/reconcile_test_counts.py --analyze

# Update documentation files with accurate counts
python scripts/reconcile_test_counts.py --update-docs

# Update tracking files with accurate counts
python scripts/reconcile_test_counts.py --update-tracking

# Update both documentation and tracking files
python scripts/reconcile_test_counts.py --update-all
```

#### distributed_test_runner_enhanced.py

```bash
# Run tests in parallel with 4 processes
python scripts/distributed_test_runner_enhanced.py --workers 4

# Run only unit tests in parallel
python scripts/distributed_test_runner_enhanced.py --category unit

# Run only fast tests in parallel
python scripts/distributed_test_runner_enhanced.py --speed fast

# Run tests with balanced load distribution
python scripts/distributed_test_runner_enhanced.py --balance-load

# Generate an HTML report
python scripts/distributed_test_runner_enhanced.py --html
```

#### fix_test_markers.py

```bash
# Generate a report of marker issues
python scripts/fix_test_markers.py --report

# Fix misaligned markers in a specific module
python scripts/fix_test_markers.py --module tests/unit/interface

# Fix all marker issues (misaligned, duplicate, inconsistent)
python scripts/fix_test_markers.py --fix-all

# Show detailed information about changes
python scripts/fix_test_markers.py --verbose

# Show changes without modifying files
python scripts/fix_test_markers.py --dry-run
```

### Related Documentation

- [Test Suite Overview](test_suite_overview.md)
- [Test Categorization Guide](test_categorization_guide.md)
- [Efficient Testing Guide](efficient_testing.md)
- [Test Marker Fixing Guide](test_marker_fixing.md)
- [Test Isolation Best Practices](test_isolation_best_practices.md)
- [Hermetic Testing Guide](hermetic_testing.md)

---

_Last updated: August 1, 2025_
