---
description: Cursor IDE rules management, validation, and best practices
globs:
  - ".cursor/**/*"
  - "**/*.md"
alwaysApply: false
---

# Cursor IDE Rules Management

## Rules Philosophy

**Thesis**: Well-structured, validated rules ensure consistent AI assistance and maintain project standards across all development activities.

**Antithesis**: Poorly maintained rules can lead to inconsistent AI behavior, outdated guidance, and reduced development efficiency.

**Synthesis**: Systematic rules management with validation, modular design, and regular review ensures rules remain effective and aligned with project evolution.

## Rules Structure

### Core Architecture

```
.cursor/
├── rules/
│   ├── 00-project-core.md          # Always applied, foundational rules
│   ├── 01-testing-standards.md     # Test-specific guidance
│   ├── 02-bdd-workflow.md          # BDD and specification workflow
│   ├── 03-security-compliance.md   # Security and audit compliance
│   ├── 04-code-style.md            # Code style and formatting
│   ├── 05-documentation.md         # Documentation standards
│   ├── 06-commit-workflow.md       # Git and PR workflow
│   └── 07-cursor-rules-management.md # This file - rules management
├── validate-rules.py               # Rules validation script
└── README.md                       # Rules documentation
```

### Rule Metadata Format

**All rules must include front matter:**
```markdown
---
description: Clear, concise description of what this rule governs
globs:
  - "pattern1/**/*"
  - "pattern2/**/*.md"
alwaysApply: true|false  # Only 00-project-core.md should be true
---
```

## Rules Validation

### Automated Validation

**Run validation before committing rule changes:**
```bash
# Validate all rules
python .cursor/validate-rules.py

# Validate specific rule
python .cursor/validate-rules.py --rule 02-bdd-workflow.md

# Check rule application
python .cursor/validate-rules.py --check-application
```

### Validation Checks

**Structure Validation:**
- ✅ Valid YAML front matter
- ✅ Required fields present (`description`, `globs`)
- ✅ Glob patterns are valid
- ✅ No conflicting globs

**Content Validation:**
- ✅ No broken internal links
- ✅ Consistent formatting
- ✅ Proper code examples
- ✅ Up-to-date command examples

**Application Validation:**
- ✅ Rules activate for intended file patterns
- ✅ No rule conflicts
- ✅ Performance impact acceptable

## Rule Development Workflow

### Creating New Rules

1. **Identify Need**: What specific guidance is missing?
2. **Scope Definition**: Which files/patterns need this rule?
3. **Content Creation**: Write clear, actionable guidance
4. **Validation**: Test with validation script
5. **Integration**: Ensure no conflicts with existing rules

### Updating Existing Rules

1. **Assessment**: What needs to be updated?
2. **Impact Analysis**: How will changes affect existing workflows?
3. **Content Update**: Make targeted improvements
4. **Validation**: Ensure changes don't break existing functionality
5. **Testing**: Verify rule works in real scenarios

### Rule Best Practices

**Content Guidelines:**
- ✅ Keep each rule under 500 lines
- ✅ Single responsibility per rule
- ✅ Concrete examples over abstract guidance
- ✅ Include troubleshooting sections
- ✅ Reference related rules and documentation

**Technical Guidelines:**
- ✅ Use consistent markdown formatting
- ✅ Test all code examples
- ✅ Include validation commands
- ✅ Document dialectical reasoning where applicable

## Rule Maintenance Schedule

### Regular Reviews

**Monthly Review:**
- Check for outdated commands
- Verify all examples still work
- Update dependency versions
- Review for clarity improvements

**Quarterly Review:**
- Assess rule effectiveness
- Check for new project patterns needing rules
- Review rule conflicts and overlaps
- Update based on team feedback

**Version Alignment:**
- Rules version should match project version
- Update version field in rule front matter
- Coordinate with release planning

## Troubleshooting Rules Issues

### Common Problems

**Problem**: Rules not activating for expected files
**Solution**:
```bash
# 1. Check glob patterns
python .cursor/validate-rules.py --debug-globs

# 2. Verify file patterns match
find . -name "*.py" | head -5

# 3. Test rule application
echo "test content" > /tmp/test.md
# Check if rule activates in Cursor IDE
```

**Problem**: Rule conflicts or overlaps
**Solution**:
```bash
# 1. Analyze rule interactions
python .cursor/validate-rules.py --analyze-conflicts

# 2. Review overlapping globs
grep -r "globs:" .cursor/rules/

# 3. Refactor if needed
# Combine related rules or adjust patterns
```

**Problem**: Performance issues with rules
**Solution**:
```bash
# 1. Check rule loading time
python .cursor/validate-rules.py --performance

# 2. Optimize large rules
# Split into smaller, focused rules

# 3. Review alwaysApply rules
# Only 00-project-core.md should be alwaysApply: true
```

## Rule Templates

### New Rule Template

```markdown
---
description: Brief description of what this rule governs
globs:
  - "pattern/**/*"
alwaysApply: false
---

# Rule Title

## Overview

Clear explanation of the rule's purpose and scope.

## Specific Guidance

Detailed, actionable guidance with examples.

## Validation

Commands to verify the rule works correctly.

## Troubleshooting

Common issues and solutions.

## Related Rules

Links to related rules and documentation.
```

### Rule Update Checklist

- [ ] Update description if scope changed
- [ ] Review and update globs if needed
- [ ] Test all examples and commands
- [ ] Run validation script
- [ ] Check for conflicts with other rules
- [ ] Update related documentation
- [ ] Get team review if significant changes

## Integration with Development Workflow

### Pre-Commit Integration

Rules are validated as part of the pre-commit process:
```bash
# Manual validation (part of pre-commit)
python .cursor/validate-rules.py

# Check rule format and content
python .cursor/validate-rules.py --strict
```

### CI/CD Integration

Rules validation should be part of CI pipeline:
```yaml
# In .github/workflows/ci.yml
- name: Validate Cursor Rules
  run: python .cursor/validate-rules.py --ci
```

## Rule Metrics and Analytics

### Measuring Rule Effectiveness

**Usage Metrics:**
- Which rules activate most frequently?
- Which rules provide most value?
- Where are rules unclear or insufficient?

**Performance Metrics:**
- Rule loading time
- Memory usage impact
- Context switching overhead

### Feedback Collection

**From Developers:**
- Rule clarity and usefulness
- Missing guidance areas
- Confusing or incorrect examples

**From AI Usage:**
- Rule activation patterns
- Common rule conflicts
- Areas needing better guidance

## Advanced Rule Features

### Conditional Rules

For complex scenarios, consider conditional logic:
```markdown
<!-- Rule applies only when specific conditions met -->
**Condition**: When working with async code
**Guidance**: Use specific async patterns
```

### Cross-Referenced Rules

Link related rules for comprehensive guidance:
```markdown
See Also:
- [Testing Standards](01-testing-standards.md)
- [Security Compliance](03-security-compliance.md)
```

## Emergency Rule Management

### Rule Rollback

If problematic rules are deployed:
```bash
# 1. Identify problematic rule
python .cursor/validate-rules.py --analyze-issues

# 2. Temporarily disable rule
# Comment out in .cursor/rules/

# 3. Investigate and fix
# Update rule content

# 4. Re-enable and validate
python .cursor/validate-rules.py
```

### Rule Versioning

Track rule changes with project:
```bash
# View rule history
git log --oneline .cursor/rules/

# Compare rule versions
git diff HEAD~1 .cursor/rules/02-bdd-workflow.md
```

## Best Practices Summary

### Do:
- ✅ Write clear, actionable guidance
- ✅ Include concrete examples
- ✅ Test all commands and examples
- ✅ Run validation before committing
- ✅ Keep rules focused and under 500 lines
- ✅ Document dialectical reasoning for significant rules

### Don't:
- ❌ Write vague or abstract guidance
- ❌ Include untested examples
- ❌ Create overlapping rules
- ❌ Skip validation steps
- ❌ Make rules too long or complex
- ❌ Forget to update related documentation

## Support and Documentation

### Getting Help

For rule-related issues:
1. Check validation script output
2. Review rule documentation
3. Consult team members
4. Open issue with `area/cursor-rules` label

### Further Reading

- [Cursor IDE Rules Documentation](https://cursor.directory/rules)
- [Project Documentation](../docs/)
- [Contributing Guide](../CONTRIBUTING.md)
- [Development Guides](../docs/developer_guides/)
