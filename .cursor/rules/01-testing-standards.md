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
@pytest.mark.fast      # < 1s - unit tests, simple validations
@pytest.mark.medium    # 1s-5s - integration tests, moderate computation
@pytest.mark.slow      # > 5s - end-to-end tests, heavy computation, external APIs
```

**Never use module-level `pytestmark` for speed categories.**

### Speed Marker Examples

```python
# Fast: Simple unit test
@pytest.mark.fast
def test_memory_item_creation():
    """Test basic MemoryItem instantiation."""
    item = MemoryItem(content="test", metadata={})
    assert item.content == "test"

# Medium: Integration test with file I/O
@pytest.mark.medium
def test_config_file_loading(tmp_path):
    """Test configuration file parsing."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("key: value")
    config = load_config(config_file)
    assert config["key"] == "value"

# Slow: End-to-end test with external service
@pytest.mark.slow
@pytest.mark.requires_resource("openai")
def test_agent_conversation():
    """Test full agent conversation workflow."""
    agent = ConversationAgent()
    response = agent.process("Hello, how are you?")
    assert len(response) > 0
```

### Validation
```bash
# Check all tests have speed markers
poetry run python scripts/verify_test_markers.py

# Check only changed files
poetry run python scripts/verify_test_markers.py --changed

# Pre-commit hook will fail if markers are missing
poetry run pre-commit run --files test_file.py
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

**Test Execution Philosophy:**

**Thesis**: Comprehensive testing ensures code reliability and maintains development velocity through early issue detection.

**Antithesis**: Over-testing or slow test suites can hinder development speed and create maintenance burden.

**Synthesis**: Balanced testing strategy with speed markers, resource flags, and parallel execution ensures both reliability and development efficiency.

### Test Commands

**Primary Test Runner (Recommended):**
```bash
# Run tests by speed category (preferred)
poetry run devsynth run-tests --speed=fast
poetry run devsynth run-tests --speed=medium
poetry run devsynth run-tests --speed=slow

# Smoke test (fastest sanity check)
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

# With HTML coverage report
poetry run devsynth run-tests --report

# Run specific test markers
poetry run devsynth run-tests --speed=fast -m "unit and not gui"
```

**Direct Pytest (Advanced Usage):**
```bash
# Run specific test directories
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/behavior/

# Run by markers
poetry run pytest -m "fast and not gui"
poetry run pytest -m "requires_resource and chromadb"

# Run with custom options
poetry run pytest --tb=short --strict-markers
```

### Test Environment Setup

**Required Environment Variables:**
```bash
# Enable optional test resources
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true

# Enable property testing (opt-in)
export DEVSYNTH_PROPERTY_TESTING=true

# Configure test parallelism
export PYTEST_XDIST_WORKER_COUNT=4
```

**Virtual Environment Verification:**
```bash
# Ensure tests run in Poetry environment
poetry run which python  # Should show .venv/bin/python
poetry run which pytest  # Should show .venv/bin/pytest

# Check available test extras
poetry run pytest --markers | grep "requires_resource"
```

## Test Documentation

- Each test class needs docstring
- Each test method needs docstring
- Use descriptive variable names

## Templates

Available in `templates/`:
- `templates/unit/test_template.py`
- `templates/integration/integration_test_template.py`

