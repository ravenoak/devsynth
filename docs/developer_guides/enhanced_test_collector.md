---
title: "Enhanced Test Collector"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Enhanced Test Collector

## Overview

The Enhanced Test Collector integrates the enhanced test parser with the existing test infrastructure. It extends the common test collector to use the enhanced parser for non-behavior tests while maintaining compatibility with the existing infrastructure.

This document provides detailed information about the Enhanced Test Collector, including its purpose, functionality, and usage.

## Key Features

1. **Seamless Integration**: Integrates with the existing common_test_collector.py
2. **Improved Accuracy**: Provides more accurate test collection for non-behavior tests
3. **Enhanced Marker Detection**: Improves marker detection for non-behavior tests
4. **Backward Compatibility**: Maintains compatibility with existing test infrastructure scripts
5. **Hybrid Approach**: Uses the enhanced parser for non-behavior tests and the original implementation for behavior tests

## Architecture

The Enhanced Test Collector consists of several key components:

### Core Functions

- `collect_tests_by_category(category, use_cache=True)`: Collects tests by category using the appropriate parser
- `collect_tests(use_cache=True)`: Collects all tests in the project, organized by category
- `get_tests_with_markers(marker_types=["fast", "medium", "slow"], use_cache=True)`: Gets tests with specific markers, organized by category
- `get_marker_counts(use_cache=True)`: Gets counts of tests with specific markers, organized by category
- `check_test_has_marker(test_path, marker_types=["fast", "medium", "slow"])`: Checks if a test has a specific marker
- `verify_test_counts(use_cache=True)`: Verifies test counts between different collection methods
- `verify_marker_detection(use_cache=True)`: Verifies marker detection between different collection methods
- `generate_test_isolation_report(directory="tests")`: Generates a report on test isolation issues

## Integration with Existing Infrastructure

The Enhanced Test Collector integrates with the existing test infrastructure in the following ways:

1. **Common Test Collector**: Imports and extends the functionality of common_test_collector.py
2. **Enhanced Test Parser**: Uses the enhanced parser for non-behavior tests
3. **Test Isolation Analyzer**: Integrates with the test isolation analyzer for generating reports
4. **Test Categories**: Uses the same test categories as the common test collector
5. **Marker Types**: Supports the same marker types as the common test collector

## Usage

### Basic Usage

```python
from enhanced_test_collector import collect_tests, get_tests_with_markers

# Collect all tests
tests = collect_tests()

# Get tests with specific markers
tests_with_markers = get_tests_with_markers(["fast", "medium", "slow"])
```

### Collecting Tests by Category

```python
from enhanced_test_collector import collect_tests_by_category

# Collect unit tests
unit_tests = collect_tests_by_category("unit")

# Collect integration tests
integration_tests = collect_tests_by_category("integration")

# Collect behavior tests
behavior_tests = collect_tests_by_category("behavior")
```

### Working with Markers

```python
from enhanced_test_collector import get_marker_counts, check_test_has_marker

# Get marker counts
marker_counts = get_marker_counts()

# Check if a test has a specific marker
has_marker, marker_type = check_test_has_marker("tests/unit/test_example.py::test_function")
```

### Verification Functions

```python
from enhanced_test_collector import verify_test_counts, verify_marker_detection

# Verify test counts
test_count_results = verify_test_counts()

# Verify marker detection
marker_detection_results = verify_marker_detection()
```

### Test Isolation Report

```python
from enhanced_test_collector import generate_test_isolation_report

# Generate a test isolation report
isolation_report = generate_test_isolation_report("tests/unit")
```

### Command-Line Usage

The Enhanced Test Collector can also be used from the command line:

```bash
# Verify test counts
python enhanced_test_collector.py --verify-counts

# Verify marker detection
python enhanced_test_collector.py --verify-markers

# Generate a test isolation report
python enhanced_test_collector.py --isolation-report --directory tests/unit

# Save reports to a file
python enhanced_test_collector.py --verify-counts --output test_count_report.json
```

## Test Collection Details

The Enhanced Test Collector uses different approaches for different test categories:

1. **Non-behavior Tests** (unit, integration, performance, property):
   - Uses the enhanced parser for more accurate test detection
   - Supports parameterized tests and nested classes
   - Provides accurate marker detection

2. **Behavior Tests**:
   - Uses the original implementation from common_test_collector.py
   - Maintains compatibility with existing behavior test infrastructure

## Marker Detection Details

The Enhanced Test Collector improves marker detection in the following ways:

1. **AST-based Analysis**: Uses AST-based decorator analysis for non-behavior tests
2. **Class-level Markers**: Properly handles class-level markers that apply to all methods
3. **Various Decorator Patterns**: Supports different ways of applying markers
4. **Parameterized Tests**: Correctly detects markers on parameterized tests

## Verification Functions

The Enhanced Test Collector provides functions to verify its accuracy:

1. **verify_test_counts**: Compares test counts between the enhanced collector and pytest
   - Total test counts
   - Test counts by category
   - Discrepancies and their percentages

2. **verify_marker_detection**: Verifies marker detection between the enhanced collector and pytest
   - Marker counts by type
   - Marker counts by category
   - Discrepancies and their percentages

## Test Isolation Report

The `generate_test_isolation_report` function provides information about test isolation issues:

1. **Total Tests**: The total number of tests analyzed
2. **Potential Issues**: Identified potential isolation issues
3. **Recommendations**: Recommendations for improving test isolation

If the test_isolation_analyzer.py script is available, it uses that for detailed analysis. Otherwise, it falls back to a basic analysis with general recommendations.

## Best Practices

1. **Use the Enhanced Collector for Non-behavior Tests**: The enhanced collector provides more accurate results for non-behavior tests
2. **Verify Test Counts**: Use the verification functions to check the accuracy of test collection
3. **Check Marker Detection**: Verify marker detection to ensure markers are correctly applied
4. **Generate Isolation Reports**: Use the test isolation report to identify and fix isolation issues
5. **Save Reports for Analysis**: Save reports to JSON files for further analysis and tracking

## Limitations

1. **Behavior Tests**: The enhanced collector uses the original implementation for behavior tests, so it has the same limitations
2. **Syntax Errors**: Like the enhanced parser, it cannot analyze files with syntax errors
3. **Dynamic Test Generation**: Tests generated dynamically at runtime may not be detected
4. **Custom Test Patterns**: Non-standard test patterns may not be detected correctly

## Integration with Other Tools

The Enhanced Test Collector is designed to work with other test infrastructure tools:

- **Enhanced Test Parser**: Uses the parser for accurate test detection
- **Common Test Collector**: Extends the common collector for backward compatibility
- **Test Isolation Analyzer**: Integrates with the analyzer for isolation reports
- **Generate Comprehensive Reports**: Used by the report generator for test counts and marker detection

## Conclusion

The Enhanced Test Collector provides a seamless integration between the enhanced test parser and the existing test infrastructure. By using the enhanced parser for non-behavior tests while maintaining compatibility with the existing infrastructure, it offers improved accuracy and reliability without disrupting existing workflows.

The verification functions and test isolation report provide valuable tools for ensuring the quality and reliability of the test infrastructure, making it easier to identify and fix issues.
