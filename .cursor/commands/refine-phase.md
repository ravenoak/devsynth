# Refine Phase Command

Implement and optimize the selected approach for: {{user_request}}

## Instructions

1. **Implement Selected Approach**: Build the solution based on the differentiate phase recommendation
2. **Follow Best Practices**: Apply coding standards, security practices, and architectural patterns
3. **Comprehensive Testing**: Implement unit tests, integration tests, and BDD scenarios
4. **Performance Optimization**: Optimize for performance, scalability, and resource usage
5. **Quality Assurance**: Ensure code quality, documentation, and compliance with standards

## Implementation Guidelines

### Reference Implementation Patterns
- **Architecture**: Follow hexagonal architecture patterns in `src/devsynth/`
- **Specifications**: Implement according to specifications in `docs/specifications/`
- **Testing**: Create comprehensive tests following patterns in `tests/`
- **Examples**: Use similar implementations from `examples/` as reference

### Code Quality Standards
- **Type Safety**: Use comprehensive type annotations and mypy strict checking
- **Documentation**: Add docstrings for all public APIs with examples
- **Error Handling**: Implement comprehensive error handling and logging
- **Security**: Apply security best practices and input validation

## Development Workflow

### 1. Implementation Structure
Create the implementation following established patterns:

```python
# Example implementation structure
class FeatureImplementation:
    """Implementation of the selected feature approach."""

    def __init__(self, dependencies):
        """Initialize with required dependencies."""
        self.dependencies = dependencies

    def main_functionality(self, input_data):
        """Implement core functionality with proper validation."""
        # Input validation
        # Core logic implementation
        # Error handling
        # Return results
        pass

    def helper_methods(self):
        """Supporting methods with clear separation of concerns."""
        pass
```

### 2. Testing Implementation
Implement comprehensive testing:

```python
# Unit tests
@pytest.mark.fast
def test_core_functionality():
    """Test core functionality in isolation."""
    implementation = FeatureImplementation(mock_dependencies)
    result = implementation.main_functionality(valid_input)
    assert result == expected_output

# Integration tests
@pytest.mark.medium
def test_system_integration():
    """Test integration with other system components."""
    # Test component interactions
    # Verify data flow
    # Check error propagation

# BDD tests
@scenario('feature_name.feature', 'scenario_name')
def test_user_behavior():
    """Test behavior from user perspective."""
    # Given preconditions
    # When user action
    # Then expected outcome
```

### 3. Documentation Updates
Update relevant documentation:

```markdown
# Specification updates
- Update implementation status
- Document architectural decisions
- Add usage examples
- Update API documentation

# Code documentation
- Add comprehensive docstrings
- Include usage examples
- Document error conditions
- Explain complex logic
```

## Output Format

### Implementation Summary
**Feature**: [Feature name and description]
**Approach**: [Selected implementation approach]
**Status**: [Implementation status]

### Code Structure
```
[File structure showing new/modified files]
├── src/devsynth/[module]/[feature].py
├── tests/unit/[module]/test_[feature].py
├── tests/integration/[module]/test_[feature]_integration.py
├── tests/behavior/features/[feature].feature
└── docs/specifications/[feature]_implementation.md
```

### Key Components Implemented
1. **Core Logic**: [Description of main implementation]
2. **Data Models**: [Description of data structures]
3. **API Interfaces**: [Description of public APIs]
4. **Error Handling**: [Description of error management]
5. **Validation**: [Description of input/output validation]

### Testing Coverage
- **Unit Tests**: [Number] tests covering core functionality
- **Integration Tests**: [Number] tests covering component interactions
- **BDD Scenarios**: [Number] scenarios covering user behaviors
- **Coverage**: [Percentage] code coverage achieved

### Performance Characteristics
- **Response Time**: [Expected/achieved response times]
- **Memory Usage**: [Memory consumption analysis]
- **Scalability**: [Scalability considerations and limits]
- **Resource Requirements**: [Hardware/resource requirements]

## Quality Validation

### Code Quality Metrics
- **Linting**: Passes all linting rules (flake8, black)
- **Type Checking**: Passes mypy strict checking
- **Test Coverage**: Meets minimum coverage requirements
- **Security Scan**: Passes security validation

### Specification Compliance
- **Requirements**: All functional requirements implemented
- **Non-functional**: All performance, security, and quality requirements met
- **BDD Scenarios**: All acceptance criteria passing
- **Documentation**: Specifications updated and accurate

## Next Steps

### Immediate Actions
1. **Code Review**: Submit implementation for review
2. **Testing**: Run full test suite and validate coverage
3. **Integration**: Test integration with existing system
4. **Documentation**: Update user and developer documentation

### Future Enhancements
1. **Performance Tuning**: Optimize based on usage patterns
2. **Feature Extension**: Add additional capabilities as needed
3. **Monitoring**: Implement monitoring and alerting
4. **Maintenance**: Schedule regular maintenance and updates

This refine phase delivers a production-ready implementation that meets all requirements, follows best practices, and maintains high quality standards.
