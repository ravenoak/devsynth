# Generate Specification Command

Create a comprehensive specification for: {{feature_description}}

## Instructions

1. **Follow SDD Process**: Create specification following Specify → Plan → Tasks → Implement workflow
2. **BDD Integration**: Include Gherkin scenarios for acceptance criteria
3. **Requirements Traceability**: Link to existing requirements and specifications
4. **Architecture Compliance**: Ensure alignment with project constitution and architecture
5. **Comprehensive Coverage**: Cover functional, non-functional, and quality requirements

## Specification Structure

### 1. Feature Overview
**Feature**: [Feature name]
**Description**: [Clear, concise description of the feature]
**Business Value**: [Why this feature is important]
**Stakeholders**: [Who benefits from this feature]

### 2. User Stories and Acceptance Criteria
**As a** [user role]
**I want** [goal/desired functionality]
**So that** [business value/benefit]

**Acceptance Criteria**:
- [Criterion 1]: [Measurable, testable requirement]
- [Criterion 2]: [Measurable, testable requirement]
- [Criterion 3]: [Measurable, testable requirement]

### 3. BDD Scenarios
Create executable Gherkin scenarios in `tests/behavior/features/`:

```gherkin
Feature: [Feature Name]
    As a [user role]
    I want [goal]
    So that [business value]

    Background:
        Given [shared preconditions]

    @happy_path @smoke_test
    Scenario: [Primary success scenario]
        Given [initial state]
        When [user action]
        Then [expected outcome]
        And [additional expectations]

    @edge_case @error_handling
    Scenario: [Error scenario]
        Given [initial state]
        When [error condition]
        Then [error handling]
        And [user feedback]

    @alternative_flow
    Scenario: [Alternative path scenario]
        Given [initial state]
        When [alternative action]
        Then [alternative outcome]
```

### 4. Technical Requirements
**Functional Requirements**:
- [Requirement 1]: [Detailed functional specification]
- [Requirement 2]: [Detailed functional specification]
- [Requirement 3]: [Detailed functional specification]

**Non-Functional Requirements**:
- **Performance**: [Response time, throughput, resource requirements]
- **Security**: [Security requirements and constraints]
- **Scalability**: [Scalability requirements and limits]
- **Reliability**: [Reliability and availability requirements]

### 5. API Specification (if applicable)
**Endpoints**:
- **GET /api/[resource]**: [Purpose and response format]
- **POST /api/[resource]**: [Purpose and request/response format]
- **PUT /api/[resource]**: [Purpose and request/response format]
- **DELETE /api/[resource]**: [Purpose and response format]

**Data Models**:
```python
class [ModelName](BaseModel):
    """[Model description]"""
    field1: [Type] = Field(..., description="[Description]")
    field2: [Type] = Field(..., description="[Description]")
```

### 6. Implementation Architecture
**Component Design**:
- [Component 1]: [Purpose and responsibilities]
- [Component 2]: [Purpose and responsibilities]
- [Component 3]: [Purpose and responsibilities]

**Integration Points**:
- [Integration 1]: [How it connects to existing systems]
- [Integration 2]: [How it connects to existing systems]

**Data Flow**:
1. [Step 1]: [Data flow description]
2. [Step 2]: [Data flow description]
3. [Step 3]: [Data flow description]

## Implementation Guidelines

### Reference Existing Patterns
- **Similar Features**: [Reference similar implementations in codebase]
- **Architecture Patterns**: [Reference established architectural patterns]
- **Testing Patterns**: [Reference testing approaches for similar features]
- **Documentation Patterns**: [Reference documentation formats]

### Quality Standards
- **Testing**: Ensure all acceptance criteria are covered by tests
- **Documentation**: Maintain comprehensive documentation
- **Security**: Follow security best practices and requirements
- **Performance**: Meet performance requirements and benchmarks

## Output Format

### Files to Create/Update

1. **Specification Document**: `docs/specifications/[feature_name].md`
2. **BDD Feature File**: `tests/behavior/features/[feature_name].feature`
3. **Implementation Plan**: `docs/specifications/[feature_name]_implementation.md`
4. **API Documentation**: Update OpenAPI specification if applicable

### Implementation Tasks
- [ ] Task 1: [Implementation task description]
- [ ] Task 2: [Implementation task description]
- [ ] Task 3: [Implementation task description]
- [ ] Task 4: [Implementation task description]

### Testing Strategy
- **Unit Tests**: [Unit testing approach]
- **Integration Tests**: [Integration testing approach]
- **BDD Tests**: [BDD testing approach]
- **Performance Tests**: [Performance testing approach]

### Success Criteria
- [ ] All BDD scenarios pass
- [ ] Code coverage meets requirements
- [ ] Performance benchmarks achieved
- [ ] Security requirements satisfied
- [ ] Documentation updated and complete

This specification serves as the single source of truth for the feature implementation and ensures all stakeholders understand the requirements and acceptance criteria.
