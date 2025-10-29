---
title: "Common Test Collector Guide"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "developer-guide"
  - "guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Common Test Collector Guide

## Overview

The Common Test Collector is a unified interface for collecting, analyzing, and managing tests across the DevSynth project. It provides a comprehensive set of tools for:

- Collecting tests from different categories (unit, integration, behavior, performance, property)
- Analyzing test complexity and dependencies
- Tracking and analyzing test failure history
- Filtering tests by various criteria
- Generating reports in CI-friendly formats

This guide explains how to use the Common Test Collector effectively, both as a command-line tool and as a Python module.

## Installation

The Common Test Collector is included in the DevSynth project. No additional installation is required.

## Command-Line Usage

### Basic Usage

```bash
# List all tests
python scripts/common_test_collector.py

# List tests in a specific category
python scripts/common_test_collector.py --category unit

# Show test counts
python scripts/common_test_collector.py --count

# Clear the cache
python scripts/common_test_collector.py --clear-cache
```

### Test Filtering

```bash
# Filter tests by name pattern
python scripts/common_test_collector.py --pattern "test_webui"

# Filter tests by module
python scripts/common_test_collector.py --module "interface"

# Exclude tests matching a pattern
python scripts/common_test_collector.py --exclude-pattern "test_cli"

# Exclude tests from a module
python scripts/common_test_collector.py --exclude-module "memory"

# Combine filters
python scripts/common_test_collector.py --pattern "test_webui" --exclude-pattern "test_webui_serve"
```

### Speed Markers

```bash
# Show tests with markers
python scripts/common_test_collector.py --markers

# Show counts of tests with markers
python scripts/common_test_collector.py --marker-counts

# List tests with a specific marker
python scripts/common_test_collector.py --list-marked-tests --marker-type medium
```

### Complexity Analysis

```bash
# Show complexity metrics for tests
python scripts/common_test_collector.py --complexity

# Show high-risk tests
python scripts/common_test_collector.py --high-risk

# Set risk threshold
python scripts/common_test_collector.py --high-risk --risk-threshold 0.7

# Sort tests by risk score
python scripts/common_test_collector.py --sort-by-risk

# Limit the number of tests shown
python scripts/common_test_collector.py --complexity --limit 10
```

### Dependency Analysis

```bash
# Show dependencies between tests
python scripts/common_test_collector.py --dependencies

# Show tests that depend on a specific test
python scripts/common_test_collector.py --dependents "tests/unit/interface/test_cli.py::test_cli_init"

# Sort tests by number of dependents
python scripts/common_test_collector.py --sort-by-dependencies

# Show only tests with at least a certain number of dependents
python scripts/common_test_collector.py --dependencies --min-dependents 5
```

### Failure History

```bash
# Record test results from a JSON file
python scripts/common_test_collector.py --record-results results.json

# Show failure rates for tests
python scripts/common_test_collector.py --failure-rates

# Show frequently failing tests
python scripts/common_test_collector.py --frequently-failing

# Set failure threshold
python scripts/common_test_collector.py --frequently-failing --failure-threshold 0.2

# Set minimum number of runs required
python scripts/common_test_collector.py --frequently-failing --min-runs 5

# Sort tests by failure rate
python scripts/common_test_collector.py --sort-by-failures
```

### Reporting

```bash
# Generate a JUnit XML report
python scripts/common_test_collector.py --junit-xml report.xml

# Generate a JSON report
python scripts/common_test_collector.py --json-report report.json

# Include complexity metrics in the JSON report
python scripts/common_test_collector.py --json-report report.json --include-complexity

# Include dependencies in the JSON report
python scripts/common_test_collector.py --json-report report.json --include-dependencies

# Include failure rates in the JSON report
python scripts/common_test_collector.py --json-report report.json --include-failure-rates

# Use test results from a JSON file for the report
python scripts/common_test_collector.py --json-report report.json --use-test-results results.json
```

### Combining Options

You can combine multiple options to create powerful test management workflows:

```bash
# Find high-risk tests in a specific module and generate a report
python scripts/common_test_collector.py --category unit --module "interface" --high-risk --json-report high_risk_interface_tests.json --include-complexity

# Find frequently failing tests with high complexity and generate a report
python scripts/common_test_collector.py --frequently-failing --complexity --sort-by-risk --json-report critical_tests.json --include-complexity --include-failure-rates

# Generate a comprehensive report for CI/CD integration
python scripts/common_test_collector.py --json-report ci_report.json --include-complexity --include-dependencies --include-failure-rates --use-test-results latest_results.json
```

## Python Module Usage

You can also use the Common Test Collector as a Python module in your scripts:

```python
from scripts.common_test_collector import (
    collect_tests,
    collect_tests_by_category,
    get_test_counts,
    filter_tests_by_pattern,
    filter_tests_by_module,
    calculate_test_complexity,
    analyze_test_dependencies,
    record_test_run,
    get_test_failure_rates,
    get_frequently_failing_tests,
    generate_junit_xml_report,
    generate_json_report
)

# Collect all tests
all_tests = collect_tests()

# Collect tests by category
unit_tests = collect_tests_by_category("unit")

# Get test counts
counts = get_test_counts()
print(f"Total tests: {counts['total']}")

# Filter tests
webui_tests = filter_tests_by_pattern(all_tests, "webui")
interface_tests = filter_tests_by_module(all_tests, "interface")

# Calculate complexity for a test
complexity = calculate_test_complexity("tests/unit/interface/test_cli.py::test_cli_init")

# Analyze dependencies
dependencies = analyze_test_dependencies(all_tests)

# Record test results
test_results = {
    "tests/unit/test_example.py::test_function": True,
    "tests/unit/test_example.py::test_failing": False
}
run_id = record_test_run(test_results)

# Get failure rates
failure_rates = get_test_failure_rates()

# Get frequently failing tests
failing_tests = get_frequently_failing_tests(threshold=0.2, min_runs=3)

# Generate reports
generate_junit_xml_report(all_tests, test_results, "report.xml")
generate_json_report(all_tests, test_results, None, dependencies, failure_rates, "report.json")
```

## Caching Behavior

The Common Test Collector uses caching to improve performance:

- Test collection results are cached to avoid repeated collection
- Complexity metrics are cached to avoid repeated calculation
- Dependency analysis results are cached to avoid repeated analysis
- Failure history is stored persistently for long-term tracking

You can control caching behavior with the following options:

- `--no-cache`: Don't use cached results
- `--clear-cache`: Clear all cache files

In Python code, most functions accept a `use_cache` parameter that you can set to `False` to bypass the cache.

## Best Practices

### Test Collection

- Use `--category` to limit the scope of collection when working with a specific test category
- Use `--no-cache` when you need to ensure fresh results (e.g., after adding new tests)
- Use `--count` to get a quick overview of the test suite

### Test Filtering

- Use `--pattern` and `--module` to focus on specific tests
- Use `--exclude-pattern` and `--exclude-module` to exclude irrelevant tests
- Combine filters to create precise test selections

### Complexity Analysis

- Use `--complexity` to identify complex tests that might need refactoring
- Use `--high-risk` to identify tests with high risk scores
- Use `--sort-by-risk` to prioritize tests for investigation

### Dependency Analysis

- Use `--dependencies` to understand relationships between tests
- Use `--dependents` to find tests that depend on a specific test
- Use `--sort-by-dependencies` to identify tests with many dependents

### Failure History

- Use `--record-results` to track test failures over time
- Use `--failure-rates` to identify tests with high failure rates
- Use `--frequently-failing` to focus on tests that fail frequently

### Reporting

- Use `--junit-xml` for integration with CI/CD systems that support JUnit XML
- Use `--json-report` for more detailed reports with additional metadata
- Include relevant data in JSON reports based on your needs

## Integration with Other Tools

### Test Prioritization

The Common Test Collector can be used with test prioritization tools:

```bash
# Generate a list of high-risk tests for prioritize_tests.py
python scripts/common_test_collector.py --high-risk --sort-by-risk > high_risk_tests.txt
python scripts/prioritize_tests.py --tests-file high_risk_tests.txt
```

### Distributed Test Execution

```bash
# Generate a list of tests for distributed_test_runner.py
python scripts/common_test_collector.py --pattern "test_webui" > webui_tests.txt
python scripts/distributed_test_runner.py --tests-file webui_tests.txt --workers 4
```

### CI/CD Integration

```bash
# Generate a report for CI/CD integration
python scripts/common_test_collector.py --json-report ci_report.json --include-complexity --include-dependencies --include-failure-rates --use-test-results latest_results.json
```

## Troubleshooting

### Common Issues

- **Tests not found**: Ensure you're using the correct category and pattern
- **Marker detection issues**: Try clearing the cache with `--clear-cache`
- **Dependency analysis errors**: Check if the code analysis tools are available
- **Report generation errors**: Ensure the output directory exists

### Debugging

- Use `--no-cache` to bypass the cache and get fresh results
- Check the error messages for specific issues
- Examine the cache files in the `.cache` directory

## API Reference

### Test Collection Functions

- `collect_tests(use_cache=True)`: Collect all tests
- `collect_tests_by_category(category, use_cache=True)`: Collect tests for a specific category
- `get_test_counts(use_cache=True)`: Get counts of tests by category

### Test Filtering Functions

- `filter_tests_by_pattern(tests, pattern)`: Filter tests by name pattern
- `filter_tests_by_module(tests, module)`: Filter tests by module name
- `apply_filters(tests, args)`: Apply all filters to the list of tests

### Complexity Analysis Functions

- `calculate_test_complexity(test_path, use_cache=True)`: Calculate complexity metrics for a test
- `get_tests_with_complexity(tests, use_cache=True)`: Get tests with their complexity metrics
- `get_high_risk_tests(tests, threshold=0.5, min_runs=3, use_cache=True)`: Get tests with risk score above the threshold

### Dependency Analysis Functions

- `analyze_test_dependencies(test_paths, use_cache=True)`: Analyze dependencies between tests
- `get_dependent_tests(test_path, dependencies)`: Get tests that depend on the given test

### Failure History Functions

- `record_test_run(test_results, run_id=None)`: Record the results of a test run
- `get_test_failure_rates(use_cache=True)`: Get failure rates for all tests
- `get_frequently_failing_tests(threshold=0.1, min_runs=3, use_cache=True)`: Get tests that fail frequently

### Reporting Functions

- `generate_junit_xml_report(tests, test_results=None, output_file="test_report.xml")`: Generate a JUnit XML report
- `generate_json_report(tests, test_results=None, complexity_metrics=None, dependencies=None, failure_rates=None, output_file="test_report.json")`: Generate a JSON report

## Conclusion

The Common Test Collector is a powerful tool for managing and analyzing tests in the DevSynth project. By leveraging its capabilities, you can:

- Gain insights into your test suite's complexity and dependencies
- Track and analyze test failures over time
- Generate reports for CI/CD integration
- Prioritize tests for investigation and optimization

For more information, see the [Test Suite Overview](test_suite_overview.md) and [Efficient Testing Guide](efficient_testing.md).
