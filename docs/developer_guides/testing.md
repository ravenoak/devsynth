---
title: "DevSynth Testing Guide"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "testing"
  - "development"
  - "best practices"
  - "quality assurance"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-01"
---

# DevSynth Testing Guide

## Executive Summary

This guide documents the testing standards, practices, and infrastructure for the DevSynth project. It covers the project's testing philosophy, directory structure, test types (BDD, unit, integration), test isolation practices, and guidelines for writing and running tests. It serves as the definitive reference for both human contributors and agentic LLMs working on the project's test suite.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Directory Structure](#test-directory-structure)
- [Test Types](#test-types)
- [Test Isolation & Cleanliness](#test-isolation--cleanliness)
- [Provider System Testing](#provider-system-testing)
- [ChromaDB Memory Store Testing](#chromadb-memory-store-testing)
- [Writing New Tests](#writing-new-tests)
- [Running Tests](#running-tests)
- [Continuous Integration](#continuous-integration)
- [Test Coverage](#test-coverage)

## Testing Philosophy

DevSynth follows a comprehensive testing approach that combines multiple testing strategies:

- **Behavior-Driven Development (BDD)**: Using Gherkin syntax to define features and scenarios that validate system behavior from a user perspective.
- **Unit Testing**: Testing individual components in isolation to verify their correctness.
- **Integration Testing**: Testing the interaction between multiple components.
- **Property-Based Testing**: Using strategies like hypothesis testing to verify properties of functions across a range of inputs.

Our testing philosophy emphasizes:

1. **Test Isolation**: Tests should not interfere with each other and should run independently.
2. **Test Cleanliness**: Tests should clean up after themselves and not leave artifacts in the workspace.
3. **Test Coverage**: Critical components should have comprehensive test coverage.
4. **Test Readability**: Tests should be clear and serve as documentation for the code they test.
5. **Provider Abstraction**: Tests should work with either OpenAI or LM Studio through our provider abstraction layer.

## Test Directory Structure

```
tests/
├── conftest.py              # Global test fixtures and configuration
├── README.md                # Testing overview and instructions
├── behavior/                # Behavior-driven (BDD) tests
│   ├── conftest.py          # BDD-specific test fixtures
│   ├── steps/               # Step definitions for BDD scenarios
│   ├── *.feature            # Feature files in Gherkin syntax
│   └── test_*.py            # Test implementations for features
├── integration/             # Integration tests
│   └── test_*.py            # Integration test implementations
└── unit/                    # Unit tests
    └── test_*.py            # Unit test implementations
```

## Test Types

### Behavior-Driven Tests

Behavior-driven tests use Gherkin syntax (Feature/Scenario/Given/When/Then) to define system behaviors. These tests ensure the system works correctly from a user perspective.

Example feature file (`tests/behavior/chromadb_integration.feature`):

```gherkin
Feature: ChromaDB Integration
  As a developer
  I want to use ChromaDB as a memory store
  So that I can leverage vector database capabilities for semantic search

  Scenario: Initialize ChromaDB memory store
    Given the DevSynth CLI is installed
    When I configure the memory store type as "chromadb"
    Then a ChromaDB memory store should be initialized
```

BDD tests are implemented in Python files that use the `pytest-bdd` framework to connect Gherkin steps to Python functions.

### Unit Tests

Unit tests verify the correctness of individual components in isolation. They typically mock external dependencies to focus on the component under test.

### Integration Tests

Integration tests verify that multiple components work together correctly. These tests use real (or realistic) implementations of dependencies instead of mocks.

## Test Isolation & Cleanliness

DevSynth tests are designed to be isolated and clean:

- All tests use temporary directories for artifact storage (e.g., `.devsynth` directories, logs).
- Environment variables are patched during tests to prevent pollution of the real environment.
- Tests clean up after themselves, even if they fail.

The main test fixtures for isolation and cleanliness are:

- `tmp_project_dir`: Creates a temporary directory for test artifacts.
- `patch_env_and_cleanup`: Patches environment variables and ensures cleanup.

Example of test isolation (from `tests/behavior/conftest.py`):

```python
@pytest.fixture(autouse=True)
def patch_env_and_cleanup(tmp_project_dir):
    """
    Patch environment variables for LLM providers and ensure all logs/artifacts 
    are isolated and cleaned up.
    """
    # Save old environment and set test environment
    old_env = dict(os.environ)
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["LM_STUDIO_ENDPOINT"] = "http://127.0.0.1:1234"
    os.environ["DEVSYNTH_PROJECT_DIR"] = tmp_project_dir

    # Redirect logs to temp dir
    logs_dir = os.path.join(tmp_project_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    old_cwd = os.getcwd()
    os.chdir(tmp_project_dir)

    yield

    # Cleanup: restore env and cwd, remove logs
    os.environ.clear()
    os.environ.update(old_env)
    os.chdir(old_cwd)

    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)

    # Remove any stray .devsynth or logs in cwd
    for artifact in [".devsynth", "logs"]:
        path = os.path.join(old_cwd, artifact)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
```

## Provider System Testing

DevSynth tests the provider system (OpenAI, LM Studio) with a combination of unit tests and integration tests:

- **Unit Tests**: Mock the provider APIs to test the provider system's logic.
- **Integration Tests**: Optionally connect to real LLM services to test actual API integration.

The provider system tests validate:

1. Provider selection logic (choosing between OpenAI and LM Studio)
2. Fallback mechanisms (trying alternative providers if one fails)
3. Environment variable configuration
4. Error handling and retries

Test fixtures for provider system testing include:

- `llm_provider`: Returns a configured provider instance.
- `llm_complete`: Provides a function to generate LLM completions.

Example of provider system testing fixtures (from `tests/behavior/conftest.py`):

```python
@pytest.fixture
def llm_provider():
    """
    Get a provider for LLM completion that works with either OpenAI or LM Studio.
    """
    provider = get_provider(fallback=True)
    return provider

@pytest.fixture
def llm_complete():
    """
    Fixture providing a function to get completions from the LLM.
    """
    def _complete(prompt, system_prompt=None, temperature=0.7, max_tokens=2000):
        return complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            fallback=True  # Enable fallback to try all available providers
        )

    return _complete
```

## ChromaDB Memory Store Testing

The ChromaDB memory store is tested with both standard and enhanced features:

- **Basic Integration**: Testing store, retrieve, and search operations.
- **Provider Integration**: Testing ChromaDB with provider-based embeddings.
- **Advanced Features**: Testing caching, versioning, and optimized embedding storage.

The ChromaDB tests use fixtures for isolation and provider integration:

- `temp_chromadb_path`: Creates a temporary ChromaDB data directory.
- `memory_store`: Creates a ChromaDB memory store configured to use the provider system.
- `memory_port`: Creates a memory port with the ChromaDB memory store.

## Writing New Tests

### Guidelines for New Tests

1. **Isolation**: Tests should be isolated from each other and the local environment.
   - Use temporary directories via the `tmp_project_dir` fixture.
   - Patch environment variables.
   - Clean up all artifacts.

2. **Provider Abstraction**: Tests should work with either OpenAI or LM Studio.
   - Use the `llm_provider` or `llm_complete` fixtures for LLM operations.
   - Ensure tests can run with any provider.

3. **Completeness**: Tests should cover both happy paths and error scenarios.
   - Test error handling and recovery.
   - Validate behaviors with various inputs.

4. **Traceability**: Tests should be traceable to requirements.
   - Name tests to clearly indicate the feature/requirement they validate.
   - Add comments linking to requirement IDs where appropriate.

### Adding a New BDD Test

1. Create a new feature file in `tests/behavior/` with Gherkin syntax.
2. Add step definitions in `tests/behavior/steps/` if needed.
3. Create a test runner file in `tests/behavior/test_*.py`.

### Adding a New Integration Test

1. Create a new test file in `tests/integration/test_*.py`.
2. Use provider system and memory store fixtures as needed.
3. Test the interaction between components.

### Adding a New Unit Test

1. Create a new test file in `tests/unit/test_*.py`.
2. Mock external dependencies to isolate the component under test.
3. Test component behavior with various inputs and edge cases.

## Running Tests

### Running All Tests

```bash
pytest
```

### Running Specific Test Types

```bash
# Run BDD tests
pytest tests/behavior/

# Run integration tests
pytest tests/integration/

# Run unit tests
pytest tests/unit/
```

### Running a Specific Test File

```bash
pytest tests/behavior/test_chromadb_integration.py
```

### Running Tests with Provider Selection

```bash
# Use OpenAI provider
DEVSYNTH_PROVIDER=openai pytest

# Use LM Studio provider
DEVSYNTH_PROVIDER=lm_studio pytest
```

## Continuous Integration

DevSynth uses GitHub Actions for continuous integration testing. The CI pipeline:

1. Runs all tests on PR and push to main.
2. Verifies test isolation and cleanliness.
3. Checks test coverage.
4. Runs linting and type checking.

## Test Coverage

DevSynth aims for high test coverage, with a focus on covering:

1. Core memory and provider components.
2. API endpoints and CLI commands.
3. Error handling paths.
4. Configuration handling.

Test coverage is tracked and reported in CI runs.

---

_Last updated: May 17, 2025_
