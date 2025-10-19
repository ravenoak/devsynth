---
title: "Test Categorization Guide"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "developer-guide"
  - "guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Test Categorization Guide

This guide explains the approach to test categorization in the DevSynth project, including the test categorization schedule and how to use it.

## Table of Contents

- [Overview](#overview)
- [Test Speed Categories](#test-speed-categories)
- [Current Categorization Status](#current-categorization-status)
- [Test Categorization Schedule](#test-categorization-schedule)
- [Using the Test Categorization Scripts](#using-the-test-categorization-scripts)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

DevSynth has a large test suite with 5,842 tests across various categories. To improve test performance and enable more efficient test execution, we categorize tests by speed:

- **Fast Tests**: Execution time < 1 second
- **Medium Tests**: Execution time between 1-5 seconds
- **Slow Tests**: Execution time > 5 seconds

This categorization allows developers to run only fast tests during development, medium tests during pre-commit checks, and all tests (including slow ones) during CI/CD pipelines.

## Test Speed Categories

### Fast Tests

Fast tests execute in less than 1 second. They are ideal for running frequently during development.

**Target**: ~40% of all tests

**How to run**: `devsynth run-pipeline --fast`

### Medium Tests

Medium tests execute between 1-5 seconds. They provide a good balance between coverage and execution time.

**Target**: ~40% of all tests

**How to run**: `devsynth run-pipeline --medium`

### Slow Tests

Slow tests execute in more than 5 seconds. They are typically integration or behavior tests that involve multiple components.

**Target**: ~20% of all tests

**How to run**: `devsynth run-pipeline --slow`

## Current Categorization Status

As of August 1, 2025, the categorization status is:

| Speed | Count | Percentage | Target |
|-------|-------|------------|--------|
| Fast | 0 | 0.0% | ~40% |
| Medium | 426 | 7.3% | ~40% |
| Slow | 1 | 0.0% | ~20% |
| Unmarked | 5,415 | 92.7% | 0% |
| **Total** | **5,842** | **100%** | **100%** |

We have begun applying speed categorization to the tests using the `incremental_test_categorization.py` script and the test categorization schedule. So far, we have categorized 427 tests (7.3% of total) with the "medium" marker (execution time between 1-5 seconds).

> **Note**: There is a discrepancy between the number of tests tracked in the progress file (.test_categorization_progress.json) and the number of tests with actual markers detected by pytest. This is due to marker placement issues that have been identified and are being addressed with the `fix_test_markers.py` script.

## Test Categorization Schedule

To systematically categorize the remaining 2,476 unmarked tests, we have implemented a test categorization schedule using the `test_categorization_schedule.py` script. This script:

1. Prioritizes high-priority modules for categorization
2. Distributes the tests across a configurable number of days (default: 14)
3. Calculates the number of tests to categorize per day
4. Provides commands to generate a schedule, update progress, run the scheduled categorization for today, and list the current schedule

### High-Priority Modules

The following modules are prioritized for categorization:

1. `tests/unit/application/cli` - CLI components
2. `tests/unit/adapters/memory` - Memory adapters
3. `tests/unit/adapters/llm` - LLM adapters
4. `tests/integration/memory` - Memory integration
5. `tests/unit/application/wsde` - WSDE components
6. `tests/unit/application/webui` - WebUI components

These modules are critical for the Phase 2 implementation and are likely to be modified frequently during development.

## Using the Test Categorization Scripts

### Common Test Collector

The `common_test_collector.py` script provides a unified interface for collecting tests across the project:

```bash
# Get test counts
python scripts/common_test_collector.py --count

# Get marker counts
python scripts/common_test_collector.py --marker-counts

# List tests with a specific marker
python scripts/common_test_collector.py --list-marked-tests --marker-type medium

# Clear the cache to ensure fresh results
python scripts/common_test_collector.py --clear-cache

# Collect tests for a specific category
python scripts/common_test_collector.py --category unit
```

### Fixing Test Markers

The `fix_test_markers.py` script identifies and fixes marker placement issues:

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

### Categorizing Tests Incrementally

The `incremental_test_categorization.py` script allows you to categorize tests in smaller batches over time:

```bash
# Categorize tests in a specific module
python scripts/incremental_test_categorization.py --module tests/unit/application/cli --update

# Limit the number of tests categorized in a single run
python scripts/incremental_test_categorization.py --max-tests 50 --update

# Adjust batch size for better performance
python scripts/incremental_test_categorization.py --batch-size 20 --update

# Force recategorization of tests, even if they have already been categorized
python scripts/incremental_test_categorization.py --force --update

# Show changes without modifying files
python scripts/incremental_test_categorization.py --dry-run
```

### Using the Test Categorization Schedule

#### Legacy Approach

The `test_categorization_schedule.py` script helps you manage the categorization process:

```bash
# Generate a new categorization schedule
python scripts/test_categorization_schedule.py --generate-schedule

# Run the scheduled categorization for today
python scripts/test_categorization_schedule.py --run-scheduled

# List the current categorization schedule
python scripts/test_categorization_schedule.py --list-schedule

# Update progress after manual categorization
python scripts/test_categorization_schedule.py --update-progress

# Generate a schedule for high-priority modules only
python scripts/test_categorization_schedule.py --generate-schedule --priority-only

# Adjust the number of days for the schedule
python scripts/test_categorization_schedule.py --generate-schedule --days 21

# Adjust batch size for better performance
python scripts/test_categorization_schedule.py --run-scheduled --batch-size 50

# Show what would be done without making changes
python scripts/test_categorization_schedule.py --run-scheduled --dry-run
```

#### Enhanced Approach (New Scripts)

We've developed two new scripts that provide an enhanced approach to test categorization:

1. `create_test_categorization_schedule.py` - Creates a schedule for categorizing tests
2. `execute_test_categorization.py` - Executes the test categorization plan

##### Creating a Test Categorization Schedule

The `create_test_categorization_schedule.py` script creates a schedule for categorizing tests over a specified period:

```bash
# Create a schedule for 4 weeks with 100 tests per day
python scripts/create_test_categorization_schedule.py --weeks 4 --tests-per-day 100

# Specify custom priority modules
python scripts/create_test_categorization_schedule.py --priority-modules tests/unit/interface tests/unit/adapters/memory
```

This generates a `.test_categorization_schedule.json` file with a daily schedule of tests to categorize, prioritizing high-priority modules first.

##### Executing the Test Categorization Plan

The `execute_test_categorization.py` script runs tests according to the schedule, measures their execution time, and applies appropriate speed markers:

```bash
# Execute today's test categorization plan
python scripts/execute_test_categorization.py

# Execute test categorization for a specific date
python scripts/execute_test_categorization.py --date 2025-08-05

# Run in dry-run mode (don't apply markers, just measure execution time)
python scripts/execute_test_categorization.py --dry-run

# Force re-categorization of already categorized tests
python scripts/execute_test_categorization.py --force

# Customize speed thresholds (align with project standards)
python scripts/execute_test_categorization.py --fast-threshold 1.0 --medium-threshold 5.0
```

This script maintains a `.test_categorization_progress.json` file that tracks which tests have been categorized and their speed categories.

### Recommended Workflow

1. Generate a categorization schedule:
   ```bash
   python scripts/test_categorization_schedule.py --generate-schedule
   ```

2. View the schedule to understand what needs to be categorized:
   ```bash
   python scripts/test_categorization_schedule.py --list-schedule
   ```

3. Run the scheduled categorization for today:
   ```bash
   python scripts/test_categorization_schedule.py --run-scheduled
   ```

4. Repeat step 3 daily until all tests are categorized.

5. Update the test documentation as categorization progresses.

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

## Best Practices for Marker Placement

When adding speed markers to tests, follow these best practices to ensure they are correctly detected by pytest:

### Correct Marker Placement

1. **Place markers directly before the test function**:
   ```python
   @pytest.mark.medium  # Correct
   def test_function():
       pass
   ```

2. **No blank lines between marker and function**:
   ```python
   @pytest.mark.medium
   def test_function():  # Correct - no blank lines
       pass

   @pytest.mark.medium

   def test_function():  # Incorrect - blank line between marker and function
       pass
   ```

3. **Don't place markers inside function bodies**:
   ```python
   def test_function():
       @pytest.mark.medium  # Incorrect - inside function body
       assert True
   ```

4. **Import pytest at the top of the file**:
   ```python
   import pytest  # Required for markers to work

   @pytest.mark.medium
   def test_function():
       pass
   ```

5. **Use the correct marker format**:
   ```python
   @pytest.mark.fast    # Correct
   @pytest.mark.medium  # Correct
   @pytest.mark.slow    # Correct

   @pytest.mark.speed("fast")  # Incorrect format
   ```

### Verifying Marker Placement

After adding markers, verify they are correctly detected:

```bash
# Check if markers are detected
python scripts/common_test_collector.py --marker-counts --no-cache

# List tests with a specific marker
python scripts/common_test_collector.py --list-marked-tests --marker-type medium
```

### Fixing Marker Issues

If markers are not being detected, use the fix_test_markers.py script:

```bash
# Generate a report of marker issues
python scripts/fix_test_markers.py --report

# Fix all marker issues
python scripts/fix_test_markers.py --fix-all
```

## Troubleshooting

### Common Issues

1. **Tests take too long to run**:
   - Use `--fast` to run only fast tests
   - Enable segmentation with `--segment`
   - Run only specific test types with `--unit`, `--integration`, or `--behavior`
   - Use the distributed test runner: `python scripts/distributed_test_runner.py`

2. **Memory issues**:
   - Use segmentation with `--segment` to run tests in smaller batches
   - Reduce the segment size with `--segment-size`
   - Run tests in parallel with `--processes`

3. **Test categorization issues**:
   - Run the `incremental_test_categorization.py` script with `--update` to apply speed markers
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

### Getting Help

If you encounter issues not covered in this guide, please:

1. Check the [Troubleshooting Guide](/docs/getting_started/troubleshooting.md) for common issues and solutions
2. Review the [FAQ](/docs/getting_started/faq.md) for answers to frequently asked questions
3. Open an issue on GitHub if you encounter a bug or have a feature request

---

_Last updated: August 02, 2025_
