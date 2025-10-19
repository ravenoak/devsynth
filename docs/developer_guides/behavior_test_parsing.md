---
title: "Behavior Test Parsing and Marker Management"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Behavior Test Parsing and Marker Management

This document provides information about the enhanced behavior test parsing solution implemented to address the discrepancies between pytest-bdd test detection and file parsing in the DevSynth project.

## Table of Contents

- [Background](#background)
- [The Problem](#the-problem)
- [The Solution](#the-solution)
  - [Enhanced Gherkin Parser](#enhanced-gherkin-parser)
  - [Updated Behavior Test Collection](#updated-behavior-test-collection)
  - [Marker Addition for Behavior Tests](#marker-addition-for-behavior-tests)
- [Usage Guidelines](#usage-guidelines)
- [Maintenance Guidelines](#maintenance-guidelines)

## Background

DevSynth uses pytest-bdd for behavior-driven development (BDD) testing. Behavior tests in pytest-bdd consist of:

1. **Feature files** (.feature): Written in Gherkin syntax, these files define scenarios that describe the expected behavior of the system.
2. **Step definition files** (.py): Python files that implement the steps defined in the feature files.

When pytest-bdd runs, it dynamically generates test functions from the scenarios in the feature files. This dynamic generation creates a discrepancy between the number of tests detected by pytest and the number detected by file parsing.

## The Problem

The original test infrastructure scripts had several limitations when dealing with behavior tests:

1. **Incomplete Gherkin parsing**: The original parser only detected regular Scenarios, missing Scenario Outlines and Examples.
2. **No understanding of pytest-bdd test generation**: The original parser didn't understand how pytest-bdd generates test functions from scenarios.
3. **Inability to add markers to generated tests**: The original scripts couldn't add markers to tests that are generated dynamically by pytest-bdd.

These limitations resulted in a large discrepancy between the number of behavior tests detected by pytest (3347) and the number detected by file parsing (38).

## The Solution

The solution consists of three main components:

1. **Enhanced Gherkin Parser**: A more robust parser for Gherkin feature files.
2. **Updated Behavior Test Collection**: An updated collect_behavior_tests function that uses the enhanced parser.
3. **Marker Addition for Behavior Tests**: A specialized function for adding markers to pytest-bdd generated tests.

### Enhanced Gherkin Parser

The enhanced Gherkin parser (`enhanced_gherkin_parser.py`) provides a more robust way to parse Gherkin feature files. Key features include:

- **Complete Gherkin syntax support**: Parses Feature, Background, Scenario, and Scenario Outline elements.
- **Examples table parsing**: Properly parses Examples tables in Scenario Outlines.
- **Test path generation**: Generates test paths that match how pytest-bdd would generate them.

Example usage:

```python
from enhanced_gherkin_parser import parse_feature_file, parse_feature_directory, count_tests, generate_test_paths

# Parse a single feature file
feature = parse_feature_file("path/to/feature.feature")

# Parse all feature files in a directory
features = parse_feature_directory("path/to/features")

# Count the number of tests that would be generated
test_count = count_tests(features)

# Generate test paths for all scenarios and examples
test_paths = generate_test_paths(features)
```

### Updated Behavior Test Collection

The `collect_behavior_tests` function in `common_test_collector.py` has been updated to use the enhanced Gherkin parser:

```python
def collect_behavior_tests(directory: str, use_cache: bool = True) -> List[str]:
    """
    Collect behavior tests from a directory.

    Args:
        directory: Directory to collect tests from
        use_cache: Whether to use cached results

    Returns:
        List of test paths
    """
    # Use the enhanced Gherkin parser
    try:
        # Import the enhanced Gherkin parser
        from enhanced_gherkin_parser import parse_feature_directory, generate_test_paths

        # Parse all feature files in the directory
        features = parse_feature_directory(directory)

        # Generate test paths for all scenarios and examples
        test_paths = generate_test_paths(features)

        return test_paths

    except ImportError:
        # Fall back to the original implementation if the enhanced parser is not available
        # ...
```

This ensures that the test collection accurately counts all tests, including those generated from Scenario Outlines with Examples.

### Marker Addition for Behavior Tests

The `add_markers_to_behavior_tests` function in `fix_test_infrastructure.py` provides a specialized way to add markers to pytest-bdd generated tests:

1. It groups tests by feature file.
2. It finds the test files that import scenarios from each feature file.
3. It adds markers to the step functions (@given, @when, @then) in those test files.

This approach ensures that markers are correctly applied to all behavior tests, even those generated dynamically by pytest-bdd.

## Usage Guidelines

### Adding Markers to Behavior Tests

To add markers to behavior tests, use the `fix_test_infrastructure.py` script with the `--add-markers` option:

```bash
python scripts/fix_test_infrastructure.py --add-markers --category behavior
```

This will:
1. Collect all behavior tests using the enhanced Gherkin parser.
2. Find tests without markers.
3. Add 'medium' markers to all unmarked tests.

### Verifying Behavior Test Counts

To verify that behavior test counts match between pytest and file parsing:

```bash
python scripts/fix_test_infrastructure.py --verify --category behavior
```

This will:
1. Collect tests using pytest.
2. Collect tests using file parsing (with the enhanced Gherkin parser).
3. Compare the counts and report any discrepancies.

## Maintenance Guidelines

### Adding New Behavior Tests

When adding new behavior tests:

1. **Feature files**: Place them in the `tests/behavior/features` directory or a subdirectory.
2. **Step definition files**: Place them in the `tests/behavior/steps` directory.
3. **Test files**: Create a test file that imports the scenarios from the feature file.

Example test file:

```python
import os
from pytest_bdd import scenarios

# Get the absolute path to the feature file
feature_file = os.path.join(
    os.path.dirname(__file__), "features", "general", "my_feature.feature"
)

# Load the scenarios from the feature file
scenarios(feature_file)
```

### Adding Markers to New Behavior Tests

To ensure consistent marker usage:

1. Add markers to step functions in the step definition files:

```python
@pytest.mark.medium
@given("some precondition")
def some_precondition():
    # Implementation
```

2. Run the `fix_test_infrastructure.py` script with the `--add-markers` option to add markers to any unmarked tests.

### Troubleshooting

If you encounter issues with behavior test parsing or marker addition:

1. **Verify feature file syntax**: Ensure that your feature files follow the Gherkin syntax correctly.
2. **Check step definition files**: Ensure that step functions are properly decorated with @given, @when, @then.
3. **Run with --verbose**: Use the `--verbose` option to see detailed information about what the scripts are doing.
4. **Generate reports**: Use the `--report` option to generate detailed reports of test counts and marker detection.

## Conclusion

The enhanced behavior test parsing solution addresses the discrepancies between pytest-bdd test detection and file parsing. By properly parsing Gherkin feature files and understanding how pytest-bdd generates test functions, it ensures accurate test counts and proper marker management for behavior tests.
