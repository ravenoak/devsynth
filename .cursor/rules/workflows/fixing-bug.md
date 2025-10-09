---
description: Workflow for fixing bugs with test-first approach
globs:
  - "**/*"
alwaysApply: false
---

# Workflow: Fixing a Bug

## Overview

Fix bugs using test-first methodology to ensure the bug is truly fixed and won't regress.

## Step-by-Step Workflow

### 1. Reproduce the Bug

**First, understand and reproduce the bug:**

```bash
# Try to reproduce with existing tests
poetry run pytest tests/ -k "<relevant_keyword>"

# Run specific module tests
poetry run pytest tests/unit/<module>/ -v

# Check if bug is in integration or behavior
poetry run pytest tests/integration/ -v
poetry run pytest tests/behavior/ -v
```

Document reproduction steps in issue:

```markdown
## Reproduction Steps

1. Setup: <initial state>
2. Action: <what triggers bug>
3. Expected: <what should happen>
4. Actual: <what actually happens>
5. Impact: <who/what is affected>

## Environment
- Python version: 3.12.x
- DevSynth version: 0.1.0a1
- OS: <operating system>
- Relevant extras: <chromadb, api, etc.>
```

### 2. Create Branch

```bash
git checkout -b fix/<bug-description>
```

### 3. Write Failing Test (Proves Bug Exists)

**Most important step - write test that fails due to the bug:**

Location: `tests/unit/<module>/test_<component>.py` or appropriate test file

```python
"""Tests demonstrating and fixing bug #XXX."""
import pytest
from devsynth.application.<module> import <Class>


@pytest.mark.fast
def test_<bug_scenario>_should_not_fail():
    """ReqID: BUG-XXX - Test demonstrating the bug.
    
    Bug: <Brief description of bug>
    
    This test currently fails because <reason>.
    After fix, it should pass.
    """
    # Arrange - Setup that triggers bug
    instance = <Class>()
    problematic_input = <whatever triggers bug>
    
    # Act - Perform action that fails
    result = instance.method(problematic_input)
    
    # Assert - What should happen (currently fails)
    assert result is not None  # This fails before fix
    assert result == expected_value
```

### 4. Run Failing Test (Verify It Fails)

```bash
# Run the new test - should fail
poetry run pytest tests/unit/<module>/test_<component>.py::test_<bug_scenario> -v
```

**Expected**: Test should fail, proving bug exists

**If test passes**: Bug not correctly reproduced yet, refine test

### 5. Analyze Root Cause

Use dialectical reasoning:

**Thesis**: Original implementation assumed X
**Antithesis**: Bug shows X doesn't hold when Y
**Synthesis**: Need to handle Y case explicitly

Document in issue or PR:

```markdown
## Root Cause Analysis

**What went wrong:**
The implementation in `src/devsynth/<module>/<file>.py` line XX
assumes <assumption> which is violated when <condition>.

**Why it wasn't caught:**
- Existing tests didn't cover <edge case>
- Input validation missed <scenario>

**Impact:**
- Affects users when <condition>
- Severity: <Low/Medium/High>
```

### 6. Implement Fix

Location: `src/devsynth/<module>/<file>.py`

```python
def method(self, input_data: str) -> str:
    """Process input data.
    
    Args:
        input_data: Input to process
        
    Returns:
        Processed result
        
    Raises:
        ValueError: If input is invalid
    """
    # FIX: Handle edge case that caused bug #XXX
    if not input_data:
        raise ValueError("Input cannot be empty")
    
    # FIX: Add validation that was missing
    if not self._is_valid(input_data):
        raise ValueError(f"Invalid input: {input_data}")
    
    # Original logic (possibly with adjustments)
    result = self._process(input_data)
    return result
```

**Keep changes minimal - only fix the bug**

### 7. Run Test Suite

```bash
# Run the failing test - should now pass
poetry run pytest tests/unit/<module>/test_<component>.py::test_<bug_scenario> -v

# Run all related tests
poetry run pytest tests/unit/<module>/ -v

# Run fast suite
poetry run devsynth run-tests --speed=fast

# Run full suite if appropriate
poetry run devsynth run-tests --speed=medium
```

**All tests should pass**

### 8. Add Regression Tests

Add additional tests to prevent regression:

```python
@pytest.mark.fast
def test_<bug>_with_edge_case_a():
    """ReqID: BUG-XXX - Verify fix handles edge case A."""
    # Test edge case
    pass

@pytest.mark.fast  
def test_<bug>_with_edge_case_b():
    """ReqID: BUG-XXX - Verify fix handles edge case B."""
    # Test another edge case
    pass

@pytest.mark.medium
@pytest.mark.parametrize("input,expected", [
    ("case1", "result1"),
    ("case2", "result2"),
    (None, ValueError),  # Bug scenario
])
def test_<bug>_various_inputs(input, expected):
    """ReqID: BUG-XXX - Comprehensive regression test."""
    # Parametrized test for multiple scenarios
    pass
```

### 9. Update Documentation

#### If Bug Revealed Gap in Docs

Update relevant documentation:
- User guides if usage unclear
- API docs if behavior misunderstood
- Architecture docs if design unclear

#### Add to Changelog

Update `CHANGELOG.md`:

```markdown
## [Unreleased]

### Fixed
- Fixed <bug description> that caused <problem> when <condition> (#XXX)
```

#### Document in Rationale (if significant)

If bug fix required significant test changes:
`docs/rationales/test_fixes.md`

### 10. Run Quality Checks

```bash
# Format
poetry run black .
poetry run isort .

# Lint
poetry run flake8 src/ tests/

# Type check
poetry run mypy src tests

# Verify markers
poetry run python scripts/verify_test_markers.py --changed

# Audit
poetry run python scripts/dialectical_audit.py
```

### 11. Create Commit

```bash
git add .

git commit -m "fix(<scope>): <brief description of fix>

Fixed <bug description> that occurred when <condition>.

Root cause: <explanation>
Solution: <what changed>

Added regression tests to prevent recurrence:
- test_<bug>_with_edge_case_a
- test_<bug>_with_edge_case_b

Dialectical analysis:
- Thesis: Original code assumed <X>
- Antithesis: Bug revealed <Y> case violated assumption
- Synthesis: Added validation for <Y> case

Closes #<bug_issue_number>
"
```

### 12. Run Pre-Commit Hooks

```bash
poetry run pre-commit run --files <changed_files>
```

### 13. Push and Create PR

```bash
git push origin fix/<bug-description>
```

**PR Description Template:**

```markdown
## Bug Fix Summary

Fixes #<issue>

**Bug:** <Brief description>

**Root Cause:** <What went wrong>

**Solution:** <How it's fixed>

## Dialectical Analysis

- **Thesis**: Original implementation assumed X
- **Antithesis**: Bug showed Y case wasn't handled
- **Synthesis**: Added Y handling while preserving X benefits

## Testing Evidence

- [ ] Wrote failing test demonstrating bug
- [ ] Verified test fails before fix
- [ ] Implemented fix
- [ ] Verified test passes after fix
- [ ] Added regression tests
- [ ] All existing tests still pass

## Changes

- Modified: `src/devsynth/<module>/<file>.py`
- Added tests: `tests/unit/<module>/test_<component>.py`
- Updated: `CHANGELOG.md`

## Verification

```bash
# Reproduction before fix
poetry run pytest tests/unit/<module>/test_<bug>.py  # FAILED

# After fix
poetry run pytest tests/unit/<module>/test_<bug>.py  # PASSED
poetry run devsynth run-tests --speed=fast  # ALL PASSED
```

Closes #<issue>
```

## Bug Fix Checklist

- [ ] Bug reproduced reliably
- [ ] Reproduction steps documented
- [ ] Root cause identified
- [ ] Wrote failing test proving bug exists
- [ ] Verified test fails before fix
- [ ] Implemented minimal fix
- [ ] Verified failing test now passes
- [ ] All existing tests still pass
- [ ] Added regression tests
- [ ] Tests include speed markers
- [ ] Code formatted and linted
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated
- [ ] Dialectical audit resolved
- [ ] Conventional commit message
- [ ] PR linked to bug issue

## Anti-Patterns

❌ **Don't fix without failing test**
✅ Write test that fails first

❌ **Don't make unnecessary changes**
✅ Minimal fix for the specific bug

❌ **Don't skip regression tests**
✅ Add tests to prevent recurrence

❌ **Don't ignore related bugs**
✅ Check for similar issues

## Special Cases

### Security Bug

If security-related:

```bash
# Run security audit
poetry run python scripts/security_audit.py

# Verify security policy compliance
poetry run python scripts/verify_security_policy.py
```

Mark issue with `security` label and follow security policy.

### Performance Bug

If performance-related:

```bash
# Run benchmark
DEVSYNTH_ENABLE_BENCHMARKS=true \
pytest -p benchmark tests/performance/ -q

# Compare before/after
```

Add performance regression test if appropriate.

### Integration Bug

If involves multiple components:

```bash
# Run integration tests
poetry run pytest tests/integration/ -v

# May need medium/slow tests
poetry run devsynth run-tests --speed=medium
```

Consider adding integration test to prevent regression.

## Example Bug Fixes

See examples:
- `tests/unit/application/memory/` - Memory system bug fixes
- `docs/rationales/test_fixes.md` - Documented significant fixes

