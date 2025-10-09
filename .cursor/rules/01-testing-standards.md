---
description: Comprehensive testing standards for unit, integration, and BDD tests
globs:
  - "tests/**/*"
  - "**/*test*.py"
alwaysApply: false
---

# DevSynth Testing Standards

## Test Organization

```
tests/
├── unit/                  # Unit tests (isolated components)
├── integration/           # Integration tests (component interactions)
├── behavior/              # BDD tests (end-to-end scenarios)
│   ├── features/          # Gherkin feature files
│   └── steps/             # Step definitions
├── property/              # Property-based tests (opt-in)
├── performance/           # Performance benchmarks (opt-in)
└── conftest.py            # Shared fixtures
```

## Mandatory: Speed Markers

**Every test function must have exactly one speed marker:**

```python
@pytest.mark.fast      # < 1s
@pytest.mark.medium    # 1s-5s
@pytest.mark.slow      # > 5s
```

**Never use module-level `pytestmark` for speed categories.**

### Validation
```bash
poetry run python scripts/verify_test_markers.py --changed
```

## Unit Test Pattern

```python
import pytest
from unittest.mock import MagicMock

class TestMyClass:
    """Tests for MyClass."""

    @pytest.fixture
    def my_instance(self):
        """Fixture providing MyClass instance."""
        return MyClass()

    @pytest.mark.fast
    def test_method_with_valid_input(self, my_instance):
        """Test method with valid input."""
        # Arrange
        input_data = "valid"
        
        # Act
        result = my_instance.method(input_data)
        
        # Assert
        assert result == expected_value
```

**Key principles:**
- Arrange-Act-Assert pattern
- Descriptive names: `test_<method>_<scenario>`
- Docstrings explaining the test
- Use fixtures for setup
- Mock external dependencies

## Integration Test Pattern

```python
@pytest.mark.medium
@pytest.mark.requires_resource("openai")
def test_integration_scenario():
    """Test integration between components."""
    # Test actual component interactions
    # Use real implementations where possible
```

## Resource Markers

Guard tests requiring optional dependencies:

```python
@pytest.mark.fast
@pytest.mark.requires_resource("chromadb")
def test_chromadb_feature():
    """Test ChromaDB functionality."""
    pytest.importorskip("chromadb")
    # Test implementation
```

Enable via environment:
```bash
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
```

## Context Markers

Combine speed with context markers:

```python
@pytest.mark.fast
@pytest.mark.no_network
@pytest.mark.unit
def test_offline_feature():
    """Test feature without network."""
    pass

@pytest.mark.slow
@pytest.mark.integration
def test_full_workflow():
    """Test complete workflow."""
    pass
```

## Property-Based Tests

Opt-in via environment:

```python
from hypothesis import given, strategies as st

@pytest.mark.property
@pytest.mark.medium
@given(st.text(min_size=1))
def test_property(content):
    """Property test for invariant."""
    # Test implementation
```

```bash
export DEVSYNTH_PROPERTY_TESTING=true
```

## Coverage Standards

- **Target**: ≥90% aggregate (enforced by `--cov-fail-under=90`)
- All public methods must have tests
- Test edge cases and error paths
- Use parameterized tests for variations

## Mocking

```python
from unittest.mock import MagicMock, patch

@pytest.mark.fast
def test_with_mock():
    """Test with mocked dependency."""
    with patch('module.ExternalService') as mock:
        mock.return_value.method.return_value = expected
        result = function_using_service()
        assert result == expected
```

## Running Tests

```bash
# Preferred: via CLI wrapper
poetry run devsynth run-tests --speed=fast

# Smoke test
poetry run devsynth run-tests --smoke --speed=fast --no-parallel

# With report
poetry run devsynth run-tests --report

# Direct pytest
poetry run pytest tests/unit/
poetry run pytest -m "fast and not gui"
```

## Test Documentation

- Each test class needs docstring
- Each test method needs docstring
- Use descriptive variable names

## Templates

Available in `templates/`:
- `templates/unit/test_template.py`
- `templates/integration/integration_test_template.py`

