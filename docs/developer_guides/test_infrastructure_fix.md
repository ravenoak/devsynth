---
title: "Test Infrastructure Fix Guide"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Test Infrastructure Fix Guide

This document provides information about the `fix_test_infrastructure.py` script, which addresses critical issues in the DevSynth test infrastructure.

## Overview

The `fix_test_infrastructure.py` script is designed to resolve several key issues with the test infrastructure:

1. Test count discrepancies between different collection methods
2. Marker detection discrepancies between files and pytest
3. Missing markers on tests
4. Inconsistent marker formats

## Installation

The script is located in the `scripts` directory of the DevSynth repository. No additional installation is required beyond the standard DevSynth development environment.

## Usage

```bash
python scripts/fix_test_infrastructure.py [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--verify` | Verify test counts and marker detection |
| `--fix-markers` | Fix marker detection issues |
| `--add-markers` | Add markers to tests without running them |
| `--module MODULE` | Specific module to process (e.g., tests/unit/interface) |
| `--category CATEGORY` | Test category to process (unit, integration, behavior, all) |
| `--report` | Generate a detailed report |
| `--verbose` | Show detailed information |
| `--apply` | Apply changes without confirmation (use with caution) |
| `--dry-run` | Show changes without modifying files (default for --add-markers) |

## Common Use Cases

### Verifying Test Counts

To check for discrepancies between test counts reported by pytest and those found by parsing files:

```bash
python scripts/fix_test_infrastructure.py --verify
```

This will output a summary of test counts for each category and highlight any discrepancies.

For a more detailed report:

```bash
python scripts/fix_test_infrastructure.py --verify --report --verbose
```

This will generate a JSON report file with detailed information about test counts.

### Fixing Marker Detection Issues

To identify and fix issues with marker detection:

```bash
python scripts/fix_test_infrastructure.py --fix-markers
```

This will identify tests where markers are present in the files but not detected by pytest, and vice versa. It will then fix the marker format for tests where markers are not being detected correctly.

For a more targeted approach:

```bash
python scripts/fix_test_infrastructure.py --fix-markers --module tests/unit/interface --verbose
```

This will only process tests in the specified module and show detailed information about the changes being made.

### Adding Markers to Unmarked Tests

To add markers to tests that don't have any:

```bash
python scripts/fix_test_infrastructure.py --add-markers
```

By default, this will run in dry-run mode and show which tests would be modified without actually making changes. It will prompt for confirmation before applying changes.

To apply changes without confirmation:

```bash
python scripts/fix_test_infrastructure.py --add-markers --apply
```

To explicitly run in dry-run mode:

```bash
python scripts/fix_test_infrastructure.py --add-markers --dry-run
```

To focus on a specific category:

```bash
python scripts/fix_test_infrastructure.py --add-markers --category unit --verbose
```

## Generated Reports

When using the `--report` option, the script generates JSON report files:

- `test_infrastructure_report.json`: Contains information about test counts and marker detection
- `marker_discrepancy_report.json`: Lists tests with marker discrepancies

These reports can be used for further analysis or to track progress over time.

## Implementation Details

The script uses several approaches to ensure accurate test detection and marker handling:

1. **AST-based parsing**: Uses Python's Abstract Syntax Tree (AST) module to reliably parse test files and detect test functions, methods, and markers.
2. **Pytest integration**: Uses pytest's collection mechanism to get the "ground truth" about which tests and markers are detected by pytest.
3. **Marker standardization**: Ensures markers are applied in a consistent format that pytest can detect.

## Best Practices

1. **Always run with `--verify` first**: Before making any changes, verify the current state of the test infrastructure.
2. **Use `--verbose` for detailed information**: This helps understand what the script is doing and which tests it's processing.
3. **Use `--dry-run` when adding markers**: This allows you to see what changes would be made without actually modifying files.
4. **Focus on specific modules or categories**: For large codebases, it's often better to process one module or category at a time.
5. **Generate reports for tracking progress**: Use the `--report` option to generate detailed reports that can be used to track progress over time.

## Troubleshooting

### Common Issues

1. **Script reports more tests than pytest**: This usually indicates that there are test functions or methods that pytest is not detecting as tests. Check for issues with test naming or imports.
2. **Marker discrepancies**: If markers are present in files but not detected by pytest, check the marker format and placement. The script can fix most of these issues automatically.
3. **Parsing errors**: If the script encounters errors parsing certain files, try running with `--verbose` to see which files are causing issues. You may need to fix syntax errors in those files manually.

### Getting Help

If you encounter issues with the script, please:

1. Run with `--verbose` to get more detailed information
2. Check the generated reports for specific issues
3. Consult the DevSynth development team for assistance

## Future Improvements

Planned improvements to the script include:

1. **Intelligent marker assignment**: Using heuristics to determine the appropriate marker (fast, medium, slow) based on test complexity and runtime.
2. **Integration with CI/CD**: Running the script automatically as part of the CI/CD pipeline to ensure consistent test infrastructure.
3. **Extended reporting**: More detailed reports on test infrastructure status and improvements over time.

## Related Documentation

- [Test Best Practices Guide](./test_best_practices.md)
- [Test Infrastructure Architecture](../architecture/test_infrastructure.md)
- [Test Categorization Guide](./test_categorization.md)

---

_Last updated: August 2, 2025_
