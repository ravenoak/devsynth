---
title: "Enhanced Test Parser"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Enhanced Test Parser

## Overview

The Enhanced Test Parser is a sophisticated tool for accurately detecting and analyzing tests in Python files using Abstract Syntax Tree (AST) analysis. It addresses discrepancies in test counts between pytest collection and file parsing for non-behavior tests.

This document provides detailed information about the Enhanced Test Parser, including its purpose, functionality, and usage.

## Key Features

1. **Robust Test Detection**: Uses AST analysis to accurately detect test functions and methods
2. **Parameterized Test Support**: Handles complex parameter expressions in parameterized tests
3. **Nested Class Support**: Properly handles nested classes and complex inheritance patterns
4. **Accurate Marker Detection**: Uses AST-based decorator analysis for reliable marker detection
5. **Edge Case Handling**: Supports various pytest test patterns and edge cases

## Architecture

The Enhanced Test Parser consists of several key components:

### TestVisitor Class

The `TestVisitor` class is an AST visitor that finds test functions and methods along with their markers. It handles:

- Detecting test functions and methods (starting with `test_`)
- Extracting markers from decorators
- Identifying parameterized tests
- Extracting individual test cases from parameterized tests
- Tracking class-level markers for inheritance

### Core Functions

- `parse_test_file(file_path, use_cache=True)`: Parses a test file to find test functions and methods
- `collect_tests_from_directory(directory, use_cache=True)`: Collects tests from a directory by parsing Python files
- `get_test_paths_from_directory(directory, use_cache=True, include_file_only=True)`: Gets test paths from a directory
- `get_tests_with_markers(directory, marker_types=["fast", "medium", "slow"], use_cache=True)`: Gets tests with specific markers
- `get_marker_counts(directory, use_cache=True)`: Gets counts of tests with specific markers
- `compare_with_pytest(directory)`: Compares test collection between this parser and pytest

## Usage

### Basic Usage

```python
from enhanced_test_parser import parse_test_file, collect_tests_from_directory

# Parse a single test file
tests = parse_test_file('tests/unit/test_example.py')

# Collect all tests from a directory
tests = collect_tests_from_directory('tests/unit')
```

### Getting Test Paths

```python
from enhanced_test_parser import get_test_paths_from_directory

# Get test paths from a directory
test_paths = get_test_paths_from_directory('tests/unit')

# Get test paths without file-only paths
test_paths = get_test_paths_from_directory('tests/unit', include_file_only=False)
```

### Working with Markers

```python
from enhanced_test_parser import get_tests_with_markers, get_marker_counts

# Get tests with specific markers
tests_by_marker = get_tests_with_markers('tests/unit', ["fast", "medium", "slow"])

# Get counts of tests with specific markers
marker_counts = get_marker_counts('tests/unit')
```

### Comparing with pytest

```python
from enhanced_test_parser import compare_with_pytest

# Compare test collection with pytest
comparison = compare_with_pytest('tests/unit')
print(f"Parser count: {comparison['parser_count']}")
print(f"Pytest count: {comparison['pytest_count']}")
print(f"Discrepancy: {comparison['discrepancy']}")
```

### Command-Line Usage

The Enhanced Test Parser can also be used from the command line (run via Poetry to ensure consistent environment and plugins):

```bash
# Compare with pytest collection
poetry run python scripts/enhanced_test_parser.py --directory tests/unit --compare

# Show marker counts
poetry run python scripts/enhanced_test_parser.py --directory tests/unit --markers

# Show detailed information
poetry run python scripts/enhanced_test_parser.py --directory tests/unit --verbose
```

## Test Detection Details

The Enhanced Test Parser uses the following criteria to detect tests:

1. **Test Functions**: Functions whose names start with `test_`
2. **Test Methods**: Methods in classes whose names start with `test_`
3. **Parameterized Tests**: Tests decorated with `@pytest.mark.parametrize` or equivalent

For each test, the parser extracts:
- The full test path (file::class::method or file::function)
- The test name
- The class name (if applicable)
- Markers applied to the test
- Whether the test is parameterized
- The line number where the test is defined

## Marker Detection Details

The parser detects markers using AST-based decorator analysis, supporting various patterns:

1. `@pytest.mark.fast`, `@pytest.mark.medium`, `@pytest.mark.slow`
2. `@pytest.mark.fast()`, `@pytest.mark.medium()`, `@pytest.mark.slow()`
3. `@mark.fast`, `@mark.medium`, `@mark.slow` (when pytest.mark is imported as mark)
4. `@mark.fast()`, `@mark.medium()`, `@mark.slow()`

The parser also handles class-level markers that apply to all methods in the class.

## Caching

The Enhanced Test Parser uses a file cache to improve performance when parsing multiple files. The cache can be:

- Enabled by default (`use_cache=True`)
- Disabled for fresh results (`use_cache=False`)
- Cleared manually (`clear_cache()`)

## Comparison with pytest

The `compare_with_pytest` function provides detailed information about discrepancies between the Enhanced Test Parser and pytest collection:

- Total test counts from both methods
- Tests found only by the parser
- Tests found only by pytest
- Common tests found by both methods
- Overall discrepancy

This comparison helps identify and understand differences in test collection methods.

## Best Practices

1. **Use Caching Appropriately**: Enable caching for better performance, but disable it when you need fresh results
2. **Handle Syntax Errors**: The parser skips files with syntax errors, so be aware of this when comparing with pytest
3. **Understand Discrepancies**: Some discrepancy between the parser and pytest is expected due to fundamental differences in collection methods
4. **Use Verbose Mode**: When troubleshooting, use the `--verbose` flag to see detailed information

## Limitations

1. **Syntax Errors**: The parser cannot analyze files with syntax errors, while pytest can still collect tests from them
2. **Dynamic Test Generation**: Tests generated dynamically at runtime may not be detected
3. **Custom Test Patterns**: Non-standard test patterns may not be detected correctly
4. **Path Format Differences**: The parser and pytest may use different path formats for the same test

## Integration with Other Tools

The Enhanced Test Parser is designed to work with other test infrastructure tools:

- **Enhanced Test Collector**: Integrates the parser with the existing test infrastructure
- **Test Isolation Analyzer**: Uses the parser to analyze test isolation issues
- **Generate Comprehensive Reports**: Uses the parser to generate reports on test counts and marker detection

## Conclusion

The Enhanced Test Parser provides a robust and accurate way to detect and analyze tests in Python files. By using AST analysis, it addresses many of the limitations of simpler parsing methods and provides valuable insights into the test infrastructure.

While some discrepancies with pytest collection are expected due to fundamental differences in collection methods, the Enhanced Test Parser provides a solid foundation for understanding and managing these differences.
