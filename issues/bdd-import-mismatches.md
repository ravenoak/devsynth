# BDD Framework Import Mismatches

Title: BDD test files import 'behave' instead of 'pytest_bdd'
Date: 2025-10-27
Status: open
Priority: critical
Affected Area: tests/behavior

## Problem Statement

Three BDD test files are importing from the wrong framework:
- `tests/behavior/steps/test_cursor_integration_steps.py`
- `tests/behavior/steps/test_enhanced_knowledge_graph_steps.py`
- `tests/behavior/steps/test_memetic_unit_steps.py`

These files use `from behave import given, when, then` but the project uses `pytest-bdd`, not `behave`. This causes ImportError during test collection.

## Root Cause

Historical migration from behave to pytest-bdd was incomplete - these files were not updated with the correct imports.

## Impact

- Blocks test collection (ImportError)
- Prevents smoke runs and coverage generation
- Delays release v0.1.0a1

## Solution

Change imports in all three files from:
```python
from behave import given, when, then
```

To:
```python
from pytest_bdd import given, when, then
```

## Acceptance Criteria

- `poetry run pytest --collect-only -q` shows no ImportError for these files
- BDD step definitions load correctly
- Test collection completes without errors
