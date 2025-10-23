---
description: Complete workflow for adding a new feature
globs:
  - "**/*"
alwaysApply: false
---

# Workflow: Adding a New Feature

## Overview

Follow this structured workflow when adding any new feature to DevSynth.

## Prerequisites

- Development environment set up (`scripts/install_dev.sh`)
- Dependencies installed (`poetry install --with dev --extras "tests retrieval chromadb api"`)
- Git branch created: `feature/<feature-name>`

## Step-by-Step Workflow

### 1. Create Specification (MANDATORY FIRST STEP)

**Using Cursor IDE:**
```bash
# In Cursor chat, use:
/generate-specification <feature_name> feature

# This will:
# 1. Create specification in docs/specifications/<feature_name>.md
# 2. Generate BDD scenarios in tests/behavior/features/<feature_name>.feature
# 3. Provide implementation guidance with examples
```

**Manual Creation (if needed):**
Location: `docs/specifications/<feature_name>.md`

```bash
# Create specification file
touch docs/specifications/<feature_name>.md
```

**Must answer Socratic checklist:**

```markdown
---
title: "<Feature Name>"
date: "$(date +%Y-%m-%d)"
version: "0.1.0-alpha.1"
tags: ["specification", "<domain>"]
status: "draft"
author: "DevSynth Team"
---

# <Feature Name> Specification

## Problem Statement (Socratic: What is the problem?)

Clear description of what problem this feature solves.

### Background
Why is this needed?

### Stakeholders
Who benefits from this feature?

## Solution Overview

High-level description of the solution.

### Dialectical Analysis

**Thesis**: Initial approach - why we consider X

**Antithesis**: Alternative Y - why it might be better/worse

**Synthesis**: Resolved approach incorporating insights from both

## Requirements

### Functional Requirements
- FR-01: User shall be able to...
- FR-02: System shall...

### Non-Functional Requirements
- NFR-01: Performance: Operation completes in < 100ms
- NFR-02: Security: Data encrypted at rest

## Acceptance Criteria (Socratic: What proofs confirm?)

1. User can perform action X
2. System responds with Y
3. Edge case Z is handled appropriately

## Traceability

- Feature file: `tests/behavior/features/<feature_name>.feature`
- Implementation: `src/devsynth/<module>/<file>.py`
- Related issues: `issues/<id>.md`
```

### 2. Create Failing BDD Feature

Location: `tests/behavior/features/<feature_name>.feature`

```bash
# Create feature file
touch tests/behavior/features/<feature_name>.feature
```

```gherkin
@feature_<feature_name>
@fast
Feature: <Feature Name>
  As a <role>
  I want to <action>
  So that <benefit>

  Background:
    Given a configured system
    And required resources are available

  @smoke
  Scenario: Happy path - primary use case
    Given <initial state>
    When I <perform action>
    Then <expected outcome>
    And <additional verification>

  @edge_case
  Scenario: Edge case - boundary condition
    Given <edge case state>
    When I <perform action>
    Then <appropriate handling>

  @integration
  @medium
  Scenario Outline: Multiple inputs
    Given a system with "<config>"
    When I perform action with "<input>"
    Then the result should be "<expected>"

    Examples:
      | config  | input    | expected  |
      | default | value1   | result1   |
      | custom  | value2   | result2   |
```

### 3. Create Step Definitions

Location: `tests/behavior/steps/<feature_name>_steps.py`

```bash
# Create step definitions
touch tests/behavior/steps/<feature_name>_steps.py
```

```python
"""Step definitions for <feature_name> feature."""
import pytest
from pytest_bdd import given, when, then, parsers, scenarios

from devsynth.application.<module> import <Class>

scenarios('../features/<feature_name>.feature')

@pytest.fixture
def context():
    """Shared context for scenarios."""
    return {
        "system": None,
        "result": None,
        "error": None
    }

@given("a configured system")
def given_system(context):
    """Initialize system."""
    context["system"] = <Class>()

@when("I <perform action>")
def when_action(context):
    """Perform the action."""
    try:
        context["result"] = context["system"].action()
    except Exception as e:
        context["error"] = e

@then("<expected outcome>")
def then_outcome(context):
    """Verify outcome."""
    assert context["result"] is not None
    assert context["error"] is None
```

### 4. Run Failing Test (Verify It Fails)

```bash
# Should fail because feature not implemented yet
poetry run pytest tests/behavior/features/<feature_name>.feature -v
```

**Expected**: Test should fail (not implemented yet)

### 5. Create Unit Tests

Location: `tests/unit/<module>/test_<feature_name>.py`

```python
"""Unit tests for <feature_name>."""
import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.<module> import <Class>


class Test<Class>:
    """Tests for <Class>."""

    @pytest.fixture
    def instance(self):
        """Provide class instance."""
        return <Class>()

    @pytest.mark.fast
    def test_<feature>_with_valid_input(self, instance):
        """ReqID: FR-01 - Feature works with valid input."""
        # Arrange
        input_data = "valid"

        # Act
        result = instance.method(input_data)

        # Assert
        assert result == expected_value

    @pytest.mark.fast
    def test_<feature>_with_invalid_input_raises_error(self, instance):
        """ReqID: FR-02 - Feature raises error for invalid input."""
        # Arrange
        invalid_input = None

        # Act & Assert
        with pytest.raises(ValueError):
            instance.method(invalid_input)
```

### 6. Implement the Feature

**Using Cursor IDE:**
```bash
# In Cursor chat, use EDRR workflow:
/expand-phase implement <feature_name> feature
/differentiate-phase <feature_name> implementation approaches
/refine-phase implement selected <feature_name> approach

# Or use TestArchitect mode (Cmd+Shift+T) for comprehensive implementation
```

**Manual Implementation:**
Location: `src/devsynth/<module>/<feature_name>.py`

```python
"""<Feature Name> implementation.

This module implements <brief description>.

Example:
    >>> from devsynth.<module> import <Class>
    >>> instance = <Class>()
    >>> result = instance.method("input")
"""
from typing import Optional, List
from devsynth.logging_setup import get_logger
from devsynth.exceptions import DevSynthError

logger = get_logger(__name__)


class <FeatureName>Error(DevSynthError):
    """Raised when <feature> operations fail."""
    pass


class <Class>:
    """<Brief class description>.

    Implements <feature> functionality following <relevant policy>.

    Attributes:
        config: Configuration dictionary

    Example:
        >>> instance = <Class>(config={"key": "value"})
        >>> result = instance.method("input")
    """

    def __init__(self, config: Optional[dict] = None) -> None:
        """Initialize <Class>.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        logger.info(f"Initialized <Class> with config: {self.config}")

    def method(self, input_data: str) -> str:
        """Perform primary operation.

        Args:
            input_data: Input to process

        Returns:
            Processed result

        Raises:
            <FeatureName>Error: If operation fails
            ValueError: If input invalid
        """
        if not input_data:
            raise ValueError("Input cannot be empty")

        try:
            result = self._process(input_data)
            logger.debug(f"Processed {input_data} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to process {input_data}: {e}")
            raise <FeatureName>Error(f"Processing failed: {e}") from e

    def _process(self, data: str) -> str:
        """Internal processing logic."""
        # Implementation
        return data
```

### 7. Run All Tests

**Using Cursor IDE:**
```bash
# Generate comprehensive tests automatically:
/generate-test-suite <feature_name> component

# This will create:
# - Unit tests in tests/unit/<module>/test_<feature_name>.py
# - Integration tests in tests/integration/<module>/test_<feature_name>_integration.py
# - Additional BDD scenarios in tests/behavior/features/<feature_name>.feature
```

**Manual Testing:**
```bash
# Run fast tests
poetry run devsynth run-tests --speed=fast

# Run BDD feature
poetry run pytest tests/behavior/features/<feature_name>.feature -v

# Run unit tests
poetry run pytest tests/unit/<module>/test_<feature_name>.py -v

# Run integration tests
poetry run pytest tests/integration/ -k "<feature_name>" -v
```

**Testing in Cursor Terminal:**
```bash
# Verify environment in Cursor terminal
poetry run python --version  # Should show 3.12.x from .venv

# Run tests with proper environment
poetry run devsynth run-tests --speed=fast --no-parallel

# Check coverage
poetry run devsynth run-tests --report
```

**Expected**: All tests should now pass

### 8. Update Documentation

#### Update API Reference (if applicable)
Add docstrings that will be automatically included in generated API docs.

#### Update User Guide (if user-facing)
Location: `docs/user_guides/<relevant_guide>.md`

Add usage examples and explanations.

#### Update Architecture Docs (if significant)
Location: `docs/architecture/<relevant_doc>.md`

Document architectural decisions and component interactions.

### 9. Run Quality Checks

**Using Cursor IDE:**
```bash
# Comprehensive code review
/code-review <feature_name> implementation

# This will analyze:
# - Code quality and architecture compliance
# - Security vulnerabilities and performance issues
# - Testing coverage and documentation completeness
# - Improvement suggestions and best practice recommendations
```

**Manual Quality Checks:**
```bash
# Format code
poetry run black .
poetry run isort .

# Lint
poetry run flake8 src/ tests/

# Type check
poetry run mypy src tests

# Verify test markers
poetry run python scripts/verify_test_markers.py --changed

# Verify traceability
poetry run python scripts/verify_requirements_traceability.py

# Run dialectical audit
poetry run python scripts/dialectical_audit.py

# Security scanning
poetry run bandit -r src/
poetry run safety check
```

**Quality Validation in Cursor:**
```bash
# Validate BDD scenarios
/validate-bdd-scenarios <feature_name>.feature

# Check for missing speed markers
/add-speed-markers tests/

# Update specifications if needed
/update-specifications <feature_name> implementation details
```

**Resolve any issues before proceeding.**

### 10. Update Specification Status

Update `docs/specifications/<feature_name>.md`:

```markdown
---
status: "implemented"
implementation_date: "YYYY-MM-DD"
---
```

### 11. Create Commit

```bash
git add .

git commit -m "feat(<scope>): add <feature name>

Implements <brief description> as specified in
docs/specifications/<feature_name>.md.

Key changes:
- Added <Class> in src/devsynth/<module>
- Created BDD feature with X scenarios
- Added unit tests with Y% coverage
- Updated documentation

Dialectical notes:
- Thesis: Considered approach X for simplicity
- Antithesis: Approach Y offers better scalability
- Synthesis: Implemented X with Y's extension points

ReqID: FR-01, FR-02, NFR-01
Closes #<issue_number>
"
```

### 12. Run Pre-Commit Hooks

```bash
poetry run pre-commit run --files <changed_files>
```

### 13. Push and Create PR

```bash
# Push to feature branch
git push origin feature/<feature_name>

# Create PR via GitHub UI or CLI
```

Use PR template:
- Summary of changes
- Link to specification
- Test evidence
- Dialectical analysis
- Checklist completion

## Verification Checklist

Before considering feature complete:

- [ ] Specification created in `docs/specifications/`
- [ ] Socratic checklist answered
- [ ] Dialectical analysis included
- [ ] BDD feature file created
- [ ] Step definitions implemented
- [ ] Feature verified to fail initially
- [ ] Unit tests created
- [ ] Unit tests include speed markers
- [ ] Unit tests include ReqID references
- [ ] Feature implemented
- [ ] All tests pass
- [ ] Code formatted (Black, isort)
- [ ] No lint errors (flake8)
- [ ] Type hints added (mypy passes)
- [ ] Docstrings complete (Google style)
- [ ] Documentation updated
- [ ] Traceability verified
- [ ] Dialectical audit resolved
- [ ] Conventional commit message
- [ ] Pre-commit hooks pass
- [ ] PR created and linked to issue

## Common Pitfalls

❌ **Don't start coding without specification**
✅ Always create spec first

❌ **Don't skip the failing test step**
✅ Verify test fails before implementing

❌ **Don't forget speed markers**
✅ Every test needs exactly one: fast/medium/slow

❌ **Don't leave dialectical_audit.log unresolved**
✅ Run audit and resolve before committing

❌ **Don't use vague commit messages**
✅ Use Conventional Commits format

## Practical Cursor IDE Examples

### Example 1: Adding a CLI Command

**Complete workflow using Cursor IDE:**

```bash
# 1. Specification (Cursor chat)
/generate-specification add offline mode to CLI

# 2. Implementation (Cursor EDRR workflow)
/expand-phase implement CLI offline mode
/differentiate-phase CLI offline implementation approaches
/refine-phase implement offline mode with transformers fallback

# 3. Testing (Cursor commands)
/generate-test-suite CLI offline functionality

# 4. Integration (Terminal)
/validate-bdd-scenarios cli_offline_mode.feature
poetry run devsynth --help  # Verify new command appears
```

**Expected Results:**
- ✅ Specification created in `docs/specifications/cli_offline_mode.md`
- ✅ BDD scenarios in `tests/behavior/features/cli_offline_mode.feature`
- ✅ Implementation in `src/devsynth/application/cli/commands/`
- ✅ Unit tests with speed markers in `tests/unit/application/cli/`
- ✅ Integration tests in `tests/integration/cli/`
- ✅ Command appears in `devsynth --help` output

### Example 2: Implementing a New Agent

**Complete workflow using Cursor IDE:**

```bash
# 1. Specification (Cursor chat)
/generate-specification conversation agent with memory

# 2. Architecture (Cursor EDRR)
/expand-phase implement agent with memory integration
/differentiate-phase agent architecture patterns
/refine-phase implement conversation agent using langgraph

# 3. Testing (Cursor commands)
/generate-test-suite conversation agent

# 4. Integration (Terminal)
poetry run pytest tests/unit/application/agents/test_conversation_agent.py -v
poetry run pytest tests/behavior/features/conversation_agent.feature -v
```

**Expected Results:**
- ✅ Agent implementation in `src/devsynth/application/agents/`
- ✅ Memory integration with proper error handling
- ✅ Configuration management for agent settings
- ✅ Comprehensive test coverage with mocks for external dependencies
- ✅ Documentation with usage examples and API reference

### Example 3: Database Integration

**Complete workflow using Cursor IDE:**

```bash
# 1. Specification (Cursor chat)
/generate-specification database integration for user preferences

# 2. Schema Design (Cursor EDRR)
/expand-phase database schema options for preferences
/differentiate-phase database backend comparison
/refine-phase implement TinyDB integration for preferences

# 3. Testing (Cursor commands)
/generate-test-suite database integration tests

# 4. Integration (Terminal)
export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
poetry run pytest tests/integration/application/memory/ -k "preferences" -v
```

**Expected Results:**
- ✅ Database adapter in `src/devsynth/adapters/`
- ✅ Schema definition with proper data types
- ✅ CRUD operations with error handling
- ✅ Resource gating with environment variables
- ✅ Integration tests with proper setup/teardown

## Cursor IDE Best Practices for Feature Development

### 1. Start with Clear Intent
```bash
# Always begin with specification generation
/generate-specification [clear feature description]

# Review generated specification before proceeding
# Edit specification manually if needed for clarity
```

### 2. Use EDRR Process Systematically
```bash
# Don't skip phases - each provides value:
/expand-phase [task]     # Multiple approaches
/differentiate-phase [options]  # Structured comparison
/refine-phase [selection]       # Implementation
/retrospect-phase [analysis]    # Learning capture
```

### 3. Leverage Test Generation
```bash
# Generate comprehensive tests automatically
/generate-test-suite [component]

# This creates tests faster and more comprehensively than manual creation
# Always review and adjust generated tests for your specific needs
```

### 4. Use Appropriate Modes
```bash
# EDRRImplementer Mode (Cmd+Shift+E) - For implementation tasks
# SpecArchitect Mode (Cmd+Shift+S) - For specification and BDD work
# TestArchitect Mode (Cmd+Shift+T) - For testing and quality work
# CodeReviewer Mode (Cmd+Shift+R) - For review and analysis
# DialecticalThinker Mode (Cmd+Shift+D) - For complex decisions
```

### 5. Environment Management
```bash
# Always verify environment in Cursor terminal
poetry run python --version  # Should show .venv Python
poetry run which python      # Should show .venv path

# Set required environment variables
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
```

### 6. Quality Integration
```bash
# Use code review for comprehensive analysis
/code-review [recent changes]

# Validate BDD scenarios
/validate-bdd-scenarios [feature file]

# Check test markers
/add-speed-markers [test directory]
```

## Example Complete Feature

See completed examples in:
- `examples/full_workflow/` - Complete feature workflow demonstration
- `tests/behavior/features/memory_crud.feature` - CRUD feature with comprehensive BDD
- `docs/specifications/memory_crud.md` - Corresponding specification with dialectical analysis
- `src/devsynth/application/memory/` - Implementation with proper architecture
- `tests/unit/application/memory/` - Unit tests with speed markers and coverage
