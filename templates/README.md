# Test Templates for DevSynth

This directory contains templates for different types of tests in the DevSynth project. These templates provide a standardized structure for writing tests and help ensure consistency across the codebase.

## Directory Structure

- `unit/`: Templates for unit tests
- `integration/`: Templates for integration tests
- `behavior/`: Templates for behavior tests (BDD)

## Templates

### Unit Test Template

The `unit/test_template.py` file provides a template for writing unit tests. Unit tests verify that individual components (classes, functions) work correctly in isolation.

Usage:
1. Copy the template to the appropriate location in the `tests/unit/` directory
2. Rename the file to `test_<module_name>.py`
3. Replace the placeholder content with your actual tests
4. Follow the Arrange-Act-Assert pattern for each test
5. Include both positive and negative test cases
6. Ensure tests are hermetic and deterministic

Example:
```bash
cp templates/unit/test_template.py tests/unit/test_my_module.py
# Edit tests/unit/test_my_module.py
pytest tests/unit/test_my_module.py
```

### Integration Test Template

The `integration/test_integration_template.py` file provides a template for writing integration tests. Integration tests verify that different components of the system work together correctly.

Usage:
1. Copy the template to the appropriate location in the `tests/integration/` directory
2. Rename the file to `test_<feature_name>_integration.py`
3. Replace the placeholder content with your actual tests
4. Follow the Arrange-Act-Assert pattern for each test
5. Include both positive and negative test cases
6. Ensure tests are hermetic and deterministic

Example:
```bash
cp templates/integration/test_integration_template.py tests/integration/test_my_integration.py
# Edit tests/integration/test_my_integration.py
pytest tests/integration/test_my_integration.py
```

### BDD Feature Template

The `behavior/feature_template.feature` file provides a template for writing BDD feature files using Gherkin syntax. Feature files describe the behavior of the system from a user perspective.

Usage:
1. Copy the template to the appropriate location in the `tests/behavior/features/` directory
2. Rename the file to `<feature_name>.feature`
3. Replace the placeholder content with your actual feature description and scenarios
4. Ensure the scenarios cover all important aspects of the feature
5. Use scenario outlines for parameterized tests

Example:
```bash
cp templates/behavior/feature_template.feature tests/behavior/features/my_feature.feature
# Edit tests/behavior/features/my_feature.feature
```

### BDD Step Definitions Template

The `behavior/test_steps_template.py` file provides a template for implementing step definitions for BDD tests. Step definitions map the steps in feature files to executable code.

Usage:
1. Copy the template to the appropriate location in the `tests/behavior/steps/` directory
2. Rename the file to `test_<feature_name>_steps.py`
3. Replace the placeholder content with your actual step definitions
4. Update the `scenarios()` function call to point to your feature file
5. Ensure all steps in the corresponding feature file are implemented

Example:
```bash
cp templates/behavior/test_steps_template.py tests/behavior/steps/test_my_feature_steps.py
# Edit tests/behavior/steps/test_my_feature_steps.py
# Update the scenarios() function call to point to 'my_feature.feature'
pytest tests/behavior/steps/test_my_feature_steps.py
```

### Sample Tests

The templates directory also includes runnable example tests that `devsynth init`
can copy into a new project:

- `unit/sample_test.py` – basic unit test exercising a simple `add` function
- `integration/sample_integration_test.py` – demonstrates a small workflow
- `behavior/sample.feature` and `behavior/sample_steps.py` – BDD example for
  adding two numbers

These files provide ready-to-run tests that verify the development environment
after initialization.

## Best Practices

When writing tests, follow these best practices:

1. **Test-First Development**: Write tests before implementing functionality (TDD)
2. **Behavior-Driven Development**: Define behavior from a user perspective (BDD)
3. **Hermetic Testing**: Ensure tests are isolated from each other and from the external environment
4. **Comprehensive Coverage**: Test both happy paths and error cases
5. **Clear Assertions**: Make assertions clear and specific
6. **Descriptive Names**: Use descriptive names for test functions and variables
7. **Arrange-Act-Assert**: Follow the Arrange-Act-Assert pattern for clear test structure
8. **Dialectical Reasoning**: Consider multiple perspectives in test design

For more details, see the [TDD/BDD Approach Documentation](../docs/developer_guides/tdd_bdd_approach.md).
