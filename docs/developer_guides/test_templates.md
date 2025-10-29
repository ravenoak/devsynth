---

author: DevSynth Team
date: '2025-05-25'
last_reviewed: "2025-08-17"
status: published
tags:

- testing
- templates
- TDD
- BDD
- best-practices

title: Test Templates in DevSynth
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Test Templates in DevSynth
</div>

# Test Templates in DevSynth

## 1. Overview

This document explains the organization and usage of test templates in the DevSynth project. It covers the rationale behind the placement of templates, how to use them, and best practices for creating new tests.

## 2. Template Location

Test templates are located in the `tests/templates/` directory. This location was chosen after careful consideration and dialectical reasoning, weighing the pros and cons of different approaches.

### 2.1 Rationale for Template Location

The decision to organize test templates within the `tests/templates/` directory was based on several factors:

**Thesis (Keep templates in tests/):**

- Templates are closely related to tests and should be kept near where they'll be used
- Developers will naturally look for test examples in the tests directory
- Proximity to actual tests makes templates more discoverable


**Antithesis (Move templates to a dedicated directory):**

- Templates are not tests themselves and don't belong in a test directory
- Test runners might try to run template files as actual tests
- A dedicated templates directory provides a clear separation of concerns
- The project already has a convention for templates in `tests/templates/`


**Synthesis (Final Decision):**

- Templates should be in a dedicated directory to clearly separate them from actual tests
- The location should follow existing project conventions for templates
- The templates should be well-documented and easily discoverable
- The `tests/templates/` directory provides the best balance of these considerations


This approach ensures that:

1. Test templates are not accidentally run as tests by test runners
2. Templates are organized according to project conventions
3. There is a clear separation between templates and actual tests
4. Templates are still easily discoverable through documentation


## 3. Template Organization

The test templates are organized into subdirectories based on the type of test:

- `unit/`: Templates for unit tests
- `integration/`: Templates for integration tests
- `behavior/`: Templates for behavior tests (BDD)


Each subdirectory contains templates specific to that type of test, and the root directory contains a README.md file with usage instructions.

## 4. Using Templates

To use a template, copy it to the appropriate location in the `tests/` directory and customize it for your specific needs. For example:

```bash

# Copy a unit test template

cp tests/templates/unit/unit_test_template.py tests/unit/test_my_module.py

# Copy an integration test template

cp tests/templates/integration/integration_test_template.py tests/integration/test_my_integration.py

# Copy a BDD feature template

cp tests/templates/behavior/feature_template.feature tests/behavior/features/my_feature.feature

# Copy a BDD step definitions template

cp tests/templates/behavior/step_definitions_template.py tests/behavior/steps/test_my_feature_steps.py
```

After copying a template, edit it to replace the placeholder content with your actual test code.

For integration tests the enhanced parser can build file paths dynamically:

```python
from scripts import enhanced_test_parser as etp

etp.build_test_path("integration", "workflow", component="general")
# -> "tests/integration/general/test_workflow.py"
```

## 5. Template Content

Each template includes:

1. A comprehensive docstring explaining how to use the template
2. Examples of different types of tests (success cases, error cases, etc.)
3. Placeholders for test code
4. Comments explaining the purpose of each section


Templates follow best practices like the Arrange-Act-Assert pattern and include examples of fixtures, parameterized tests, and other pytest features.

## 6. Creating New Templates

If you need to create a new template:

1. Identify the type of test (unit, integration, behavior)
2. Create a new file in the appropriate subdirectory of `tests/templates/`
3. Include a comprehensive docstring explaining how to use the template
4. Add examples of different test scenarios
5. Include placeholders for test code
6. Add comments explaining the purpose of each section
7. Update the README.md file to include the new template


## 7. Best Practices

When using templates to create tests, follow these best practices:

1. **Test-First Development**: Write tests before implementing functionality (TDD)
2. **Behavior-Driven Development**: Define behavior from a user perspective (BDD)
3. **Hermetic Testing**: Ensure tests are isolated from each other and from the external environment
4. **Comprehensive Coverage**: Test both happy paths and error cases
5. **Clear Assertions**: Make assertions clear and specific
6. **Descriptive Names**: Use descriptive names for test functions and variables
7. **Arrange-Act-Assert**: Follow the Arrange-Act-Assert pattern for clear test structure
8. **Dialectical Reasoning**: Consider multiple perspectives in test design


For more details on testing approaches, see the [TDD/BDD Approach Documentation](/docs/developer_guides/tdd_bdd_approach.md).

## 8. Review Process

Regular review keeps templates aligned with the project's evolving test
strategy and integration requirements:

1. Revisit each template at least once per quarter to confirm it reflects
   current integration scenarios.
2. Verify that examples run with the enhanced parser by constructing paths
   with `build_test_path`. Integration examples should include the
   appropriate `component` parameter to select the correct subdirectory.
3. Update metadata headers like `last_reviewed` whenever adjustments are made.

## 9. Conclusion

The organization of test templates in DevSynth follows best practices for separation of concerns while maintaining discoverability and usability. By placing templates in a dedicated directory, we ensure that they are not accidentally run as tests while still making them easily accessible to developers.

The test-first approach, combined with clear templates and guidelines, helps ensure consistent, high-quality tests throughout the project.
## Implementation Status

Integration templates support component-specific directories through the
`build_test_path` helper, enabling reviewers to generate accurate paths for
any subsystem.
