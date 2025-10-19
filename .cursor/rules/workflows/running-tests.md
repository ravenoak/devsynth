---
description: Comprehensive guide for running and organizing tests
globs:
  - "tests/**/*"
alwaysApply: false
---

# Workflow: Running Tests

## Quick Reference

### By Speed Category (Recommended)

```bash
# Fast tests only (< 1s each) - run frequently
poetry run devsynth run-tests --speed=fast

# Medium tests (1-5s each) - run before commits
poetry run devsynth run-tests --speed=medium

# Slow tests (> 5s each) - run before PRs
poetry run devsynth run-tests --speed=slow

# All tests
poetry run devsynth run-tests --speed=fast --speed=medium --speed=slow
```

### By Test Type

```bash
# Unit tests only
poetry run devsynth run-tests --target unit-tests --speed=fast

# Integration tests only
poetry run devsynth run-tests --target integration-tests --speed=fast

# BDD behavior tests only
poetry run devsynth run-tests --target behavior-tests --speed=fast
```

### Special Modes

```bash
# Smoke test (minimal plugins, fastest)
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# With HTML report
poetry run devsynth run-tests --report --speed=fast

# With coverage
poetry run devsynth run-tests --speed=fast
# (coverage enabled by default)
```

## Detailed Test Execution

### Development Workflow Tests

#### During Active Development

Run frequently while coding:

```bash
# Fast tests only - should complete in seconds
poetry run devsynth run-tests --speed=fast

# Or specific module
poetry run pytest tests/unit/application/memory/ -m fast
```

#### Before Committing

Run broader test suite:

```bash
# Fast and medium tests
poetry run devsynth run-tests --speed=fast --speed=medium

# Verify test markers
poetry run python scripts/verify_test_markers.py --changed

# Run pre-commit
poetry run pre-commit run --files <changed>
```

#### Before Creating PR

Run comprehensive tests:

```bash
# All speed categories
poetry run devsynth run-tests --speed=fast --speed=medium --speed=slow

# Run verification scripts
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/dialectical_audit.py

# Full pre-commit
poetry run pre-commit run --all-files
```

### Test Type Execution

#### Unit Tests

Test individual components in isolation:

```bash
# All unit tests (fast)
poetry run pytest tests/unit/ -m fast

# Specific module
poetry run pytest tests/unit/application/memory/ -v

# With coverage
poetry run pytest tests/unit/ --cov=src/devsynth --cov-report=term-missing
```

#### Integration Tests

Test component interactions:

```bash
# All integration tests
poetry run pytest tests/integration/ -m "not slow"

# With specific resources
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
poetry run pytest tests/integration/memory/ -m requires_resource

# API integration tests
poetry run pytest tests/integration/api/ -v
```

#### BDD Behavior Tests

Test end-to-end scenarios:

```bash
# All behavior tests
poetry run pytest tests/behavior/

# Specific feature
poetry run pytest tests/behavior/features/memory_crud.feature

# By tag
poetry run pytest tests/behavior/ -m smoke
poetry run pytest tests/behavior/ -m "fast and integration"

# Verbose with Gherkin output
poetry run pytest tests/behavior/ -v --gherkin-terminal-reporter
```

### Marker-Based Execution

#### By Speed

```bash
# Fast only
poetry run pytest -m fast

# Medium only
poetry run pytest -m medium

# Slow only
poetry run pytest -m slow

# Exclude slow
poetry run pytest -m "not slow"
```

#### By Context

```bash
# Smoke tests only
poetry run pytest -m smoke

# No network tests
poetry run pytest -m no_network

# GUI tests (usually skipped)
poetry run pytest -m gui

# Integration tests
poetry run pytest -m integration
```

#### By Resource

```bash
# Chromadb tests (with resource enabled)
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
poetry run pytest -m resource_chromadb

# OpenAI tests (with resource enabled)
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
poetry run pytest -m resource_openai

# Memory backend tests
export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
export DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true
poetry run pytest -m "resource_tinydb or resource_lmdb"
```

### Optional Test Types

#### Property-Based Tests

Opt-in via environment flag:

```bash
# Enable property tests
export DEVSYNTH_PROPERTY_TESTING=true

# Run property tests
poetry run pytest tests/property/ -m property

# With medium speed
poetry run pytest tests/property/ -m "property and medium"
```

#### Performance Benchmarks

Opt-in via environment flag:

```bash
# Enable benchmarks
export DEVSYNTH_ENABLE_BENCHMARKS=true

# Run with benchmark plugin
pytest -p benchmark tests/performance/ -q

# Save benchmark results
pytest -p benchmark --benchmark-save=baseline tests/performance/
```

### Coverage Reports

#### Generate Coverage

```bash
# Terminal report
poetry run pytest --cov=src --cov-report=term-missing

# HTML report
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html

# JSON report (for CI)
poetry run pytest --cov=src --cov-report=json:test_reports/coverage.json

# XML report (for tooling)
poetry run pytest --cov=src --cov-report=xml
```

#### Coverage Options

```bash
# Fail if below threshold (90% default)
poetry run pytest --cov=src --cov-fail-under=90

# Show covered lines
poetry run pytest --cov=src --cov-report=term

# Show missing lines
poetry run pytest --cov=src --cov-report=term-missing:skip-covered
```

### Parallel Execution

#### Speed Up Tests

```bash
# Auto-detect CPU count
poetry run pytest -n auto

# Specific number of workers
poetry run pytest -n 4

# Load balancing
poetry run pytest -n auto --dist loadscope
```

#### Disable Parallel

```bash
# Smoke mode (no parallel)
poetry run devsynth run-tests --smoke --no-parallel

# Specific tests that need isolation
poetry run pytest tests/integration/memory/ -m isolation --no-parallel
```

### Debugging Tests

#### Verbose Output

```bash
# Very verbose
poetry run pytest -vv

# Show local variables on failure
poetry run pytest -l

# Show print statements
poetry run pytest -s

# Full output
poetry run pytest -vv -s -l
```

#### Stop on Failure

```bash
# Stop on first failure
poetry run pytest -x

# Stop after N failures
poetry run pytest --maxfail=3

# Drop into debugger on failure
poetry run pytest --pdb
```

#### Run Specific Tests

```bash
# By file
poetry run pytest tests/unit/application/memory/test_multi_layered.py

# By class
poetry run pytest tests/unit/application/memory/test_multi_layered.py::TestMultiLayered

# By method
poetry run pytest tests/unit/application/memory/test_multi_layered.py::TestMultiLayered::test_store

# By keyword
poetry run pytest -k "memory and store"

# By marker
poetry run pytest -m "fast and unit"
```

### Test Organization Verification

#### Verify Test Structure

```bash
# Check organization
poetry run python tests/verify_test_organization.py

# Verify markers
poetry run python scripts/verify_test_markers.py

# Generate marker report
poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json

# Check changed files only
poetry run python scripts/verify_test_markers.py --changed
```

### CI Simulation

#### Run Like CI

```bash
# Smoke test (CI entry check)
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# Fast tests (CI quick feedback)
poetry run devsynth run-tests --speed=fast

# Full suite (CI comprehensive)
poetry run devsynth run-tests --speed=fast --speed=medium --speed=slow

# With all verifications
poetry run pre-commit run --all-files
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/dialectical_audit.py
```

## Test Fixtures and Setup

### Using Shared Fixtures

```python
# From conftest.py
def test_with_shared_fixture(global_test_isolation):
    """Test using global isolation fixture."""
    # Test automatically isolated
    pass

# From conftest_extensions.py
def test_with_feature_marker(feature_memory):
    """Test using feature marker fixture."""
    pass
```

### Environment Variables

```bash
# Enable resources
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true

# Enable property tests
export DEVSYNTH_PROPERTY_TESTING=true

# Enable benchmarks
export DEVSYNTH_ENABLE_BENCHMARKS=true

# Coverage threshold
export DEVSYNTH_COV_FAIL_UNDER=90
```

## Common Test Patterns

### Test Parametrization

```python
@pytest.mark.fast
@pytest.mark.parametrize("input,expected", [
    ("value1", "result1"),
    ("value2", "result2"),
    (None, ValueError),
])
def test_with_params(input, expected):
    """Test with multiple inputs."""
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            function(input)
    else:
        assert function(input) == expected
```

### Test Isolation

```python
@pytest.mark.fast
@pytest.mark.isolation
def test_requires_isolation():
    """Test that needs to run separately."""
    # Test that modifies global state
    pass
```

### Resource Guards

```python
@pytest.mark.medium
@pytest.mark.requires_resource("chromadb")
def test_chromadb_feature():
    """Test requiring ChromaDB."""
    pytest.importorskip("chromadb")
    # Test implementation
```

## Troubleshooting

### Tests Hang

```bash
# Add timeout
poetry run pytest --timeout=30

# Identify hanging test
poetry run pytest -v --timeout=10
```

### Import Errors

```bash
# Verify environment
poetry env info --path
poetry install --with dev --extras "tests retrieval chromadb api"

# Clear cache
poetry run pytest --cache-clear
```

### Marker Errors

```bash
# Verify markers registered
poetry run pytest --markers

# Validate test markers
poetry run python scripts/verify_test_markers.py --report
```

### Coverage Issues

```bash
# Debug coverage
poetry run pytest --cov=src --cov-report=term-missing -v

# Specific module coverage
poetry run pytest tests/unit/application/memory/ --cov=src/devsynth/application/memory
```

## Test Development Checklist

When writing new tests:

- [ ] Include exactly one speed marker
- [ ] Add docstring with ReqID reference
- [ ] Follow Arrange-Act-Assert pattern
- [ ] Use descriptive test name
- [ ] Use appropriate fixtures
- [ ] Mock external dependencies
- [ ] Add context markers as needed
- [ ] Verify test fails appropriately
- [ ] Verify test passes when fixed
- [ ] Run `verify_test_markers.py --changed`

## Integration with Development Tools

### Pre-Commit Hook

Automatically runs on changed test files:

```bash
# Install hook
poetry run pre-commit install

# Runs verify_test_markers.py on commit
```

### IDE Integration

Most IDEs support pytest:

- Run individual tests
- Debug tests
- View coverage inline
- Jump to failures

### CI Pipeline

GitHub Actions runs:
- Smoke tests (fast entry check)
- Unit + integration tests (comprehensive)
- Typing + lint (quality)
- Marker verification (enforcement)
