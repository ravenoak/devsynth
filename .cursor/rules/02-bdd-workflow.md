---
description: Behavior-Driven Development workflow with Gherkin features
globs:
  - "tests/behavior/**/*"
  - "docs/specifications/**/*"
  - "**/*.feature"
alwaysApply: false
---

# DevSynth BDD Workflow

## Specification-First Approach

**Strict workflow (non-negotiable):**

1. Draft specification in `docs/specifications/`
2. Write failing BDD feature in `tests/behavior/features/`
3. Implement step definitions in `tests/behavior/steps/`
4. Write production code in `src/devsynth/`
5. Verify tests pass

**Never write code before specification and failing feature exist.**

## Socratic Checklist

Every specification must answer:

1. **What is the problem?**
   - Clear problem statement
   - Context and background
   - Stakeholders affected

2. **What proofs confirm the solution?**
   - Acceptance criteria
   - Observable behaviors
   - Success metrics

## Specification Template

Location: `docs/specifications/<feature_name>.md`

```markdown
---
title: "<Feature Name>"
date: "YYYY-MM-DD"
version: "0.1.0-alpha.1"
tags: ["specification", "<domain>"]
status: "draft"
author: "DevSynth Team"
---

# <Feature Name> Specification

## Problem Statement
Clear description of the problem.

## Solution Overview
High-level solution description.

### Dialectical Analysis
**Thesis**: Initial approach
**Antithesis**: Challenges/alternatives
**Synthesis**: Resolved approach

## Requirements
### Functional Requirements
- FR-01: <Requirement>

### Non-Functional Requirements
- NFR-01: <Requirement>

## Acceptance Criteria
1. Observable behavior 1
2. Observable behavior 2

## Traceability
- Features: `tests/behavior/features/<name>.feature`
- Code: `src/devsynth/<module>/<file>.py`
```

## Feature File Structure

Location: `tests/behavior/features/<feature_name>.feature`

```gherkin
@feature_<feature_name>
@fast
Feature: <Feature Name>
  As a <role>
  I want to <action>
  So that <benefit>

  Background:
    Given a <common precondition>

  @smoke
  Scenario: <Primary scenario>
    Given <initial context>
    When <action performed>
    Then <observable outcome>

  @edge_case
  Scenario Outline: <Parameterized scenario>
    Given a context with "<parameter>"
    When action with "<input>"
    Then result should be "<expected>"
    
    Examples:
      | parameter | input   | expected |
      | value1    | input1  | output1  |
      | value2    | input2  | output2  |
```

### Feature Conventions

- One feature per file
- Declarative style (describe *what*, not *how*)
- User perspective
- Tags for categorization

### Feature Marker Enum

After changing `feature_*` markers:

```bash
poetry run python scripts/generate_feature_marker_enum.py
```

## Step Definition Pattern

Location: `tests/behavior/steps/<feature_name>_steps.py`

```python
"""Step definitions for <feature_name>."""
from pytest_bdd import given, when, then, parsers, scenarios

scenarios('../features/<feature_name>.feature')

@pytest.fixture
def context():
    """Shared context."""
    return {"system": None, "output": None}

@given("a resource")
def given_resource(context):
    """Establish resource."""
    context["system"] = MyClass()

@when(parsers.parse('I perform action with "{input}"'))
def when_action(context, input):
    """Perform action."""
    context["output"] = context["system"].action(input)

@then(parsers.parse('result should be "{expected}"'))
def then_result(context, expected):
    """Verify result."""
    assert context["output"] == expected
```

### Step Best Practices

- Use shared context fixture
- Descriptive function names
- Use `parsers.parse()` for parameters
- Capture exceptions for error scenarios
- Write reusable generic steps

## Running BDD Tests

```bash
# All behavior tests
poetry run pytest tests/behavior/

# Specific feature
poetry run pytest tests/behavior/features/<feature>.feature

# By tag
poetry run pytest tests/behavior/ -m "smoke"
```

## BDD Anti-Patterns

❌ **Don't write imperative steps:**
```gherkin
When I click the button
And I wait 2 seconds
```

✅ **Write declarative steps:**
```gherkin
When I submit the form
Then the submission should succeed
```

❌ **Don't include implementation details:**
```gherkin
When I call /api/v1/memory with POST
```

✅ **Focus on behavior:**
```gherkin
When I create a memory item
```

## Templates

- `templates/behavior/feature_template.feature`
- `templates/step_definitions_template.py`

