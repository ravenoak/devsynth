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

1. **Draft specification** in `docs/specifications/` answering Socratic questions
2. **Write failing BDD feature** in `tests/behavior/features/`
3. **Implement step definitions** in `tests/behavior/steps/`
4. **Write production code** in `src/devsynth/`
5. **Verify tests pass** and update documentation

**Never write code before specification and failing feature exist.**

### Workflow Example: Adding CLI Command

**1. Specification Phase:**
```markdown
<!-- docs/specifications/cli-offline-mode.md -->
# CLI Offline Mode Specification

## Problem Statement
Users need to run DevSynth agents without internet connectivity for air-gapped environments and offline development scenarios.

## Solution Overview
Add `--offline` flag that disables network-dependent features and uses local transformers for LLM inference.

### Dialectical Analysis
**Thesis**: Always use cloud APIs for maximum capability
**Antithesis**: Air-gapped environments cannot access cloud APIs
**Synthesis**: Detect network availability and provide offline fallback
```

**2. Feature File:**
```gherkin
# tests/behavior/features/cli_offline_mode.feature
@feature_cli_offline
@fast
Feature: CLI Offline Mode
  As a developer in air-gapped environments
  I want to run DevSynth with --offline flag
  So that I can work without internet connectivity

  Background:
    Given DevSynth is installed
    And local transformers model is available

  @smoke
  Scenario: Offline mode disables network features
    Given I have internet connectivity
    When I run "devsynth agent run --offline"
    Then network requests should be disabled
    And local transformers should be used for inference
```

**3. Step Definitions:**
```python
# tests/behavior/steps/cli_offline_steps.py
from pytest_bdd import given, when, then, scenarios

scenarios('../features/cli_offline_mode.feature')

@given("DevSynth is installed")
def devsynth_installed():
    """Verify DevSynth CLI is available."""
    # Implementation

@given("local transformers model is available")
def local_model_available():
    """Ensure transformers library and model are available."""
    # Implementation

@when('I run "devsynth agent run --offline"')
def run_offline_command():
    """Execute CLI command with offline flag."""
    # Implementation

@then("network requests should be disabled")
def verify_network_disabled():
    """Verify no network calls are made."""
    # Implementation

@then("local transformers should be used for inference")
def verify_local_inference():
    """Verify local model is used instead of API."""
    # Implementation
```

**4. Implementation:**
```python
# src/devsynth/cli/commands/agent_cmd.py
@app.command()
def run(
    offline: bool = typer.Option(False, "--offline", help="Run in offline mode")
):
    """Run agent with optional offline mode."""
    if offline:
        # Disable network features
        # Configure local transformers
        pass
    # Implementation
```

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

**BDD Testing Philosophy:**

**Thesis**: Behavior-Driven Development ensures alignment between business requirements and implementation through executable specifications.

**Antithesis**: Poorly written BDD tests can become maintenance burdens and fail to provide clear business value.

**Synthesis**: Well-structured BDD with proper step definitions, clear scenarios, and regular maintenance provides living documentation that validates business requirements.

### BDD Test Commands

```bash
# All behavior tests (within Poetry environment)
poetry run pytest tests/behavior/

# Specific feature file
poetry run pytest tests/behavior/features/<feature>.feature

# By BDD tags
poetry run pytest tests/behavior/ -m "smoke"
poetry run pytest tests/behavior/ -m "feature_<feature_name>"

# With verbose output for debugging
poetry run pytest tests/behavior/ -v -s

# Generate BDD report
poetry run pytest tests/behavior/ --bdd-report
```

### BDD Environment Setup

**Required Dependencies:**
```bash
# Ensure BDD extras are installed
poetry install --with dev --extras "tests"

# Verify BDD tools available
poetry run python -c "import pytest_bdd; print('pytest-bdd OK')"
poetry run python -c "import behave; print('behave OK')"  # If using behave
```

**Feature File Validation:**
```bash
# Check feature file syntax
poetry run python -m pytest_bdd.check tests/behavior/features/

# Generate step definition stubs
poetry run python scripts/generate_step_stubs.py tests/behavior/features/
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
