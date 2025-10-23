# Code Review Command

Perform comprehensive code review for: {{code_changes_or_files}}

## Instructions

1. **Analyze Changes**: Review code changes against project standards and best practices
2. **Quality Assessment**: Evaluate code quality, security, performance, and maintainability
3. **Compliance Check**: Verify compliance with project constitution and architectural patterns
4. **Testing Review**: Assess testing coverage and quality
5. **Recommendations**: Provide actionable improvement suggestions

## Review Framework

### 1. Code Quality Analysis
**Readability**:
- Clear variable and function names
- Consistent code formatting and style
- Appropriate comments and documentation
- Logical code organization and structure

**Maintainability**:
- Separation of concerns
- Appropriate abstraction levels
- Consistent patterns and conventions
- Future-proof design decisions

**Complexity**:
- Cyclomatic complexity analysis
- Function length and responsibility
- Class design and inheritance
- Algorithm efficiency

### 2. Architecture Compliance
**Design Patterns**:
- Alignment with hexagonal architecture
- Proper use of ports and adapters
- Dependency injection implementation
- Interface segregation

**Component Structure**:
- Clear module boundaries
- Appropriate coupling and cohesion
- Interface contracts adherence
- Integration point management

### 3. Security Assessment
**Input Validation**:
- All inputs properly validated and sanitized
- SQL injection prevention
- XSS protection measures
- Authentication and authorization checks

**Data Protection**:
- Sensitive data encryption
- Access control implementation
- Audit trail maintenance
- Compliance with security policies

### 4. Performance Analysis
**Algorithm Efficiency**:
- Appropriate data structures and algorithms
- Database query optimization
- Caching strategy implementation
- Resource usage optimization

**Scalability Considerations**:
- Stateless design where appropriate
- Horizontal scaling support
- Connection pooling usage
- Resource limit management

### 5. Testing Coverage
**Test Completeness**:
- Unit test coverage for new code
- Integration test coverage for interactions
- BDD scenario coverage for behaviors
- Edge case and error condition testing

**Test Quality**:
- Appropriate speed markers
- Clear test organization
- Proper mocking strategies
- Deterministic test behavior

## Review Criteria

### Critical Issues (Must Fix)
- **Security Vulnerabilities**: Any security risks or vulnerabilities
- **Breaking Changes**: Changes that break existing functionality
- **Performance Issues**: Significant performance degradation
- **Compliance Violations**: Violations of project standards or policies

### Major Issues (Should Fix)
- **Code Quality**: Significant code quality issues
- **Architecture**: Architectural pattern violations
- **Testing**: Inadequate test coverage or quality
- **Documentation**: Missing or inadequate documentation

### Minor Issues (Consider Fixing)
- **Style**: Code style inconsistencies
- **Optimization**: Performance optimization opportunities
- **Best Practices**: Deviations from best practices
- **Readability**: Readability improvements

### Positive Aspects
- **Well Implemented**: Areas that are well implemented
- **Best Practices**: Good application of best practices
- **Innovation**: Innovative or creative solutions
- **Quality**: High-quality implementations

## Output Format

### Review Summary

#### Code Changes Reviewed
**Files Modified**: [List of files reviewed]
**Lines Changed**: [Total lines added/modified/deleted]
**Review Type**: [Full review / Incremental review / Security review]

#### Overall Assessment
**Quality Score**: [1-10 rating]
**Security Score**: [1-10 rating]
**Architecture Score**: [1-10 rating]
**Testing Score**: [1-10 rating]

### Detailed Findings

#### Critical Issues
1. **Issue 1**: [Description, location, and recommended fix]
   - **Severity**: Critical
   - **Impact**: [Description of impact]
   - **Fix Required**: [Specific fix recommendation]

2. **Issue 2**: [Description, location, and recommended fix]
   - **Severity**: Critical
   - **Impact**: [Description of impact]
   - **Fix Required**: [Specific fix recommendation]

#### Major Issues
1. **Issue 1**: [Description, location, and recommended fix]
   - **Severity**: Major
   - **Impact**: [Description of impact]
   - **Fix Required**: [Specific fix recommendation]

2. **Issue 2**: [Description, location, and recommended fix]
   - **Severity**: Major
   - **Impact**: [Description of impact]
   - **Fix Required**: [Specific fix recommendation]

#### Minor Issues
1. **Issue 1**: [Description, location, and suggested improvement]
   - **Severity**: Minor
   - **Impact**: [Description of impact]
   - **Suggestion**: [Improvement suggestion]

2. **Issue 2**: [Description, location, and suggested improvement]
   - **Severity**: Minor
   - **Impact**: [Description of impact]
   - **Suggestion**: [Improvement suggestion]

### Positive Findings

#### Well Implemented Areas
1. **Strength 1**: [Description of well-implemented area]
2. **Strength 2**: [Description of well-implemented area]

#### Best Practices Applied
1. **Practice 1**: [Description of good practice application]
2. **Practice 2**: [Description of good practice application]

## Recommendations

### Immediate Actions Required
1. **Security Fixes**: [Critical security issues to address immediately]
2. **Breaking Changes**: [Fixes for breaking changes]
3. **Compliance**: [Compliance violations to resolve]

### Quality Improvements
1. **Code Quality**: [Code quality enhancements]
2. **Testing**: [Testing improvements needed]
3. **Documentation**: [Documentation enhancements]

### Architectural Improvements
1. **Design**: [Design improvements suggested]
2. **Patterns**: [Pattern adherence improvements]
3. **Integration**: [Integration improvements]

## Approval Status

### Ready for Merge
- [ ] All critical issues resolved
- [ ] All major issues addressed or acknowledged
- [ ] Testing coverage adequate
- [ ] Documentation updated

### Requires Changes
- [ ] Critical issues need immediate attention
- [ ] Major issues require resolution
- [ ] Testing needs enhancement
- [ ] Documentation needs updates

This comprehensive code review ensures that all changes meet project standards, maintain quality, and contribute positively to the codebase.
