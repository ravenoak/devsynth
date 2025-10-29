---

author: DevSynth Team
date: '2025-05-25'
last_reviewed: "2025-07-10"
status: published
tags:
- training
- TDD
- BDD
- EDRR
- methodology
- integration
- best-practices
title: TDD/BDD-EDRR Integration Training Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; TDD/BDD-EDRR Integration Training Guide
</div>

# TDD/BDD-EDRR Integration Training Guide

This comprehensive training guide is designed to help developers understand and implement the integration of Test-Driven Development (TDD) and Behavior-Driven Development (BDD) with DevSynth's "Expand, Differentiate, Refine, Retrospect" (EDRR) methodology.

## 1. Introduction to TDD/BDD

### 1.1 Test-Driven Development (TDD)

Test-Driven Development is a software development approach where tests are written before the code that needs to be tested. The TDD cycle consists of three steps:

1. **Red**: Write a failing test that defines the functionality you want to implement
2. **Green**: Write the minimum amount of code needed to make the test pass
3. **Refactor**: Improve the code while ensuring the tests still pass

Benefits of TDD include:
- Improved code quality and design
- Better test coverage
- Faster feedback on code changes
- Reduced debugging time
- More maintainable codebase

### 1.2 Behavior-Driven Development (BDD)

Behavior-Driven Development extends TDD by focusing on the behavior of the system from a user's perspective. BDD uses a ubiquitous language that all stakeholders can understand, typically in the form of "Given-When-Then" scenarios.

Key components of BDD include:
- **Feature files**: Written in Gherkin syntax, describing the behavior of the system
- **Step definitions**: Code that maps the Gherkin steps to executable actions
- **Scenarios**: Specific examples of how the system should behave in different situations

Benefits of BDD include:
- Improved communication between technical and non-technical stakeholders
- Clear documentation of system behavior
- Focus on user value and business outcomes
- Early detection of misunderstandings and gaps in requirements

## 2. Overview of EDRR Methodology

The EDRR methodology is DevSynth's approach to software development, consisting of four phases:

### 2.1 Expand Phase

The Expand phase focuses on gathering all available information and requirements. During this phase, you:
- Collect and analyze requirements
- Identify stakeholders and their needs
- Explore the problem domain
- Gather existing artifacts and knowledge

### 2.2 Differentiate Phase

The Differentiate phase validates requirements against each other and identifies inconsistencies. During this phase, you:
- Analyze relationships between requirements
- Identify conflicts and gaps
- Prioritize requirements
- Define boundaries and constraints

### 2.3 Refine Phase

The Refine phase implements the solution and integrates it with existing code. During this phase, you:
- Implement the solution
- Integrate with existing systems
- Validate against requirements
- Optimize and improve

### 2.4 Retrospect Phase

The Retrospect phase evaluates outcomes and plans for the next iteration. During this phase, you:
- Review the implementation
- Analyze what worked and what didn't
- Identify lessons learned
- Plan for the next iteration

Each phase records a `quality_score` and sets `phase_complete` when predefined
thresholds are met. These markers enable the coordinator to transition between
phases automatically while preserving quality metrics for later review.

## 3. Integration Principles

The integration of TDD/BDD with EDRR is guided by the following principles:

### 3.1 Test-First Development

Tests are written before implementation in all EDRR phases. This ensures that:
- Requirements are testable
- Implementation meets the requirements
- Quality is built in from the start

### 3.2 Multi-Level Testing

Different types of tests are applied at appropriate phases:
- BDD scenarios for user-facing behavior
- Integration tests for component interactions
- Unit tests for internal components

### 3.3 Continuous Validation

Tests serve as executable specifications that validate progress throughout the EDRR process:
- BDD scenarios validate user requirements
- Integration tests validate component interactions
- Unit tests validate internal behavior

### 3.4 Dialectical Reasoning

Multiple testing perspectives provide a comprehensive view of the system:
- Thesis: Unit testing perspective (individual components)
- Antithesis: Integration testing perspective (component interactions)
- Synthesis: Behavior testing perspective (user-facing behavior)

### 3.5 Living Documentation

Tests and scenarios serve as up-to-date documentation:
- BDD scenarios document user requirements
- Integration tests document component interactions
- Unit tests document internal behavior

## 4. Practical Examples

### 4.1 Promise System Example

The Promise System in DevSynth was developed using TDD/BDD integrated with EDRR:

#### Expand Phase:

```gherkin
Feature: Promise System Capability Management
  As a developer using DevSynth
  I want to use the Promise System to declare, authorize, and manage capabilities
  So that agents can collaborate securely with proper authorization

  Scenario: Agent creates a promise
    Given agent "code_agent" has capability "CODE_GENERATION"
    When agent "code_agent" creates a promise of type "CODE_GENERATION" with parameters:
      | parameter   | value                           |
      | file_path   | /project/src/module.py          |
      | language    | python                          |
      | description | Implement data processing function |
    Then a new promise should be created
    And the promise should be in "PENDING" state
    And the promise should have the specified parameters
```

#### Differentiate Phase:

```python
def test_resolve(self):
    """Test resolving a Promise."""
    promise = Promise[str]()
    promise.resolve("test value")

    assert promise.state == PromiseState.FULFILLED
    assert promise.is_fulfilled
    assert not promise.is_pending
    assert promise.value == "test value"

    # Cannot resolve again
    with pytest.raises(PromiseStateError):
        promise.resolve("another value")
```

#### Refine Phase:

```python
def resolve(self, value: T) -> None:
    """
    Resolves the promise with a given value.
    To be used by the promise's creator.

    Args:
        value: The value with which to resolve the promise

    Raises:
        PromiseStateError: If the promise is already fulfilled or rejected
    """
    if self._state != PromiseState.PENDING:
        raise PromiseStateError(f"Cannot resolve promise in state {self._state}")

    self._state = PromiseState.FULFILLED
    self._value = value
    self._metadata["resolved_at"] = None  # Will be set by calling code

    # Call all the on_fulfilled callbacks with the value
    for callback in self._on_fulfilled:
        try:
            callback(value)
        except Exception as e:
            logger.error(f"Error in promise callback: {e}")

    # Clear the callback lists to avoid memory leaks
    self._on_fulfilled = []
    self._on_rejected = []
```

#### Retrospect Phase:

- Review test coverage (100% for Promise class)
- Identify additional scenarios (promise chaining, timeout handling)
- Plan improvements for the next iteration

### 4.2 Methodology Adapters Example

The Methodology Adapters feature also followed the TDD/BDD-EDRR integration:

#### Expand Phase:

```gherkin
Feature: Methodology Adapters Integration
  As a developer using DevSynth
  I want to use different methodology adapters
  So that I can integrate the EDRR process with my preferred development methodology

  Scenario: Configure Sprint Methodology Adapter
    When I set the methodology type to "sprint" in the configuration
    And I configure the sprint duration to 2 weeks
    And I configure the ceremony mappings:
      | ceremony       | edrr_phase                  |
      | planning       | retrospect.iteration_planning |
      | dailyStandup   | phase_progression_tracking  |
      | review         | refine.outputs_review       |
      | retrospective  | retrospect.process_evaluation |
    Then the methodology adapter should be of type "SprintAdapter"
    And the sprint duration should be 2 weeks
    And the ceremony mappings should be correctly configured
```

## 5. Exercises and Workshops

### 5.1 Writing Your First BDD Scenario

**Objective**: Learn how to write effective BDD scenarios

**Instructions**:
1. Identify a user-facing feature to implement
2. Write a feature file with at least one scenario
3. Implement step definitions for the scenario
4. Run the scenario to verify it fails (Red)

**Integration Aspect**: BDD in Expand phase

### 5.2 Creating Unit Tests for TDD

**Objective**: Learn how to write unit tests following TDD principles

**Instructions**:
1. Identify a component to implement
2. Write unit tests for the component
3. Run the tests to verify they fail (Red)
4. Implement the component to make the tests pass (Green)
5. Refactor the implementation while keeping the tests passing

**Integration Aspect**: TDD in Differentiate phase

### 5.3 Implementing Code to Pass Tests

**Objective**: Learn how to implement code that passes the tests

**Instructions**:
1. Start with failing tests (from previous exercises)
2. Implement the minimum code needed to make the tests pass
3. Refactor the code to improve quality
4. Verify that the tests still pass

**Integration Aspect**: Implementation in Refine phase

### 5.4 Retrospective Analysis of Test Coverage

**Objective**: Learn how to analyze test coverage and effectiveness

**Instructions**:
1. Run coverage analysis on your tests
2. Identify areas with low coverage
3. Add tests to improve coverage
4. Analyze the effectiveness of your tests
5. Plan improvements for the next iteration

**Integration Aspect**: Testing in Retrospect phase

## 6. Common Pitfalls and Solutions

### 6.1 Writing Tests After Implementation

**Pitfall**: Writing tests after implementing the code defeats the purpose of TDD/BDD.

**Solution**:
- Use pre-commit hooks to enforce test-first development
- Track test-first metrics to monitor adherence
- Pair programming with a TDD/BDD advocate

### 6.2 Overly Complex Tests

**Pitfall**: Tests that are too complex are difficult to maintain and understand.

**Solution**:
- Keep tests small and focused
- Test one behavior per test
- Use helper methods and fixtures for setup
- Follow the Arrange-Act-Assert pattern

### 6.3 Insufficient Test Coverage

**Pitfall**: Missing tests for edge cases and error conditions.

**Solution**:
- Use test coverage tools to identify gaps
- Include tests for error conditions and edge cases
- Use property-based testing for complex behaviors
- Review tests during code reviews

### 6.4 Brittle Tests

**Pitfall**: Tests that break when implementation details change.

**Solution**:
- Test behavior, not implementation
- Use appropriate levels of abstraction
- Avoid testing private methods directly
- Use test doubles (mocks, stubs) appropriately

### 6.5 Neglecting BDD for Technical Components

**Pitfall**: Using BDD only for user-facing features and neglecting it for technical components.

**Solution**:
- Write BDD scenarios for technical components from a developer's perspective
- Use domain-specific language for technical scenarios
- Include technical stakeholders in BDD discussions

## 7. Advanced Topics

### 7.1 Property-Based Testing

Property-based testing generates random inputs to test properties of your code. It's useful for finding edge cases and unexpected behaviors.

**Example**:

```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    """Test that sorting a list twice gives the same result as sorting once."""
    sorted_once = sorted(lst)
    sorted_twice = sorted(sorted_once)
    assert sorted_once == sorted_twice
```

### 7.2 Mutation Testing

Mutation testing evaluates the quality of your tests by introducing small changes (mutations) to your code and checking if your tests catch them.

**Example**:

```bash

# Using the pytest-mutate plugin

poetry run pytest --mutate=src/devsynth/module.py
```

## 7.3 Test-Driven Architecture

Test-Driven Architecture applies TDD principles to architectural decisions, using tests to drive the design of the system architecture.

**Key Principles**:
- Write tests for architectural constraints
- Use tests to validate architectural decisions
- Evolve the architecture based on test feedback

### 7.4 Continuous Testing

Continuous Testing integrates testing into the development workflow, providing immediate feedback on code changes.

**Implementation**:
- Run tests automatically on code changes
- Integrate tests into the CI/CD pipeline
- Use test results to gate deployments
- Monitor test metrics over time

## 8. Next Steps

To continue your learning journey:

1. **Practice**: Apply the TDD/BDD-EDRR integration to a real project
2. **Explore**: Dive deeper into advanced topics
3. **Share**: Teach others about TDD/BDD-EDRR integration
4. **Contribute**: Help improve the DevSynth testing framework

For personalized guidance, use the DevSynth learning path generator to create a customized learning plan based on your skill level and goals.

## 9. Resources

### 9.1 DevSynth Documentation

- [TDD/BDD Approach](tdd_bdd_approach.md)
- [TDD/BDD-EDRR Integration](tdd_bdd_edrr_integration.md)
- [Hermetic Testing](hermetic_testing.md)
- [Test Templates](test_templates.md)

### 9.2 External Resources

- [Test-Driven Development: By Example](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530) by Kent Beck
- [BDD in Action](https://www.manning.com/books/bdd-in-action) by John Ferguson Smart
- [Growing Object-Oriented Software, Guided by Tests](https://www.amazon.com/Growing-Object-Oriented-Software-Guided-Tests/dp/0321503627) by Steve Freeman and Nat Pryce
- [Pytest Documentation](https://docs.pytest.org/)
- [Cucumber Documentation](https://cucumber.io/docs/)
## Implementation Status

.
