# Generate Test Suite Command

Generate comprehensive tests for: {{feature_or_component}}

## Instructions

1. **Analyze Requirements**: Review specifications and BDD scenarios for testing requirements
2. **Create Test Structure**: Generate unit tests, integration tests, and BDD scenarios
3. **Follow Testing Standards**: Ensure all tests follow project testing philosophy and speed markers
4. **Mock Dependencies**: Create appropriate mocks for external dependencies
5. **Validate Coverage**: Ensure comprehensive coverage of functionality and edge cases

## Test Structure

### 1. Unit Tests (`tests/unit/`)
Test individual components in isolation:

```python
# Example unit test structure
@pytest.mark.fast
class TestComponentName:
    """Unit tests for ComponentName functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.component = ComponentName(mock_dependencies)

    def test_happy_path(self):
        """Test normal operation."""
        result = self.component.main_function(valid_input)
        assert result == expected_output

    def test_edge_case(self):
        """Test edge case behavior."""
        result = self.component.main_function(edge_input)
        assert result == expected_edge_output

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ExpectedError):
            self.component.main_function(invalid_input)
```

### 2. Integration Tests (`tests/integration/`)
Test component interactions:

```python
# Example integration test structure
@pytest.mark.medium
class TestComponentIntegration:
    """Integration tests for component interactions."""

    def setup_method(self):
        """Set up integration test environment."""
        self.system = TestSystem()
        self.client = TestClient()

    def test_end_to_end_flow(self):
        """Test complete user journey."""
        # Setup
        # Execute
        # Verify
        pass

    def test_data_flow(self):
        """Test data flow between components."""
        # Test data transformation
        # Test persistence
        # Test retrieval
        pass
```

### 3. BDD Scenarios (`tests/behavior/features/`)
Test behavior from user perspective:

```gherkin
Feature: ComponentName Functionality
    As a user of the system
    I want to use ComponentName
    So that I can achieve my goal

    Background:
        Given the system is properly configured
        And I have necessary permissions

    @happy_path @smoke_test
    Scenario: Successful operation
        Given I provide valid input
        When I perform the operation
        Then I should receive the expected result
        And the system should remain stable

    @error_handling @security
    Scenario: Invalid input handling
        Given I provide invalid input
        When I attempt the operation
        Then I should receive an appropriate error message
        And no data should be corrupted

    @performance @load_test
    Scenario: High load performance
        Given the system is under normal load
        When I perform multiple operations
        Then response times should remain acceptable
        And no errors should occur
```

## Testing Standards

### Speed Markers (Required)
- **@pytest.mark.fast**: Tests completing in <1 second
- **@pytest.mark.medium**: Tests completing in 1-10 seconds
- **@pytest.mark.slow**: Tests taking >10 seconds

### Test Organization
- **Fixtures**: Use pytest fixtures for setup/teardown
- **Mocks**: Mock external dependencies appropriately
- **Resource Gates**: Use environment variables for optional resources
- **Isolation**: Ensure tests are independent and repeatable

### Coverage Requirements
- **Function Coverage**: All public functions must have tests
- **Branch Coverage**: All conditional branches must be tested
- **Line Coverage**: Achieve minimum 90% coverage
- **Edge Cases**: Cover boundary conditions and error cases

## Implementation Guidelines

### Reference Existing Patterns
- **Similar Tests**: Look for similar functionality in existing tests
- **Testing Patterns**: Follow established testing patterns in the codebase
- **Mock Strategies**: Use existing mocking approaches for dependencies
- **Test Data**: Follow existing test data creation patterns

### Quality Assurance
- **Deterministic**: Tests should produce consistent results
- **Fast Feedback**: Prioritize fast tests for quick feedback
- **Clear Assertions**: Use descriptive assertions with clear failure messages
- **Documentation**: Document complex test logic and edge cases

## Output Format

### Generated Files

#### Unit Tests
**File**: `tests/unit/[module]/test_[component].py`
**Structure**:
- Test class with descriptive name
- Setup and teardown methods
- Happy path tests
- Edge case tests
- Error handling tests

#### Integration Tests
**File**: `tests/integration/[module]/test_[component]_integration.py`
**Structure**:
- System setup and teardown
- End-to-end flow tests
- Component interaction tests
- Data persistence tests

#### BDD Feature File
**File**: `tests/behavior/features/[component].feature`
**Structure**:
- Feature description with business value
- Background steps for common setup
- Multiple scenarios covering different behaviors
- Appropriate tags for categorization

#### Step Definitions
**File**: `tests/behavior/steps/test_[component]_steps.py`
**Structure**:
- Step definition functions for Given/When/Then
- Helper functions for test setup
- Assertions and validations
- Error handling and cleanup

### Test Coverage Analysis
**Unit Test Coverage**: [Number] tests covering core functionality
**Integration Coverage**: [Number] tests covering system interactions
**BDD Coverage**: [Number] scenarios covering user behaviors
**Overall Coverage**: [Percentage] code coverage achieved

### Mock and Fixture Setup
- **Dependencies Mocked**: [List of mocked dependencies]
- **Test Data Created**: [Test data generation approach]
- **Environment Setup**: [Environment configuration for tests]
- **Cleanup Procedures**: [Cleanup and teardown procedures]

## Quality Validation

### Test Quality Metrics
- **Speed Distribution**: Fast [X%], Medium [Y%], Slow [Z%]
- **Coverage Achievement**: [Coverage percentage and analysis]
- **Flakiness Risk**: [Assessment of test reliability]
- **Maintainability**: [Code quality of test implementations]

### Compliance Check
- **Standards Compliance**: All tests follow project testing standards
- **Speed Markers**: All tests have appropriate speed markers
- **Resource Gates**: Optional dependencies properly gated
- **Documentation**: Tests are well-documented and understandable

This comprehensive test suite ensures that the implementation is thoroughly validated and maintains high quality standards throughout the development lifecycle.
