---
title: "Test Infrastructure Architecture"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Test Infrastructure Architecture

This document provides a comprehensive overview of the DevSynth test infrastructure architecture, including the caching mechanisms, test categorization, and performance optimization strategies.

## Table of Contents

- [Overview](#overview)
- [Core Components](#core-components)
- [Caching Mechanism](#caching-mechanism)
- [Test Categorization](#test-categorization)
- [Performance Optimization](#performance-optimization)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The DevSynth test infrastructure is designed to support a large and growing test suite (currently 2,777+ tests) with a focus on performance, maintainability, and developer experience. The infrastructure includes:

- Test collection and categorization
- Speed-based test markers (fast, medium, slow)
- Caching mechanisms for test collection and execution times
- Distributed test execution
- Test prioritization based on risk and history

## Core Components

### Test Utility Modules

1. **common_test_collector.py**
   - Core module for test collection and marker detection
   - Manages caching for test collection, complexity metrics, and failure history
   - Provides functions for cache invalidation and selective cache clearing

2. **test_utils.py**
   - Common utilities for test scripts
   - Provides functions for test collection, execution, and timing
   - Adds common command-line arguments to test scripts

3. **test_utils_extended.py**
   - Extends functionality in test_utils.py
   - Provides enhanced test collection and marker verification
   - Manages synchronization between test categorization tracking files

### Test Categorization Scripts

1. **add_missing_markers.py**
   - Identifies tests without speed markers
   - Runs tests to measure execution time
   - Adds appropriate markers (fast, medium, slow) based on execution time

2. **apply_speed_markers.py**
   - Applies speed markers to tests using existing timing data
   - Reads timing data from the .test_timing_cache directory
   - Applies markers without running tests again

3. **verify_test_markers.py**
   - Verifies that test markers are correctly applied and recognized
   - Identifies inconsistencies in marker placement

### Test Execution Scripts

1. **distributed_test_runner_enhanced.py**
   - Runs tests in parallel across multiple processes
   - Distributes tests based on execution time for balanced workloads

2. **run_balanced_tests.py**
   - Runs tests with balanced distribution across processes
   - Optimizes test execution time

3. **run_high_risk_tests.py**
   - Prioritizes and runs tests with high risk of failure
   - Uses failure history and complexity metrics

## Caching Mechanism

The caching mechanism is a critical component of the test infrastructure, enabling efficient test collection, marker detection, and execution time tracking.

### Cache Structure

The test infrastructure uses several cache files:

1. **Test Collection Cache** (`TEST_CACHE_FILE`)
   - Stores collected tests by category
   - Stores marker information
   - Contains metadata including file timestamps and last update time

2. **Complexity Cache** (`COMPLEXITY_CACHE_FILE`)
   - Stores complexity metrics for test files and functions

3. **Failure History** (`FAILURE_HISTORY_FILE`)
   - Tracks test failures over time
   - Used for test prioritization

### Cache Invalidation

The cache invalidation mechanism ensures that the cache is updated when test files are modified:

1. **File Timestamp Tracking**
   - The cache stores the modification time of each test file
   - When a file is modified, its timestamp changes
   - The cache is invalidated if any file's current timestamp differs from its cached timestamp

2. **Selective Cache Invalidation**
   - The `clear_cache(selective=True)` function selectively invalidates the cache without removing the cache files
   - This preserves the cache structure while forcing recollection of data

3. **File-Specific Cache Invalidation**
   - The `invalidate_cache_for_files(file_paths)` function invalidates the cache for specific files
   - This is used by marker application scripts to invalidate only the relevant parts of the cache

### Cache Usage in Scripts

Test scripts interact with the cache in several ways:

1. **Test Collection**
   - Scripts use `collect_tests()` or `collect_tests_by_category()` to collect tests
   - These functions use the cache to avoid repeated collection

2. **Marker Detection**
   - Scripts use `check_test_has_marker()` to check if a test has a marker
   - This function updates the file timestamp in the cache

3. **Cache Invalidation**
   - Scripts use `invalidate_cache_for_files()` after modifying test files
   - This ensures that the cache is updated when markers are added or modified

## Test Categorization

Tests are categorized by speed to enable efficient test execution during development and CI/CD:

### Speed Categories

1. **Fast Tests** (< 1.0 seconds)
   - Quick unit tests that can be run frequently during development
   - Marked with `@pytest.mark.fast`

2. **Medium Tests** (1.0 - 5.0 seconds)
   - Tests that take a moderate amount of time to run
   - Marked with `@pytest.mark.medium`

3. **Slow Tests** (> 5.0 seconds)
   - Tests that take a long time to run
   - Marked with `@pytest.mark.slow`

### Categorization Process

1. **Measuring Execution Time**
   - Tests are run to measure their execution time
   - Timing data is stored in the `.test_timing_cache` directory

2. **Applying Markers**
   - Markers are applied based on execution time
   - `add_missing_markers.py` runs tests and adds markers
   - `apply_speed_markers.py` uses existing timing data to add markers

3. **Verifying Markers**
   - `verify_test_markers.py` verifies that markers are correctly applied
   - Identifies inconsistencies in marker placement

## Performance Optimization

Several strategies are used to optimize test performance:

### Distributed Test Execution

1. **Process-Based Parallelism**
   - Tests are distributed across multiple processes
   - `distributed_test_runner_enhanced.py` manages the distribution

2. **Balanced Distribution**
   - Tests are distributed based on execution time
   - `run_balanced_tests.py` ensures balanced workloads

### Test Prioritization

1. **Risk-Based Prioritization**
   - Tests are prioritized based on risk of failure
   - `run_high_risk_tests.py` runs high-risk tests first

2. **History-Based Prioritization**
   - Tests with a history of failures are prioritized
   - Failure history is tracked in the `FAILURE_HISTORY_FILE`

### Incremental Testing

1. **Modified Tests**
   - Only tests affected by recent changes are run
   - `run_modified_tests.py` identifies and runs modified tests

2. **Speed-Based Selection**
   - Only tests of a specific speed category are run
   - `--speed` option selects tests by speed marker

## Best Practices

### Adding New Tests

1. **Add Speed Markers**
   - Add appropriate speed markers to new tests
   - Use `@pytest.mark.fast`, `@pytest.mark.medium`, or `@pytest.mark.slow`

2. **Run Tests with Markers**
   - Run tests with the appropriate speed marker
   - Use `pytest -m fast` to run only fast tests

### Modifying Tests

1. **Update Markers**
   - Update markers if test execution time changes significantly
   - Use `apply_speed_markers.py` to update markers

2. **Invalidate Cache**
   - Invalidate the cache after modifying test files
   - Use `invalidate_cache_for_files()` or `clear_cache(selective=True)`

### Running Tests

1. **Use Speed Categories**
   - Run tests by speed category during development
   - Use `pytest -m fast` for quick feedback

2. **Use Distributed Execution**
   - Use distributed execution for large test suites
   - Use `distributed_test_runner_enhanced.py` for parallel execution

## Troubleshooting

### Cache Issues

1. **Stale Cache**
   - If the cache seems stale, clear it with `clear_cache()`
   - Use `--no-cache` option to bypass the cache

2. **Marker Detection Issues**
   - If markers are not detected, check marker placement
   - Use `verify_test_markers.py` to identify issues

### Performance Issues

1. **Slow Test Execution**
   - Use distributed execution for large test suites
   - Use speed markers to run only necessary tests

2. **Unbalanced Distribution**
   - Use `run_balanced_tests.py` for balanced distribution
   - Update test timing data regularly

---

_Last updated: August 1, 2025_
