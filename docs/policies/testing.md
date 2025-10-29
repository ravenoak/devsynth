---

title: "DevSynth Testing Policy"
date: "2025-07-07"
version: "0.1.0a1"
tags:
  - "policy"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; DevSynth Testing Policy
</div>

# DevSynth Testing Policy

This document defines the testing policy for the DevSynth project, establishing standards and requirements for all test creation and maintenance. It serves as a governing policy that all contributors—both human and agentic—must follow to ensure the project's ongoing health, resilience, and stability.

## Policy Goals

1. **Ensure Comprehensive Test Coverage**: All features and components must have appropriate test coverage.
2. **Maintain Test Isolation**: Tests must be isolated from each other and the environment.
3. **Enforce Test Cleanliness**: Tests must clean up all artifacts and not pollute the workspace.
4. **Enable Provider Agnosticism**: Tests must work with either OpenAI or LM Studio.
5. **Support Traceability**: Tests must be traceable to requirements and specifications.
6. **Facilitate Continuous Integration**: Tests must be automatable and reliable in CI environments.


## Testing Requirements

### Mandatory Testing

1. **New Features**: All new features must include appropriate tests before being merged:
   - Behavior tests for user-facing features (using Gherkin syntax)
   - Integration tests for component interactions
   - Unit tests for individual components

2. **Bug Fixes**: All bug fixes must include regression tests that:
   - Reproduce the issue
   - Verify the fix works correctly
   - Prevent the issue from recurring

3. **Refactoring**: Code refactoring must not break existing tests, and may require:
   - Updates to existing tests
   - Additional tests for new patterns or components


### Test Types and Coverage

1. **Behavior Tests**: Required for all user-facing features and workflows.
   - Must use Gherkin syntax (Feature/Scenario/Given/When/Then)
   - Must be implemented using pytest-bdd
   - Must be placed in `tests/behavior/`

2. **Integration Tests**: Required for component interactions.
   - Must verify that components work together correctly
   - Must be placed in `tests/integration/`

3. **Unit Tests**: Required for individual components.
   - Must test component behavior in isolation
   - Must mock external dependencies appropriately
   - Must be placed in `tests/unit/`

4. **Property-Based Tests**: Encouraged for functions with complex logic.
   - Should use hypothesis or similar for generating test cases
   - Should verify properties across a range of inputs


### Test Categorization and Markers

1. **Speed Markers**: Each test must include exactly one of `fast`, `medium`, or `slow`.
   - Unmarked tests default to `medium` but should still be explicitly marked.
2. **Isolation Marker**: Add the `isolation` marker when a test requires dedicated resources or cleans up global state.


### Test Isolation and Cleanliness

1. **Temporary Resources**: Tests must use temporary directories for all artifacts.
   - Must use the `tmp_project_dir` fixture or equivalent
   - Must not create files outside these directories

2. **Environment Variables**: Tests must patch environment variables.
   - Must use the `patch_env_and_cleanup` fixture or equivalent
   - Must restore original environment after test completion

3. **Cleanup**: Tests must clean up all artifacts, even on failure.
   - Must use appropriate cleanup in fixtures (e.g., using `yield` with cleanup code)
   - Must handle both success and failure cases

4. **Verification**: CI must verify that tests do not leave artifacts.
   - Tests that pollute the workspace will fail CI checks


### Provider Abstraction

1. **Provider Testing**: Tests involving LLMs must use the provider abstraction.
   - Must use the `llm_provider` or `llm_complete` fixtures
   - Must not directly instantiate provider classes without abstraction

2. **Provider Agnosticism**: Tests must work with any configured provider.
   - Must not assume a specific provider is available
   - Must leverage the fallback mechanism for resilience

3. **Mock Providers**: Unit tests should use mock providers where appropriate.
   - Should avoid actual API calls in unit tests
   - Should test fallback and error handling


### Test Documentation and Traceability

1. **Test Naming**: Tests must be named clearly to indicate what they test.
   - Must follow the pattern `test_<component>_<behavior>.py`
   - Must use descriptive function names

2. **Test Documentation**: Tests must include clear docstrings.
   - Must explain the purpose of the test
   - Should reference relevant requirements where applicable

3. **Requirement Traceability**: Tests should be traceable to requirements.
   - Should include comments linking to requirement IDs
   - Should be listed in the Requirements Traceability Matrix


## Testing Process

### Creating Tests

1. **Test-Driven Development**: Encouraged for new features.
   - Write tests before implementation when possible
   - Use tests to validate requirements

2. **Test Review**: Tests must be reviewed as part of code review.
   - Review for coverage, isolation, and cleanliness
   - Ensure tests follow this policy


### Running Tests

1. **Local Testing**: Contributors must run tests locally before submitting PRs.
   - Must run at minimum the tests affected by their changes
   - Should run the full test suite when possible

2. **Continuous Integration**: All PRs must pass CI tests.
   - CI will run the full test suite
   - CI will verify test isolation and cleanliness
   - CI will check test coverage


### Test Maintenance

1. **Test Updates**: Tests must be updated when related code changes.
   - Must update tests when APIs change
   - Must update tests when behavior changes

2. **Test Refactoring**: Test code should be refactored for maintainability.
   - Should extract common test patterns into fixtures
   - Should maintain clean test code

3. **Test Deprecation**: Deprecated features must maintain tests until removal.
   - Tests for deprecated features should be marked but not removed
   - Tests should be removed only when the feature is removed


## Enforcement

1. **CI Checks**: Automated checks will enforce this policy.
   - Test coverage thresholds
   - Test isolation verification
   - Linting of test code

2. **Code Review**: Reviewers must verify compliance with this policy.
   - Reject PRs that lack appropriate tests
   - Ensure tests follow isolation and cleanliness requirements

3. **Documentation**: Testing requirements must be documented.
   - Policy must be available in the repository
   - Guidelines must be available for contributors


---

_Last updated: May 17, 2025_
## Implementation Status

This feature is **implemented**.
