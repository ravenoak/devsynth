---
title: "Test Stabilization Tools"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "developer-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Test Stabilization Tools

This document provides information about the test stabilization tools created during Phase 1 of the DevSynth project. These tools are designed to help identify and fix common issues in test files.

## Overview

During the test stabilization phase, we identified several common issues in test files:

1. Missing pytest imports
2. Inconsistent method signatures in test classes
3. Indentation issues
4. Syntax errors

To address these issues, we created three scripts:

1. `fix_pytest_imports.py`: Adds missing pytest imports to test files
2. `fix_test_method_signatures.py`: Fixes inconsistent method signatures in test classes
3. `fix_test_syntax_errors.py`: Fixes common syntax errors in test files

Additional tools assist with broader stabilization tasks:

4. `fix_flaky_tests.py`: Detects and resolves common flaky-test patterns
5. `incremental_test_categorization.py`: Measures runtime and applies `fast`, `medium`, or `slow` markers
6. `devsynth run-pipeline`: Runs categorized tests with optional parallelism and HTML reporting

## Usage

### Fix Missing Pytest Imports

```bash
python scripts/fix_pytest_imports.py [directory]
```

This script scans test files for usage of pytest decorators without corresponding imports and adds the necessary import statements. If no directory is specified, it will scan the `tests` directory.

Example:

```bash
python scripts/fix_pytest_imports.py tests/unit
```

### Fix Method Signature Issues

```bash
python scripts/fix_test_method_signatures.py [directory]
```

This script identifies test classes with inconsistent use of 'self' parameter and adds 'self' to methods that are missing it. If no directory is specified, it will scan the `tests` directory.

Example:

```bash
python scripts/fix_test_method_signatures.py tests/unit/interface
```

### Fix Syntax Errors

```bash
python scripts/fix_test_syntax_errors.py [directory]
```

This script identifies and fixes common syntax errors in test files, such as:
- Missing or incorrect imports
- Indentation issues
- Incorrect function signatures
- Docstring formatting issues

If no directory is specified, it will scan the `tests` directory.

Example:

```bash
python scripts/fix_test_syntax_errors.py tests/behavior/steps
```

### Fix Flaky Tests

```bash
python scripts/fix_flaky_tests.py --module tests/unit/interface --pattern isolation
```

This script scans tests for mocking, isolation, and state issues that can cause nondeterministic failures. Use `--dry-run` to preview changes or `--report` to generate a summary of detected problems.

### Incremental Test Categorization

```bash
python scripts/incremental_test_categorization.py --update --batch-size 10
```

The categorization tool measures execution time in batches and updates test files with speed markers. Progress is saved to `.test_categorization_progress.json`, allowing subsequent runs to continue where they left off.

### Run All Tests

```bash
devsynth run-pipeline --fast --medium --report
```

This wrapper around `pytest` respects speed markers, can segment tests for faster feedback, and optionally produces an HTML report under `test_reports/`.

## Common Test Issues and Solutions

### Missing Pytest Imports

**Issue**: Test files use pytest decorators or functions but don't import pytest.

**Solution**: Add `import pytest` at the top of the file.

```python
# Before
@pytest.mark.medium
def test_something():
    pass

# After
import pytest

@pytest.mark.medium
def test_something():
    pass
```

### Inconsistent Method Signatures

**Issue**: Test classes have methods with inconsistent use of 'self' parameter.

**Solution**: Ensure all methods in a test class include 'self' as the first parameter.

```python
# Before
class TestSomething:
    def test_method1(self):
        pass

    def test_method2():  # Missing 'self'
        pass

# After
class TestSomething:
    def test_method1(self):
        pass

    def test_method2(self):  # Added 'self'
        pass
```

### Indentation Issues

**Issue**: Test files have inconsistent indentation, especially in docstrings.

**Solution**: Fix indentation to follow Python's standard 4-space indentation.

```python
# Before
def test_something():
    """Test something.
import pytest  # Incorrectly indented import in docstring

    ReqID: N/A"""
    pass

# After
def test_something():
    """Test something.

    ReqID: N/A"""
    pass
```

### Pytest Import in Docstrings

**Issue**: Some test files have pytest imports inside docstrings.

**Solution**: Move the import to the top of the file and remove it from the docstring.

```python
# Before
def test_something():
    """Test something.
import pytest

    ReqID: N/A"""
    pass

# After
import pytest

def test_something():
    """Test something.

    ReqID: N/A"""
    pass
```

## Best Practices for Test Files

1. **Always import pytest at the top of test files**: This ensures that pytest decorators and functions are available throughout the file.

2. **Use consistent method signatures in test classes**: All methods in a test class should include 'self' as the first parameter.

3. **Follow Python's standard 4-space indentation**: This makes the code more readable and avoids syntax errors.

4. **Keep docstrings clean**: Don't include imports or other code in docstrings.

5. **Use fixtures for setup and teardown**: This helps ensure proper test isolation and reduces flaky tests.

6. **Add appropriate markers to tests**: This helps categorize tests and makes it easier to run specific subsets of tests.

## Maintenance

These scripts are designed to be run as needed to fix common issues in test files. They can be run individually or as part of a larger test stabilization effort.

If you encounter new types of issues that are not addressed by these scripts, consider extending them or creating new scripts to address those issues.

---

_Last updated: August 2, 2025_
