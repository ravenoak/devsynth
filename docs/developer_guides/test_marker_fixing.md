---
title: "Test Marker Fixing Guide"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Test Marker Fixing Guide

This guide explains how to use the `fix_all_test_markers.py` script to fix test marker issues across the DevSynth project.

## Background

DevSynth uses pytest markers to categorize tests by speed (fast, medium, slow), which enables more efficient test execution. However, several issues can prevent these markers from being properly applied and detected:

1. **Syntax errors** in test files prevent pytest from collecting tests
2. **Misaligned markers** are not properly associated with test functions
3. **Missing markers** on test functions that should be categorized
4. **Duplicate markers** on the same test function
5. **Inconsistent markers** across similar test functions

The `fix_all_test_markers.py` script addresses all these issues in a single automated process.

## How It Works

The script follows a comprehensive approach to fixing test marker issues:

1. **Fixes syntax errors** in test files by:
   - Identifying files with syntax errors using pytest's collect-only mode
   - Fixing common syntax errors like indentation issues with import statements
   - Adding missing pytest imports

2. **Fixes misaligned markers** by running `fix_test_markers.py` with the `--fix-all` flag, which:
   - Identifies and fixes misaligned markers
   - Removes orphaned markers
   - Fixes duplicate markers
   - Addresses inconsistent markers

3. **Adds missing markers** by running `incremental_test_categorization.py` with the `--force` flag, which:
   - Measures execution times for tests
   - Categorizes tests as fast, medium, or slow based on execution time
   - Adds appropriate markers to test functions

4. **Verifies marker detection** by running `common_test_collector.py` with the `--no-cache` flag, which:
   - Counts markers across all test categories
   - Ensures markers are properly detected

## Usage

### Basic Usage

To run the script on all tests:

```bash
python scripts/fix_all_test_markers.py
```

### Targeting Specific Modules

To run the script on a specific module:

```bash
python scripts/fix_all_test_markers.py --module tests/unit/interface
```

### Dry Run Mode

To see what changes would be made without actually modifying files:

```bash
python scripts/fix_all_test_markers.py --dry-run
```

### Verbose Output

To see detailed information about the changes being made:

```bash
python scripts/fix_all_test_markers.py --verbose
```

### Controlling Batch Size and Maximum Tests

To control the number of tests processed in each batch and the maximum number of tests to process:

```bash
python scripts/fix_all_test_markers.py --batch-size 10 --max-tests 50
```

## Recommended Approach

For large test suites, we recommend running the script incrementally on different modules:

1. Start with high-priority modules:

```bash
python scripts/fix_all_test_markers.py --module tests/unit/application/cli
python scripts/fix_all_test_markers.py --module tests/unit/interface
python scripts/fix_all_test_markers.py --module tests/unit/adapters/llm
```

2. Then run on test categories:

```bash
python scripts/fix_all_test_markers.py --module tests/unit --max-tests 100
python scripts/fix_all_test_markers.py --module tests/integration --max-tests 100
python scripts/fix_all_test_markers.py --module tests/behavior --max-tests 100
```

3. Finally, run on any remaining tests:

```bash
python scripts/fix_all_test_markers.py --max-tests 100
```

## Verifying Results

After running the script, you can verify the results by running:

```bash
python scripts/common_test_collector.py --marker-counts --no-cache
```

This will show you how many tests have been marked with each speed category across all test categories.

## Troubleshooting

### Script Doesn't Fix Syntax Errors

If the script doesn't fix certain syntax errors, you may need to manually fix them. Common issues include:

- Complex indentation issues
- Circular imports
- Missing dependencies
- Incorrect import paths

### Markers Not Being Detected

If markers are not being detected after running the script, try:

1. Clearing the cache:

```bash
python scripts/common_test_collector.py --clear-cache
```

2. Running with the `--no-cache` flag:

```bash
python scripts/common_test_collector.py --marker-counts --no-cache
```

3. Checking if pytest can collect the tests:

```bash
python -m pytest <path-to-test-file> --collect-only -v
```

## Integration with Test Execution

Once tests are properly marked, you can run them by speed category:

```bash
# Run fast tests
devsynth run-pipeline --fast

# Run medium tests
devsynth run-pipeline --medium

# Run slow tests
devsynth run-pipeline --slow

# Run fast and medium tests
devsynth run-pipeline --fast --medium
```

This enables more efficient test execution, especially in CI/CD pipelines where you might want to run fast tests more frequently than slow tests.
