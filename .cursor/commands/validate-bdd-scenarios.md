# Validate BDD Scenarios Command

Validate and improve BDD scenarios for: {{feature_or_file}}

## Instructions

1. **Validate Syntax**: Check Gherkin syntax and structure compliance
2. **Test Completeness**: Verify scenarios cover all acceptance criteria
3. **Style Compliance**: Ensure adherence to BDD best practices and project standards
4. **Implementation Alignment**: Check that scenarios can be implemented with current architecture
5. **Suggest Improvements**: Propose enhancements for clarity, completeness, and testability

## Validation Criteria

### Syntax Validation
- **Gherkin Structure**: Proper Feature/Scenario/Step structure
- **Keywords**: Correct use of Given/When/Then/And/But keywords
- **Indentation**: Consistent indentation and formatting
- **Tags**: Appropriate use of tags for categorization and filtering

### Content Validation
- **Clarity**: Scenarios are clear and unambiguous
- **Completeness**: All acceptance criteria are covered
- **Atomicity**: Each scenario tests a single behavior
- **Measurability**: All outcomes are objectively verifiable

### Style Guidelines
- **Declarative Style**: Describe what users want to achieve, not how
- **Business Language**: Use business-friendly terminology
- **Consistent Voice**: Maintain consistent perspective and tone
- **Appropriate Detail**: Include enough detail for implementation but avoid UI specifics

## Implementation Feasibility

### Technical Validation
- **Architecture Compatibility**: Scenarios align with system architecture
- **Data Availability**: Required test data can be created or mocked
- **System Access**: Scenarios can access necessary system components
- **Error Conditions**: Error scenarios are realistic and testable

### Testing Framework Compatibility
- **Step Definitions**: Scenarios can be implemented with existing step definitions
- **Test Data**: Required test data formats are supported
- **Assertions**: Expected outcomes can be verified programmatically
- **Setup/Teardown**: Proper setup and cleanup procedures exist

## Output Format

### Validation Results

#### Syntax Validation
- **Valid**: [Yes/No]
- **Issues Found**:
  - [Issue 1]: [Description and location]
  - [Issue 2]: [Description and location]
- **Suggestions**:
  - [Suggestion 1]: [Improvement recommendation]

#### Content Validation
- **Clarity Score**: [1-10 rating and explanation]
- **Completeness Score**: [1-10 rating and explanation]
- **Testability Score**: [1-10 rating and explanation]

#### Style Compliance
- **Declarative Style**: [Yes/No/Partial]
- **Business Language**: [Yes/No/Partial]
- **Consistency**: [Yes/No/Partial]
- **Detail Level**: [Appropriate/Too detailed/Insufficient]

### Implementation Analysis

#### Technical Feasibility
- **Architecture Alignment**: [Compatible/Requires changes/Explanation]
- **Data Requirements**: [Can be satisfied/Cannot be satisfied/Explanation]
- **System Integration**: [Feasible/Not feasible/Explanation]

#### Testing Framework Compatibility
- **Step Implementation**: [Can implement/Cannot implement/Explanation]
- **Test Data Support**: [Supported/Not supported/Explanation]
- **Assertion Capability**: [Can verify/Cannot verify/Explanation]

### Improvement Recommendations

#### Critical Issues (Must Fix)
1. **Issue 1**: [Description and recommended fix]
2. **Issue 2**: [Description and recommended fix]

#### Enhancement Opportunities (Should Consider)
1. **Enhancement 1**: [Description and potential benefit]
2. **Enhancement 2**: [Description and potential benefit]

#### Best Practice Suggestions (Optional)
1. **Practice 1**: [Description and implementation suggestion]
2. **Practice 2**: [Description and implementation suggestion]

## Enhanced Scenarios

### Improved Feature File
Provide an improved version of the feature file:

```gherkin
[Enhanced Gherkin content with improvements applied]
```

### Implementation Notes
- **Step Definitions Needed**: [List of step definitions to implement]
- **Test Data Requirements**: [Test data setup requirements]
- **Mocking Strategy**: [Approach for mocking dependencies]
- **Setup/Teardown**: [Setup and cleanup procedures]

## Quality Metrics

### Scenario Quality Score
**Overall Score**: [1-10 based on all validation criteria]

**Breakdown**:
- **Syntax**: [Score/10]
- **Content**: [Score/10]
- **Style**: [Score/10]
- **Technical**: [Score/10]
- **Testability**: [Score/10]

### Coverage Analysis
- **Requirements Coverage**: [Percentage of requirements covered by scenarios]
- **Acceptance Criteria**: [Percentage of acceptance criteria covered]
- **Edge Cases**: [Coverage of edge cases and error conditions]
- **User Journeys**: [Coverage of different user paths]

This validation ensures that BDD scenarios are clear, complete, testable, and aligned with both business requirements and technical implementation capabilities.
