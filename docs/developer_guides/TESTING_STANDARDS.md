---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- developer-guide

title: DevSynth Testing Standards
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; DevSynth Testing Standards
</div>

# DevSynth Testing Standards

This document outlines the testing standards and best practices for the DevSynth project. Following these standards ensures that tests are consistent, reliable, and maintainable.

## Testing Levels

DevSynth uses three levels of testing:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test interactions between components
3. **Behavior Tests**: Test end-to-end functionality from a user perspective


### Unit Tests

Unit tests focus on testing individual functions, methods, or classes in isolation. They should be fast, isolated, and cover all code paths.

- **Location**: `tests/unit/`
- **Naming Convention**: `test_*.py`
- **Framework**: pytest


### Integration Tests

Integration tests verify that different components work together correctly. They test the interactions between components and ensure that they integrate properly.

- **Location**: `tests/integration/`
- **Naming Convention**: `test_*.py`
- **Framework**: pytest


### Behavior Tests

Behavior tests (BDD) verify that the system behaves as expected from a user's perspective. They are written in a natural language format using Gherkin syntax.

- **Location**: `tests/behavior/`
- **Feature Files**: `tests/behavior/features/*.feature`
- **Step Definitions**: `tests/behavior/steps/*.py`
- **Framework**: pytest-bdd


## Test Organization

Tests should be organized to mirror the structure of the source code:

```text
src/devsynth/domain/models/user.py
tests/unit/domain/models/test_user.py
```

This makes it easy to find tests for a specific module and ensures that all modules have corresponding tests.

## Test Categorization

Tests are categorized by speed to help developers run appropriate subsets of tests:

- **Fast Tests**: Execution time < 1s
- **Medium Tests**: Execution time between 1s and 5s
- **Slow Tests**: Execution time > 5s


To run tests by category:

```bash

# Run only fast tests

pytest --speed=fast

# Run only medium tests

pytest --speed=medium

# Run only slow tests

pytest --speed=slow

# Run all tests

pytest --speed=all
```

## Test Isolation

Tests should be isolated from each other and from the environment. This ensures that tests are reliable and can be run in any order.

### Fixtures

Use pytest fixtures for setup and teardown:

```python
@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = User(name="Test User", email="test@example.com")
    return user

def test_user_name(sample_user):
    """Test that the user name is correct."""
    assert sample_user.name == "Test User"
```

### Mocking

Use mocks to isolate tests from external dependencies:

```python
@pytest.fixture
def mock_database():
    """Mock the database connection."""
    with patch("myapp.database.connect") as mock_connect:
        mock_db = MagicMock()
        mock_connect.return_value = mock_db
        yield mock_db

def test_save_user(mock_database, sample_user):
    """Test that saving a user calls the database."""
    sample_user.save()
    mock_database.users.insert_one.assert_called_once()
```

## Test Data Generation

Use the test data generators to create consistent test data:

```python
from tests.fixtures.data_generators import generate_test_user

def test_user_creation():
    """Test creating a user from test data."""
    user_data = generate_test_user()
    user = User(**user_data)
    assert user.id == user_data["id"]
    assert user.username == user_data["username"]
    assert user.email == user_data["email"]
```

## Test Coverage

The target test coverage for critical modules is ≥90%. Coverage reports are generated automatically when running tests:

```bash

# Run tests with coverage report

pytest --cov=src/devsynth --cov-report=term-missing
```

## Test Documentation

Tests should be well-documented to explain what they are testing and why:

```python
def test_user_authentication():
    """
    Test user authentication process.

    This test verifies that:
    1. A user can be authenticated with valid credentials
    2. Authentication fails with invalid credentials
    3. Failed authentication attempts are logged

    """
    # Test implementation...
```

## Continuous Integration

Tests are run automatically in CI when code is pushed to the repository. The CI pipeline includes:

1. Running all tests
2. Generating coverage reports
3. Publishing test results
4. Failing the build if tests fail or coverage is below the target


## Best Practices

### Do's

- Write tests before writing code (TDD)
- Keep tests simple and focused
- Use descriptive test names
- Use fixtures for setup and teardown
- Mock external dependencies
- Test edge cases and error conditions
- Use parameterized tests for multiple input variations
- Ensure tests are deterministic (no random failures)
- Clean up after tests


### Don'ts

- Don't write tests that depend on other tests
- Don't use global state
- Don't test implementation details
- Don't write tests that depend on the environment
- Don't write tests that depend on external services
- Don't write tests that are slow or resource-intensive without marking them as such


## Examples

### Unit Test Example

```python
import pytest
from devsynth.domain.models.user import User

@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(name="Test User", email="test@example.com")

def test_user_name(sample_user):
    """Test that the user name is correct."""
    assert sample_user.name == "Test User"

def test_user_email(sample_user):
    """Test that the user email is correct."""
    assert sample_user.email == "test@example.com"

@pytest.mark.parametrize("invalid_email", [
    "",
    "not-an-email",
    "missing-at-symbol.com",
    "@missing-username.com"
])
def test_user_invalid_email(invalid_email):
    """Test that creating a user with an invalid email raises an error."""
    with pytest.raises(ValueError):
        User(name="Test User", email=invalid_email)
```

### Integration Test Example

```python
import pytest
from devsynth.domain.models.user import User
from devsynth.domain.models.project import Project

@pytest.fixture
def user_and_project():
    """Create a user and a project for testing."""
    user = User(name="Test User", email="test@example.com")
    project = Project(name="Test Project", owner=user)
    return user, project

def test_user_owns_project(user_and_project):
    """Test that a user owns a project."""
    user, project = user_and_project
    assert project in user.projects
    assert user == project.owner
```

### Behavior Test Example


```python

# tests/behavior/steps/user_authentication_steps.py

from pytest_bdd import given, when, then, parsers
from devsynth.domain.models.user import User
from devsynth.domain.services.authentication import authenticate

@given("I am a registered user")
def registered_user():
    """Create a registered user."""
    return User(name="Test User", email="test@example.com", password="password123")

@when("I enter my correct credentials")
def enter_correct_credentials(registered_user):
    """Enter correct credentials."""
    return authenticate(registered_user.email, "password123")

@when("I enter incorrect credentials")
def enter_incorrect_credentials(registered_user):
    """Enter incorrect credentials."""
    return authenticate(registered_user.email, "wrong-password")

@then("I should be authenticated")
def should_be_authenticated(enter_correct_credentials):
    """Verify that authentication was successful."""
    assert enter_correct_credentials.success is True

@then("I should not be authenticated")
def should_not_be_authenticated(enter_incorrect_credentials):
    """Verify that authentication failed."""
    assert enter_incorrect_credentials.success is False

@then("I should see my dashboard")
def should_see_dashboard(enter_correct_credentials):
    """Verify that the dashboard is displayed."""
    assert enter_correct_credentials.redirect_url == "/dashboard"

@then("I should see an error message")
def should_see_error_message(enter_incorrect_credentials):
    """Verify that an error message is displayed."""
    assert enter_incorrect_credentials.error_message == "Invalid credentials"
```

## Running Tests

### Running All Tests

```bash

# Run all tests

pytest

# Run all tests with verbose output

pytest -v
```

## Running Specific Tests

```bash

# Run a specific test file

pytest tests/unit/domain/models/test_user.py

# Run a specific test function

pytest tests/unit/domain/models/test_user.py::test_user_name

# Run tests matching a pattern

pytest -k "user"
```

## Running Tests by Category

```bash

# Run only unit tests

pytest tests/unit/

# Run only integration tests

pytest tests/integration/

# Run only behavior tests

pytest tests/behavior/

# Run tests by speed

pytest --speed=fast
```

## Generating Coverage Reports

```bash

# Generate coverage report

pytest --cov=src/devsynth

# Generate detailed coverage report

pytest --cov=src/devsynth --cov-report=term-missing

# Generate HTML coverage report

pytest --cov=src/devsynth --cov-report=html
```

## Implementation Status

.
